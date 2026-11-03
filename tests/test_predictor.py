import time
import numpy as np
import pytest
from app.ring_buffer import RingBuffer
from app.predictor import TimesFMPredictor


class FakeBackend:
    def __init__(self):
        self.last_input = None

    def predict(self, series: np.ndarray, horizon: int) -> np.ndarray:
        self.last_input = series.copy()
        return np.full(horizon, series[-1] + 1.0)


def _make_predictor(buf, fb, *, horizon=10, poll=1.0, input_interval=1.0, interval=0.1):
    return TimesFMPredictor(
        buffer=buf, backend=fb, target_ch_provider=lambda: 1,
        horizon_sec_provider=lambda: horizon,
        poll_interval_sec_provider=lambda: poll,
        input_interval_sec_provider=lambda: input_interval,
        interval_sec_provider=lambda: interval,
    )


def test_predictor_produces_horizon_length():
    buf = RingBuffer(capacity=512)
    for i in range(100):
        buf.push(1, float(i), float(i))
    fb = FakeBackend()
    p = _make_predictor(buf, fb, horizon=10, poll=1.0, input_interval=1.0)
    results = []
    p.set_callback(lambda res: results.append(res))
    p.start()
    time.sleep(0.5)
    p.stop()
    assert len(results) >= 2
    last = results[-1]
    assert last.horizon_values.shape == (10,)
    assert last.inference_time_sec > 0
    assert last.input_interval_sec == 1.0


def test_predictor_no_data_skips_silently():
    buf = RingBuffer(capacity=512)
    fb = FakeBackend()
    p = _make_predictor(buf, fb)
    results = []
    p.set_callback(lambda res: results.append(res))
    p.start()
    time.sleep(0.3)
    p.stop()
    assert results == []


def test_predictor_decimates_input_when_input_interval_larger():
    """取得周期 1s、入力周期 3s なら 3 点ごとに 1 点を抽出して TimesFM に渡す。"""
    buf = RingBuffer(capacity=512)
    for i in range(60):
        buf.push(1, float(i), float(i))  # 0..59
    fb = FakeBackend()
    # min_input=5 で短いデータでも発火させる
    p = TimesFMPredictor(
        buffer=buf, backend=fb, target_ch_provider=lambda: 1,
        horizon_sec_provider=lambda: 9,
        poll_interval_sec_provider=lambda: 1.0,
        input_interval_sec_provider=lambda: 3.0,
        interval_sec_provider=lambda: 0.1,
        min_input_points=5,
    )
    results = []
    p.set_callback(lambda res: results.append(res))
    p.start()
    time.sleep(0.4)
    p.stop()
    assert len(results) >= 1
    # 入力配列の末尾は最新の 59、間隔は 3 → 末尾から 59, 56, 53, ...
    assert fb.last_input is not None
    assert fb.last_input[-1] == 59.0
    assert fb.last_input[-2] == 56.0
    # horizon_steps = 9s / 3s = 3
    assert results[-1].horizon_values.shape == (3,)
    assert results[-1].input_interval_sec == 3.0


class LoadableBackend(FakeBackend):
    def __init__(self, fail_times=0):
        super().__init__()
        self.loaded = 0
        self.fail_times = fail_times

    def load(self):
        if self.fail_times > 0:
            self.fail_times -= 1
            raise RuntimeError("download failed")
        self.loaded += 1


def test_predictor_loads_backend_and_reports_status():
    buf = RingBuffer(capacity=512)
    for i in range(100):
        buf.push(1, float(i), float(i))
    fb = LoadableBackend()
    events = []
    p = _make_predictor(buf, fb)
    p._on_status = lambda kind, msg="": events.append(kind)
    results = []
    p.set_callback(results.append)
    p.start()
    time.sleep(0.5)
    p.stop()
    assert fb.loaded == 1
    assert events[:2] == ["loading", "ready"]
    assert len(results) >= 1


def test_predictor_reports_load_failure():
    buf = RingBuffer(capacity=512)
    fb = LoadableBackend(fail_times=1)
    events = []
    p = _make_predictor(buf, fb)
    p._on_status = lambda kind, msg="": events.append((kind, msg))
    p.start()
    time.sleep(0.3)
    p.stop()
    assert ("error", "モデル読み込み失敗: download failed") in events


def test_predictor_reports_waiting_when_data_short():
    buf = RingBuffer(capacity=512)
    for i in range(5):
        buf.push(1, float(i), float(i))
    events = []
    p = _make_predictor(buf, FakeBackend())
    p._on_status = lambda kind, msg="": events.append((kind, msg))
    p.start()
    time.sleep(0.3)
    p.stop()
    waits = [m for k, m in events if k == "waiting"]
    assert waits == ["データ蓄積中（5/32点）"]


def test_predictor_works_with_long_input_interval_and_big_buffer():
    """入力周期 100 秒でも、バッファが十分大きければ予測が始まる。"""
    buf = RingBuffer(capacity=32768)
    for i in range(4000):
        buf.push(1, float(i), float(i))
    fb = FakeBackend()
    p = _make_predictor(buf, fb, horizon=1000, poll=1.0, input_interval=100.0)
    results = []
    p.set_callback(results.append)
    p.start()
    time.sleep(0.4)
    p.stop()
    assert len(results) >= 1
    assert results[-1].horizon_values.shape == (10,)
