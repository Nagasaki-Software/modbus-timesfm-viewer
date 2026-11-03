from __future__ import annotations
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QRadioButton, QHeaderView, QCheckBox, QButtonGroup, QMessageBox
)
from app.config import ChannelConfig
from app.ui.channel_edit_dialog import ChannelEditDialog


class ChannelPanel(QWidget):
    channelsChanged = pyqtSignal()
    predictTargetChanged = pyqtSignal(int)
    visibilityChanged = pyqtSignal(int, bool)

    COLS = ["表示", "ch", "名前", "アドレス", "型", "バイト順", "色", "予測対象"]

    def __init__(self, parent=None):
        super().__init__(parent)
        v = QVBoxLayout(self)
        self.table = QTableWidget(0, len(self.COLS))
        self.table.setHorizontalHeaderLabels(self.COLS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        v.addWidget(self.table)
        h = QHBoxLayout()
        self.add_btn = QPushButton("追加")
        self.edit_btn = QPushButton("編集")
        self.remove_btn = QPushButton("削除")
        h.addWidget(self.add_btn); h.addWidget(self.edit_btn); h.addWidget(self.remove_btn)
        v.addLayout(h)
        self._radio_group = QButtonGroup(self)
        self._channels: list[ChannelConfig] = []
        self.add_btn.clicked.connect(self._add)
        self.edit_btn.clicked.connect(self._edit)
        self.remove_btn.clicked.connect(self._remove)

    def set_channels(self, channels: list[ChannelConfig]) -> None:
        self._channels = [ChannelConfig(**c.__dict__) for c in channels]
        self._refresh()

    def get_channels(self) -> list[ChannelConfig]:
        return [ChannelConfig(**c.__dict__) for c in self._channels]

    def get_predict_target(self) -> int | None:
        for c in self._channels:
            if c.predict_target:
                return c.ch
        return None

    def set_predict_target(self, ch: int) -> None:
        for c in self._channels:
            c.predict_target = (c.ch == ch)
        self._refresh()
        self.predictTargetChanged.emit(ch)

    def _refresh(self) -> None:
        self.table.setRowCount(0)
        for row, c in enumerate(self._channels):
            self.table.insertRow(row)
            vis = QCheckBox(); vis.setChecked(c.visible)
            vis.toggled.connect(lambda v, ch=c.ch: self._on_vis_toggled(ch, v))
            self.table.setCellWidget(row, 0, vis)
            for col, text in enumerate([str(c.ch), c.name, str(c.address), c.data_type, c.byte_order], start=1):
                self.table.setItem(row, col, QTableWidgetItem(text))
            color_item = QTableWidgetItem(c.color)
            color_item.setBackground(Qt.GlobalColor.transparent)
            self.table.setItem(row, 6, color_item)
            rb = QRadioButton(); rb.setChecked(c.predict_target)
            rb.toggled.connect(lambda checked, ch=c.ch: checked and self.set_predict_target(ch))
            self.table.setCellWidget(row, 7, rb)

    def _on_vis_toggled(self, ch: int, visible: bool) -> None:
        for c in self._channels:
            if c.ch == ch:
                c.visible = visible
                break
        self.visibilityChanged.emit(ch, visible)
        self.channelsChanged.emit()

    def _add(self) -> None:
        dlg = ChannelEditDialog(self)
        if dlg.exec():
            new = dlg.result_channel(visible=True, predict_target=False)
            if self._is_duplicate(new.ch, skip_row=-1):
                return
            self._channels.append(new)
            self._refresh()
            self.channelsChanged.emit()

    def _edit(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._channels):
            return
        old = self._channels[row]
        dlg = ChannelEditDialog(self, channel=old)
        if dlg.exec():
            updated = dlg.result_channel(visible=old.visible, predict_target=old.predict_target)
            if self._is_duplicate(updated.ch, skip_row=row):
                return
            self._channels[row] = updated
            self._refresh()
            self.channelsChanged.emit()

    def _is_duplicate(self, ch: int, skip_row: int) -> bool:
        if any(c.ch == ch for i, c in enumerate(self._channels) if i != skip_row):
            QMessageBox.warning(self, "チャネル番号の重複",
                                f"ch{ch} は既に登録されています。別の番号にしてください。")
            return True
        return False

    def _remove(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._channels):
            return
        del self._channels[row]
        self._refresh()
        self.channelsChanged.emit()
