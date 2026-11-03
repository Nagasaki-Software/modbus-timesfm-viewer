from __future__ import annotations
import threading
import time
import logging
from dataclasses import dataclass
import numpy as np

log = logging.getLogger(__name__)


@dataclass
class PredictionResult:
    channel: int
    last_timestamp: float
    input_interval_sec: float   # TimesFM 入力周期＝予測点同士の時間間隔
    horizon_values: np.ndarray  # (H,)
    inference_time_sec: float


class TimesFM25Backend:
    """timesfm の TimesFM 2.5（PyTorch 版）を薄くラップ。

    モデル読込（初回はダウンロード）は時間がかかるため、コンストラクタでは行わず
    load() を予測スレッドから呼ぶ。
    """
    MAX_CONTEXT = 2048
    PATCH = 128  # 出力パッチ長。max_horizon はこの倍数に切り上げられる

    def __init__(self):
        self._model = None
        self._compiled_horizon = 0
        self._lock = threading.Lock()

    def load(self) -> None:
        with self._lock:
            if self._model is not None:
                return
            import timesfm
            # torch_compile=True は Windows で C++ コンパイラが無いと失敗するため無効化
            self._model = timesfm.TimesFM_2p5_200M_torch.from_pretrained(
                "google/timesfm-2.5-200m-pytorch", torch_compile=False
            )

    def predict(self, series: np.ndarray, horizon: int) -> np.ndarray:
        self.load()
        import timesfm
        need = -(-horizon // self.PATCH) * self.PATCH
        # decode は常に max_horizon 分を予測するので、必要な長さに合わせて組み直す
        if need != self._compiled_horizon:
            self._model.compile(timesfm.ForecastConfig(
                max_context=self.MAX_CONTEXT,
                max_horizon=need,
                normalize_inputs=True,
                use_continuous_quantile_head=False,
                force_flip_invariance=True,
                infer_is_positive=False,
                fix_quantile_crossing=False,
            ))
            self._compiled_horizon = need
        point, _ = self._model.forecast(
            horizon=horizon, inputs=[series.astype(np.float32)]
        )
        return np.asarray(point[0][:horizon])


class TimesFMPredictor:
    INPUT_LEN = 2048

    def __init__(self, buffer, backend, target_ch_provider,
                 horizon_sec_provider, poll_interval_sec_provider,
                 input_interval_sec_provider,
                 interval_sec_provider, min_input_points: int = 32,
                 on_status=None):
        self._buffer = buffer
        self._backend = backend
        self._target_ch = target_ch_provider
        self._horizon_sec = horizon_sec_provider
        self._poll_interval = poll_interval_sec_provider
        self._input_interval = input_interval_sec_provider
        self._interval = interval_sec_provider
        self._min_input = min_input_points
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._callback = lambda res: None
        self._on_status = on_status or (lambda kind, msg="": None)
        self._consecutive_failures = 0
        self._last_wait_msg = ""

    def set_callback(self, fn) -> None:
        self._callback = fn

    def start(self) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3.0)

    def _decimated_input(self, ts_arr: np.ndarray, val_arr: np.ndarray,
                          k: int) -> tuple[np.ndarray, np.ndarray]:
        """末尾（最新点）を必ず含め、k 点ごとに 1 点抽出。"""
        if k <= 1:
            return ts_arr[-self.INPUT_LEN:], val_arr[-self.INPUT_LEN:]
        # 末尾から k おきにインデックスを生成し、昇順に並べ替える
        end = len(val_arr) - 1
        idx = np.arange(end, -1, -k)[::-1]
        idx = idx[-self.INPUT_LEN:]
        return ts_arr[idx], val_arr[idx]

    def _load_backend(self) -> bool:
        """モデル読込（初回はダウンロード）。成功するまで 30 秒間隔で再試行。"""
        load = getattr(self._backend, "load", None)
        if load is None:
            return True
        self._on_status("loading", "TimesFM モデル読み込み中（初回はダウンロードに数分かかります）")
        while not self._stop_event.is_set():
            try:
                load()
                self._on_status("ready", "TimesFM 準備完了")
                return True
            except Exception as e:
                log.exception("model load failed")
                self._on_status("error", f"モデル読み込み失敗: {e}")
                self._stop_event.wait(30.0)
        return False

    def _wait_msg(self, msg: str) -> None:
        if msg != self._last_wait_msg:
            self._last_wait_msg = msg
            self._on_status("waiting", msg)

    def _run(self) -> None:
        if not self._load_backend():
            return
        while not self._stop_event.is_set():
            ch = self._target_ch()
            if ch is None:
                self._stop_event.wait(self._interval())
                continue
            poll = max(self._poll_interval(), 1e-6)
            input_interval = max(self._input_interval(), poll)
            k = max(1, int(round(input_interval / poll)))
            ts_arr, val_arr = self._buffer.latest(ch, self.INPUT_LEN * k)
            ts_in, val_in = self._decimated_input(ts_arr, val_arr, k)
            if len(val_in) < self._min_input:
                self._wait_msg(f"データ蓄積中（{len(val_in)}/{self._min_input}点）")
                self._stop_event.wait(self._interval())
                continue
            self._last_wait_msg = ""
            horizon_steps = max(1, int(self._horizon_sec() / input_interval))
            try:
                t0 = time.perf_counter()
                pred = self._backend.predict(val_in, horizon_steps)
                dt = time.perf_counter() - t0
                self._consecutive_failures = 0
                self._callback(PredictionResult(
                    channel=ch,
                    last_timestamp=float(ts_in[-1]),
                    input_interval_sec=float(input_interval),
                    horizon_values=pred,
                    inference_time_sec=dt,
                ))
            except Exception as e:
                log.warning("predict failed: %s", e)
                self._on_status("error", f"予測失敗: {e}")
                self._consecutive_failures += 1
                if self._consecutive_failures >= 3:
                    log.error("predictor paused after 3 failures")
                    self._stop_event.wait(10.0)
                    self._consecutive_failures = 0
            self._stop_event.wait(self._interval())
