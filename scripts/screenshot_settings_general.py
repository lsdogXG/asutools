import sys
from pathlib import Path

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QTabWidget

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from asutools import paths, theme
from asutools.ui.dialogs import SettingsDialog


def main() -> int:
    paths.ensure_data_dir()
    app = QApplication(sys.argv)
    dlg = SettingsDialog(theme.DARK)
    dlg.resize(820, 560)

    for w in dlg.findChildren(QTabWidget):
        w.setCurrentIndex(1)

    dlg.show()
    out = Path("/tmp/asutools-shots/settings_general.png")
    out.parent.mkdir(parents=True, exist_ok=True)

    def shoot():
        pixmap = dlg.grab()
        pixmap.save(str(out), "PNG")
        print(f"saved: {out}  ({pixmap.width()}x{pixmap.height()})")
        app.quit()

    QTimer.singleShot(600, shoot)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
