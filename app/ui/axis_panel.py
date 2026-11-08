from __future__ import annotations
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QCheckBox, QDoubleSpinBox, QPushButton, QLabel
)


class AxisPanel(QWidget):
    axisChanged = pyqtSignal(bool, float, float, float)  # auto, y_min, y_max, tick

    MAX_TICKS = 100  # 目盛りが多すぎると描画が重くなるため

    def __init__(self, parent=None):
        super().__init__(parent)
        grid = QGridLayout(self)
        self.auto_check = QCheckBox("データに合わせて自動")
        self.min_spin = self._spin()
        self.max_spin = self._spin()
        self.tick_spin = self._spin()
        self.tick_spin.setMinimum(0.0)
        self.apply_btn = QPushButton("適用")
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #c0392b;")
        self.error_label.setWordWrap(True)
        # 左の列が縦に長くならないよう、2列に詰めて並べる
        grid.addWidget(self.auto_check, 0, 0, 1, 4)
        grid.addWidget(QLabel("最小値:"), 1, 0)
        grid.addWidget(self.min_spin, 1, 1)
        grid.addWidget(QLabel("最大値:"), 1, 2)
        grid.addWidget(self.max_spin, 1, 3)
        grid.addWidget(QLabel("目盛り間隔:"), 2, 0)
        grid.addWidget(self.tick_spin, 2, 1)
        grid.addWidget(self.apply_btn, 2, 2, 1, 2)
        grid.addWidget(self.error_label, 3, 0, 1, 4)
        self.error_label.hide()
        self.auto_check.toggled.connect(self._on_auto_toggled)
        self.apply_btn.clicked.connect(self._apply)

    @staticmethod
    def _spin() -> QDoubleSpinBox:
        s = QDoubleSpinBox()
        s.setRange(-999999.0, 999999.0)  # 広すぎると入力欄が横に伸びて左の列が広がる
        s.setDecimals(3)
        return s

    def set_values(self, auto: bool, y_min: float, y_max: float, tick: float) -> None:
        """設定ファイルの値を画面に入れる（シグナルは出さない）。"""
        self.min_spin.setValue(y_min)
        self.max_spin.setValue(y_max)
        self.tick_spin.setValue(tick)
        self.auto_check.blockSignals(True)
        self.auto_check.setChecked(auto)
        self.auto_check.blockSignals(False)
        self._set_fields_enabled(not auto)

    def values(self) -> tuple[bool, float, float, float]:
        return (self.auto_check.isChecked(), self.min_spin.value(),
                self.max_spin.value(), self.tick_spin.value())

    def _set_fields_enabled(self, enabled: bool) -> None:
        for w in (self.min_spin, self.max_spin, self.tick_spin, self.apply_btn):
            w.setEnabled(enabled)

    def _on_auto_toggled(self, auto: bool) -> None:
        self._set_fields_enabled(not auto)
        if auto:
            self._show_error("")
            self.axisChanged.emit(*self.values())
        else:
            self._apply()

    def _apply(self) -> None:
        auto, y_min, y_max, tick = self.values()
        if y_min >= y_max:
            self._show_error("最大値は最小値より大きくしてください。")
            return
        if tick <= 0:
            self._show_error("目盛り間隔は 0 より大きくしてください。")
            return
        if (y_max - y_min) / tick > self.MAX_TICKS:
            self._show_error(
                f"目盛りが {self.MAX_TICKS} 本を超えます。間隔を広げてください。")
            return
        self._show_error("")
        self.axisChanged.emit(auto, y_min, y_max, tick)

    def _show_error(self, text: str) -> None:
        self.error_label.setText(text)
        self.error_label.setVisible(bool(text))
