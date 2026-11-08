from __future__ import annotations
from collections import deque
import html
import numpy as np
import pyqtgraph as pg
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel

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
        # グラフの下に、各チャネルの最新値を横一列で出す
        self._values_bar = QHBoxLayout()
        self._values_bar.setContentsMargins(8, 4, 8, 4)
        self._values_bar.setSpacing(24)
        self._values_bar.addStretch()
        v.addLayout(self._values_bar)
        self._actual: dict[int, dict] = {}     # ch -> {ts, val, curve, color, name, decimals, label}
        self._predicted: dict[int, dict] = {}  # ch -> {curve, color}

    def configure_channel(self, ch: int, name: str, color: str, decimals: int = 2) -> None:
        if ch in self._actual:
            rec = self._actual[ch]
            rec["color"] = color
            rec["name"] = name
            rec["decimals"] = decimals
            rec["curve"].setPen(pg.mkPen(color, width=2))
            self._update_value_label(ch)
            return
        curve = self._plot.plot([], [], pen=pg.mkPen(color, width=2), name=f"{name} 実測")
        self._actual[ch] = {
            "ts": deque(maxlen=self.MAX_POINTS),
            "val": deque(maxlen=self.MAX_POINTS),
            "curve": curve,
            "color": color,
            "name": name,
            "decimals": decimals,
            "label": self._make_value_label(),
        }
        self._update_value_label(ch)
        pred_curve = self._plot.plot([], [], pen=pg.mkPen(color, width=2, style=pg.QtCore.Qt.PenStyle.DashLine),
                                      name=f"{name} 予測")
        self._predicted[ch] = {"curve": pred_curve, "color": color}

    def set_visible(self, ch: int, visible: bool) -> None:
        if ch in self._actual:
            self._actual[ch]["curve"].setVisible(visible)
        if ch in self._predicted:
            self._predicted[ch]["curve"].setVisible(visible)
        if ch in self._actual:
            self._actual[ch]["label"].setVisible(visible)

    def remove_channel(self, ch: int) -> None:
        if ch in self._actual:
            label = self._actual[ch]["label"]
            self._values_bar.removeWidget(label)
            label.deleteLater()
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
        self._update_value_label(ch)

    def _make_value_label(self) -> QLabel:
        label = QLabel()
        font = QFont(label.font())
        font.setPointSize(13)
        label.setFont(font)
        self._values_bar.insertWidget(self._values_bar.count() - 1, label)  # 右端の余白より前
        return label

    def _update_value_label(self, ch: int) -> None:
        rec = self._actual[ch]
        value = f"{rec['val'][-1]:.{rec['decimals']}f}" if rec["val"] else "—"
        rec["label"].setText(f'<span style="color:{rec["color"]}">■</span> '
                             f'{html.escape(rec["name"])}　<b>{value}</b>')

    def set_y_axis(self, auto: bool, y_min: float, y_max: float, tick: float) -> None:
        """縦軸を自動にするか、最小・最大・目盛り間隔を固定する。"""
        view = self._plot.getPlotItem().getViewBox()
        axis = self._plot.getAxis("left")
        if auto:
            axis.setTickSpacing()  # 引数なしで pyqtgraph の自動の目盛りに戻る
            view.setMouseEnabled(y=True)
            view.enableAutoRange(axis="y")
        else:
            axis.setTickSpacing(levels=[(tick, y_min)])  # 目盛りを最小値から刻む
            view.setMouseEnabled(y=False)  # ホイールで縦の範囲がずれないように
            view.setYRange(y_min, y_max, padding=0.02)  # 端ぴったりだと最小・最大の数字が隠れる

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
