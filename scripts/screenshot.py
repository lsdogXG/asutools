"""Self-screenshot via Qt — no system permission needed."""
import sys
from pathlib import Path

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from asutools import paths
from asutools.ui.main_window import MainWindow


def main() -> int:
    paths.ensure_data_dir()
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()

    out = Path("/tmp/asutools-shots/v0.png")
    out.parent.mkdir(parents=True, exist_ok=True)

    def shoot():
        pixmap = win.grab()
        pixmap.save(str(out), "PNG")
        print(f"saved: {out}  ({pixmap.width()}x{pixmap.height()})")
        app.quit()

    QTimer.singleShot(800, shoot)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
