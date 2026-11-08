from __future__ import annotations
import os
import sys

# --windowed (console=False) では sys.stdout/stderr が None になり、
# ライブラリの進捗バー等が None.write でクラッシュするため Null に差し替える。
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

from pathlib import Path

# TimesFM モデルの保存先を EXE（開発時はプロジェクトルート）と同じ場所の
# models フォルダに固定する。配布 ZIP 同梱の models フォルダへ保存・読込される。
# 既に HF_HOME が設定済みなら、それを優先する（setdefault）。
if getattr(sys, "frozen", False):
    _base_dir = Path(sys.executable).parent
else:
    _base_dir = Path(__file__).resolve().parent.parent
os.environ.setdefault("HF_HOME", str(_base_dir / "models"))

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication
from app.logger import setup_logging
from app.ui.main_window import MainWindow


def main() -> int:
    setup_logging(Path.home() / ".modbus-timesfm-viewer" / "logs")
    if sys.platform == "win32":
        # 独自の ID を付けないと、タスクバーに python のアイコンが出ることがある
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Nagasaki-Software.modbus-timesfm-viewer")
    app = QApplication(sys.argv)
    # EXE では同梱物の展開先（_MEIPASS）に app/assets が入る
    assets = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent)) / "app" / "assets"
    app.setWindowIcon(QIcon(str(assets / "icon.ico")))
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
