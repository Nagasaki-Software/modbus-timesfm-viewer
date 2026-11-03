from __future__ import annotations
import time
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QStatusBar, QLabel


class AppStatusBar(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.poll_label = QLabel("取得: -")
        self.predict_label = QLabel("予測間隔: -")
        self.err_label = QLabel("エラー: 0")
        self.last_err_label = QLabel("")
        for w in (self.poll_label, self.predict_label, self.err_label, self.last_err_label):
            self.addPermanentWidget(w)
        self._sample_count = 0
        self._last_count = 0
        self._fps = 0.0
        self._error_count = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_fps)
        self._timer.start(1000)

    def on_sample(self) -> None:
        self._sample_count += 1

    def on_error(self, msg: str) -> None:
        self._error_count += 1
        ts = time.strftime("%H:%M:%S")
        self.err_label.setText(f"エラー: {self._error_count}")
        self.last_err_label.setText(f"最終: {ts} {msg}")

    def set_predict_interval(self, sec: int) -> None:
        self.predict_label.setText(f"予測間隔: {sec} 秒")

    def _update_fps(self) -> None:
        diff = self._sample_count - self._last_count
        self._last_count = self._sample_count
        self.poll_label.setText(f"取得: {diff} sps")
