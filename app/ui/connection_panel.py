from __future__ import annotations
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QPushButton, QLabel, QVBoxLayout, QHBoxLayout
)
from PyQt6.QtGui import QIntValidator


class ConnectionPanel(QWidget):
    connectRequested = pyqtSignal(str, int, int)  # host, port, unit
    disconnectRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.host_edit = QLineEdit()
        self.port_edit = QLineEdit("502")
        self.port_edit.setValidator(QIntValidator(1, 65535, self))
        self.unit_edit = QLineEdit("1")
        self.unit_edit.setValidator(QIntValidator(0, 255, self))
        form.addRow("IPアドレス:", self.host_edit)
        form.addRow("ポート:", self.port_edit)
        form.addRow("ユニットID:", self.unit_edit)
        layout.addLayout(form)
        btns = QHBoxLayout()
        self.connect_btn = QPushButton("接続")
        self.disconnect_btn = QPushButton("切断")
        btns.addWidget(self.connect_btn)
        btns.addWidget(self.disconnect_btn)
        layout.addLayout(btns)
        self.status_label = QLabel("状態: 未接続")
        layout.addWidget(self.status_label)
        layout.addStretch()
        self.connect_btn.clicked.connect(self._on_connect)
        self.disconnect_btn.clicked.connect(self.disconnectRequested.emit)

    def _on_connect(self) -> None:
        try:
            host = self.host_edit.text().strip()
            port = int(self.port_edit.text())
            unit = int(self.unit_edit.text())
        except ValueError:
            self.set_status("error", "入力値が不正です")
            return
        self.connectRequested.emit(host, port, unit)

    def set_status(self, state: str, message: str = "") -> None:
        labels = {
            "connected": ("接続中", "color: #2a8;"),
            "disconnected": ("切断", "color: #888;"),
            "retrying": ("再接続中", "color: #c80;"),
            "error": ("エラー", "color: #c33;"),
        }
        text, style = labels.get(state, ("未接続", "color: #888;"))
        self.status_label.setText(f"状態: {text}  {message}")
        self.status_label.setStyleSheet(style)
        connected = state == "connected"
        for w in (self.host_edit, self.port_edit, self.unit_edit):
            w.setEnabled(not connected)
        self.connect_btn.setEnabled(not connected)
        self.disconnect_btn.setEnabled(connected)
