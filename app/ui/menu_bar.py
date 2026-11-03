from __future__ import annotations
from datetime import datetime
from typing import Callable
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QMenuBar, QLabel


class AppMenuBar(QMenuBar):
    def __init__(self, parent=None, now_provider: Callable[[], datetime] = datetime.now):
        super().__init__(parent)
        self._now = now_provider
        self.addMenu("ファイル(&F)")
        self.addMenu("表示(&V)")
        self.addMenu("ヘルプ(&H)")
        self.clock_label = QLabel("")
        self.clock_label.setContentsMargins(0, 0, 12, 0)
        self.setCornerWidget(self.clock_label, Qt.Corner.TopRightCorner)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.tick)
        self._timer.start(1000)
        self.tick()

    def tick(self) -> None:
        self.clock_label.setText(self._now().strftime("%Y/%m/%d %H:%M:%S"))
