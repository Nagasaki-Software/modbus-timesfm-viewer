from __future__ import annotations
from pathlib import Path
import logging
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QGroupBox, QScrollArea
)

from app import __version__
from app.config import Config
from app.ring_buffer import RingBuffer
from app.signals import AppSignals
from app.ui.menu_bar import AppMenuBar
from app.ui.connection_panel import ConnectionPanel
from app.ui.channel_panel import ChannelPanel
from app.ui.prediction_panel import PredictionPanel
from app.ui.axis_panel import AxisPanel
from app.ui.plot_widget import PlotWidget
from app.ui.status_bar import AppStatusBar

log = logging.getLogger(__name__)
CONFIG_PATH = Path.home() / ".modbus-timesfm-viewer" / "config.toml"


class MainWindow(QMainWindow):
    def __init__(self, parent=None, start_workers: bool = True):
        super().__init__(parent)
        self.setWindowTitle(f"Modbus × TimesFM リアルタイム予測ビューア v{__version__}")
        self.setMenuBar(AppMenuBar(self))
        self._signals = AppSignals()
        self._buffer = RingBuffer(capacity=32768)  # 入力周期を長くしても必要点数を確保
        self._modbus = None
        self._predictor = None
        self._cfg = Config.load(CONFIG_PATH)
        self._backend = None  # TimesFM は1回だけ読み込み、再接続でも使い回す
        self._params = {"target": None, "horizon": 60, "interval": 5, "input_interval": 1}

        central = QWidget()
        self.setCentralWidget(central)
        outer = QHBoxLayout(central)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        left = QWidget(); left_v = QVBoxLayout(left)
        self.connection_panel = ConnectionPanel()
        self.channel_panel = ChannelPanel()
        self.prediction_panel = PredictionPanel()
        self.axis_panel = AxisPanel()
        for title, w in (("接続", self.connection_panel),
                          ("チャネル", self.channel_panel),
                          ("予測設定", self.prediction_panel),
                          ("縦軸", self.axis_panel)):
            box = QGroupBox(title); bv = QVBoxLayout(box); bv.addWidget(w)
            left_v.addWidget(box)
        left_v.addStretch()
        # 窓が低いときにチャネル表が潰れないよう、左の列は縦にスクロールさせる
        self.channel_panel.table.setMinimumHeight(140)
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        left_scroll.setWidget(left)
        left_scroll.setMinimumWidth(left.minimumSizeHint().width() + 20)  # 縦スクロールバーの分
        splitter.addWidget(left_scroll)
        self.plot_widget = PlotWidget()
        splitter.addWidget(self.plot_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        outer.addWidget(splitter)
        self.status = AppStatusBar(self)
        self.setStatusBar(self.status)

        self._restore_config_to_ui()
        self._wire_signals()
        self._sync_params()
        if start_workers and self._cfg.host:
            pass  # ユーザーが「接続」ボタンを押すまで自動接続しない

    def _restore_config_to_ui(self) -> None:
        c = self._cfg
        self.connection_panel.host_edit.setText(c.host)
        self.connection_panel.port_edit.setText(str(c.port))
        self.connection_panel.unit_edit.setText(str(c.unit_id))
        self.channel_panel.set_channels(c.channels)
        self.prediction_panel.set_poll_interval(c.poll_interval_sec)
        self.prediction_panel.input_interval_slider.setValue(int(c.predict_input_interval_sec))
        self.prediction_panel.horizon_slider.setValue(c.horizon_sec)
        self.prediction_panel.interval_slider.setValue(int(c.predict_interval_sec))
        self.status.set_predict_interval(int(c.predict_interval_sec))
        for ch in c.channels:
            self.plot_widget.configure_channel(ch.ch, ch.name, ch.color, ch.decimals)
            self.plot_widget.set_visible(ch.ch, ch.visible)
        self.axis_panel.set_values(c.y_auto, c.y_min, c.y_max, c.y_tick)
        self.plot_widget.set_y_axis(c.y_auto, c.y_min, c.y_max, c.y_tick)
        if c.window_geometry:
            self.setGeometry(*c.window_geometry)

    def _wire_signals(self) -> None:
        self.connection_panel.connectRequested.connect(self._on_connect)
        self.connection_panel.disconnectRequested.connect(self._on_disconnect)
        self.channel_panel.channelsChanged.connect(self._on_channels_changed)
        self.channel_panel.visibilityChanged.connect(self.plot_widget.set_visible)
        self.channel_panel.predictTargetChanged.connect(self._on_predict_target_changed)
        self.prediction_panel.intervalChanged.connect(self.status.set_predict_interval)
        self.axis_panel.axisChanged.connect(self._on_axis_changed)
        for sig in (self.prediction_panel.horizonChanged,
                    self.prediction_panel.intervalChanged,
                    self.prediction_panel.inputIntervalChanged,
                    self.channel_panel.channelsChanged,
                    self.channel_panel.predictTargetChanged):
            sig.connect(lambda *_: self._sync_params())
        self._signals.sampleReceived.connect(self._on_sample)
        self._signals.connectionStatusChanged.connect(self.connection_panel.set_status)
        self._signals.connectionStatusChanged.connect(self._on_connection_status)
        self._signals.predictionReady.connect(self._on_prediction)
        self._signals.predictorStatusChanged.connect(self._on_predictor_status)

    def _sync_params(self) -> None:
        """予測スレッドが読む値を GUI スレッドで更新する（スレッドから GUI 部品を直接読まない）。"""
        self._params = {
            "target": self.channel_panel.get_predict_target(),
            "horizon": self.prediction_panel.horizon_sec(),
            "interval": self.prediction_panel.interval_sec(),
            "input_interval": self.prediction_panel.input_interval_sec(),
        }

    def _on_predict_target_changed(self, ch: int) -> None:
        for other in list(self.plot_widget._predicted.keys()):
            if other != ch:
                self.plot_widget.clear_prediction(other)
        self._cfg.channels = self.channel_panel.get_channels()
        self._cfg.save(CONFIG_PATH)

    @pyqtSlot(str, str)
    def _on_connection_status(self, state: str, message: str) -> None:
        if state in ("retrying", "error") or (state == "disconnected" and message):
            self.status.on_error(f"通信 {message}" if message else "通信 再接続中")

    @pyqtSlot(str, str)
    def _on_predictor_status(self, kind: str, message: str) -> None:
        log.info("predictor %s: %s", kind, message)
        if kind == "error":
            self.status.on_error(message)
        elif kind == "ready":
            self.status.showMessage(message, 5000)
        else:
            self.status.showMessage(message)

    @pyqtSlot(int, float, float)
    def _on_sample(self, ch: int, ts: float, value: float) -> None:
        self.plot_widget.append_sample(ch, ts, value)
        self.status.on_sample()

    @pyqtSlot(int, float, float, object, float)
    def _on_prediction(self, ch: int, last_ts: float, input_interval: float,
                        horizon_values, inference_time: float) -> None:
        self.plot_widget.set_prediction(ch, last_ts, input_interval, horizon_values)
        self.prediction_panel.show_inference_time(inference_time)

    def _on_connect(self, host: str, port: int, unit: int) -> None:
        from app.modbus_client import ModbusClient
        if self._modbus:
            self._modbus.stop()
        self._cfg.host = host; self._cfg.port = port; self._cfg.unit_id = unit
        self._buffer.clear()  # 前回接続のデータを TimesFM 入力に混ぜない
        self._cfg.channels = self.channel_panel.get_channels()
        self._cfg.save(CONFIG_PATH)
        for ch in self._cfg.channels:
            self.plot_widget.configure_channel(ch.ch, ch.name, ch.color, ch.decimals)
            self.plot_widget.set_visible(ch.ch, ch.visible)
        self._modbus = ModbusClient(
            host=host, port=port, unit_id=unit,
            poll_interval_sec=self._cfg.poll_interval_sec,
            channels=self._cfg.channels,
            buffer=self._buffer,
            on_status=lambda s, m="": self._signals.connectionStatusChanged.emit(s, m),
        )
        # ModbusClient はコールバックではなくシグナル経由でサンプルを通知できないため、
        # 別途ポーリングしてグラフへ流す薄いブリッジを設ける（_pump_buffer_to_signals）。
        self._modbus.start()
        self._start_buffer_pump()
        self._start_predictor()

    def _on_disconnect(self) -> None:
        if self._modbus:
            self._modbus.stop()
            self._modbus = None
        if self._predictor:
            self._predictor.stop()
            self._predictor = None
        if hasattr(self, "_pump_timer"):
            self._pump_timer.stop()
        self._signals.connectionStatusChanged.emit("disconnected", "")

    def _start_buffer_pump(self) -> None:
        from PyQt6.QtCore import QTimer
        if hasattr(self, "_pump_timer"):  # 再接続で二重に動かさない
            self._pump_timer.stop()
            self._pump_timer.deleteLater()
        self._pump_state: dict[int, float] = {}  # ch -> 最後に描画した ts

        def pump():
            for ch in self.channel_panel.get_channels():
                ts_arr, val_arr = self._buffer.latest(ch.ch, 256)
                last = self._pump_state.get(ch.ch, -1.0)
                for ts, val in zip(ts_arr, val_arr):
                    if ts > last:
                        self._signals.sampleReceived.emit(ch.ch, float(ts), float(val))
                        last = float(ts)
                self._pump_state[ch.ch] = last
        self._pump_timer = QTimer(self)
        self._pump_timer.timeout.connect(pump)
        self._pump_timer.start(200)

    def _start_predictor(self) -> None:
        from app.predictor import TimesFMPredictor, TimesFM25Backend
        if self._predictor:
            self._predictor.stop()
        if self._backend is None:
            self._backend = TimesFM25Backend()  # モデル読込は予測スレッド側で行う
        # 予測スレッドは GUI 部品ではなく self._params だけを読む
        self._predictor = TimesFMPredictor(
            buffer=self._buffer, backend=self._backend,
            target_ch_provider=lambda: self._params["target"],
            horizon_sec_provider=lambda: self._params["horizon"],
            poll_interval_sec_provider=lambda: self._cfg.poll_interval_sec,
            input_interval_sec_provider=lambda: float(self._params["input_interval"]),
            interval_sec_provider=lambda: self._params["interval"],
            on_status=lambda kind, msg="": self._signals.predictorStatusChanged.emit(kind, msg),
        )

        def on_result(res):
            self._signals.predictionReady.emit(
                res.channel, res.last_timestamp, res.input_interval_sec,
                res.horizon_values, res.inference_time_sec,
            )
        self._predictor.set_callback(on_result)
        self._predictor.start()

    def _on_channels_changed(self) -> None:
        chs = self.channel_panel.get_channels()
        existing = set()
        for ch in chs:
            existing.add(ch.ch)
            self.plot_widget.configure_channel(ch.ch, ch.name, ch.color, ch.decimals)
            self.plot_widget.set_visible(ch.ch, ch.visible)
        for ch in list(self.plot_widget._actual.keys()):
            if ch not in existing:
                self.plot_widget.remove_channel(ch)
        self._cfg.channels = chs
        self._cfg.save(CONFIG_PATH)

    def _on_axis_changed(self, auto: bool, y_min: float, y_max: float, tick: float) -> None:
        self.plot_widget.set_y_axis(auto, y_min, y_max, tick)
        c = self._cfg
        c.y_auto, c.y_min, c.y_max, c.y_tick = auto, y_min, y_max, tick
        c.save(CONFIG_PATH)

    def closeEvent(self, e) -> None:
        if self._modbus: self._modbus.stop()
        if self._predictor: self._predictor.stop()
        g = self.geometry()
        self._cfg.window_geometry = [g.x(), g.y(), g.width(), g.height()]
        self._cfg.horizon_sec = self.prediction_panel.horizon_sec()
        self._cfg.predict_interval_sec = float(self.prediction_panel.interval_sec())
        self._cfg.predict_input_interval_sec = float(self.prediction_panel.input_interval_sec())
        self._cfg.save(CONFIG_PATH)
        super().closeEvent(e)
