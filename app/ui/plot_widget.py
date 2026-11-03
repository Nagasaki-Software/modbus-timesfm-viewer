from __future__ import annotations
from collections import deque
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout

pg.setConfigOptions(antialias=True, background="w", foreground="k")


class PlotWidget(QWidget):
    MAX_POINTS = 2048

    def __init__(self, parent=None):
        super().__init__(parent)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        self._plot = pg.PlotWidget()
        self._plot.showGrid(x=True, y=True, alpha=0.3)
        self._plot.addLegend()
        date_axis = pg.DateAxisItem(orientation="bottom")
        self._plot.setAxisItems({"bottom": date_axis})
        v.addWidget(self._plot)
        self._actual: dict[int, dict] = {}     # ch -> {ts: deque, val: deque, curve, color, name}
        self._predicted: dict[int, dict] = {}  # ch -> {curve, color}

    def configure_channel(self, ch: int, name: str, color: str) -> None:
        if ch in self._actual:
            self._actual[ch]["color"] = color
            self._actual[ch]["name"] = name
            self._actual[ch]["curve"].setPen(pg.mkPen(color, width=2))
            return
        curve = self._plot.plot([], [], pen=pg.mkPen(color, width=2), name=f"{name} 実測")
        self._actual[ch] = {
            "ts": deque(maxlen=self.MAX_POINTS),
            "val": deque(maxlen=self.MAX_POINTS),
            "curve": curve,
            "color": color,
            "name": name,
        }
        pred_curve = self._plot.plot([], [], pen=pg.mkPen(color, width=2, style=pg.QtCore.Qt.PenStyle.DashLine),
                                      name=f"{name} 予測")
        self._predicted[ch] = {"curve": pred_curve, "color": color}

    def set_visible(self, ch: int, visible: bool) -> None:
        if ch in self._actual:
            self._actual[ch]["curve"].setVisible(visible)
        if ch in self._predicted:
            self._predicted[ch]["curve"].setVisible(visible)

    def remove_channel(self, ch: int) -> None:
        for store in (self._actual, self._predicted):
            if ch in store:
                self._plot.removeItem(store[ch]["curve"])
                del store[ch]

    def append_sample(self, ch: int, ts: float, value: float) -> None:
        rec = self._actual.get(ch)
        if rec is None:
            return
        rec["ts"].append(ts)
        rec["val"].append(value)
        rec["curve"].setData(np.fromiter(rec["ts"], dtype=float),
                              np.fromiter(rec["val"], dtype=float))

    def set_prediction(self, ch: int, last_ts: float, input_interval: float,
                       horizon_values: np.ndarray) -> None:
        """予測線を入力周期刻みで右側に延長描画する。"""
        rec = self._predicted.get(ch)
        if rec is None:
            return
        h = len(horizon_values)
        ts_arr = last_ts + np.arange(1, h + 1) * input_interval
        rec["curve"].setData(ts_arr, horizon_values)

    def clear_prediction(self, ch: int) -> None:
        rec = self._predicted.get(ch)
        if rec is None:
            return
        rec["curve"].setData([], [])
