from __future__ import annotations
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox,
    QDialogButtonBox, QColorDialog, QPushButton
)
from PyQt6.QtGui import QColor
from app.config import ChannelConfig


class ChannelEditDialog(QDialog):
    def __init__(self, parent=None, channel: ChannelConfig | None = None):
        super().__init__(parent)
        self.setWindowTitle("チャネル編集")
        form = QFormLayout(self)
        self.ch_spin = QSpinBox(); self.ch_spin.setRange(1, 100)
        self.name_edit = QLineEdit()
        self.addr_spin = QSpinBox(); self.addr_spin.setRange(0, 65535)
        self.dtype = QComboBox(); self.dtype.addItems(["float32", "int16", "int32"])
        self.order = QComboBox(); self.order.addItems(["ABCD", "CDAB", "BADC", "DCBA"])
        self._color = "#1f77b4"
        self.color_btn = QPushButton("色を選ぶ")
        self.color_btn.clicked.connect(self._pick_color)
        self._update_color_btn()
        form.addRow("ch番号:", self.ch_spin)
        form.addRow("表示名:", self.name_edit)
        form.addRow("レジスタアドレス:", self.addr_spin)
        form.addRow("データ型:", self.dtype)
        form.addRow("バイト順:", self.order)
        form.addRow("表示色:", self.color_btn)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)
        if channel is not None:
            self.ch_spin.setValue(channel.ch)
            self.name_edit.setText(channel.name)
            self.addr_spin.setValue(channel.address)
            self.dtype.setCurrentText(channel.data_type)
            self.order.setCurrentText(channel.byte_order)
            self._color = channel.color
            self._update_color_btn()

    def _pick_color(self) -> None:
        c = QColorDialog.getColor(QColor(self._color), self)
        if c.isValid():
            self._color = c.name()
            self._update_color_btn()

    def _update_color_btn(self) -> None:
        self.color_btn.setStyleSheet(f"background-color: {self._color};")

    def result_channel(self, visible: bool = True, predict_target: bool = False) -> ChannelConfig:
        return ChannelConfig(
            ch=self.ch_spin.value(),
            name=self.name_edit.text(),
            address=self.addr_spin.value(),
            data_type=self.dtype.currentText(),
            byte_order=self.order.currentText(),
            color=self._color,
            visible=visible,
            predict_target=predict_target,
        )
