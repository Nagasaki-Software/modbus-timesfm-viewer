from datetime import datetime
from PyQt6.QtWidgets import QMainWindow
from app.ui.menu_bar import AppMenuBar


def test_clock_label_updates(qtbot):
    win = QMainWindow()
    mb = AppMenuBar(win, now_provider=lambda: datetime(2026, 6, 20, 10, 30, 45))
    win.setMenuBar(mb)
    qtbot.addWidget(win)
    mb.tick()  # 手動更新
    assert mb.clock_label.text() == "2026/06/20 10:30:45"
