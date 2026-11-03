from __future__ import annotations
import math
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget, QFormLayout, QSlider, QLabel, QVBoxLayout
)


class PredictionPanel(QWidget):
    horizonChanged = pyqtSignal(int)
    intervalChanged = pyqtSignal(int)
    inputIntervalChanged = pyqtSignal(int)  # TimesFM 入力周期（秒）

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.input_interval_slider = QSlider(Qt.Orientation.Horizontal)
        self.input_interval_slider.setRange(1, 600)
        self.input_interval_slider.setValue(1)
        self.input_interval_label = QLabel("1 秒（間引きなし）")
        self.input_interval_slider.valueChanged.connect(self._on_input_changed)
        form.addRow("TimesFM 入力周期:", self.input_interval_slider)
        form.addRow("", self.input_interval_label)

        self.horizon_slider = QSlider(Qt.Orientation.Horizontal)
        self.horizon_slider.setRange(10, 3600)
        self.horizon_slider.setValue(60)
        self.horizon_label = QLabel("60 秒")
        self.horizon_slider.valueChanged.connect(
            lambda v: (self.horizon_label.setText(f"{v} 秒"), self.horizonChanged.emit(v))
        )
        form.addRow("ホライズン:", self.horizon_slider)
        form.addRow("", self.horizon_label)

        self.interval_slider = QSlider(Qt.Orientation.Horizontal)
        self.interval_slider.setRange(1, 60)
        self.interval_slider.setValue(5)
        self.interval_label = QLabel("5 秒")
        self.interval_slider.valueChanged.connect(
            lambda v: (self.interval_label.setText(f"{v} 秒"), self.intervalChanged.emit(v))
        )
        form.addRow("実行間隔:", self.interval_slider)
        form.addRow("", self.interval_label)

        self.model_label = QLabel("TimesFM 2.5")
        form.addRow("モデル:", self.model_label)
        self.inference_label = QLabel("-")
        form.addRow("最終推論時間:", self.inference_label)
        layout.addLayout(form)
        layout.addStretch()
        self._poll_interval = 1.0

    def _on_input_changed(self, v: int) -> None:
        ratio = v / self._poll_interval
        if ratio <= 1.0001:
            self.input_interval_label.setText(f"{v} 秒（間引きなし）")
        else:
            self.input_interval_label.setText(f"{v} 秒（{ratio:.0f}点に1点）")
        self.inputIntervalChanged.emit(v)

    def set_poll_interval(self, poll_sec: float) -> None:
        """取得周期の変更を反映。入力周期は取得周期以上にクランプ。"""
        self._poll_interval = max(float(poll_sec), 0.001)
        min_sec = max(1, math.ceil(self._poll_interval))
        self.input_interval_slider.setMinimum(min_sec)
        if self.input_interval_slider.value() < min_sec:
            self.input_interval_slider.setValue(min_sec)
        self._on_input_changed(self.input_interval_slider.value())

    def show_inference_time(self, sec: float) -> None:
        self.inference_label.setText(f"{sec:.2f} 秒")

    def horizon_sec(self) -> int:
        return self.horizon_slider.value()

    def interval_sec(self) -> int:
        return self.interval_slider.value()

    def input_interval_sec(self) -> int:
        return self.input_interval_slider.value()
