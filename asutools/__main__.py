import sys
from pathlib import Path


def _fix_mac_bundle_identity_pre() -> None:
    """Pre-QApplication identity fix: NSBundle dict + setproctitle + NSProcessInfo.

    Must run BEFORE QApplication instantiates NSApplication.
    """
    if sys.platform != "darwin":
        return

    try:
        import setproctitle
        setproctitle.setproctitle("asuTools")
    except ImportError:
        pass

    try:
        from Foundation import NSProcessInfo, NSBundle  # type: ignore
        NSProcessInfo.processInfo().setProcessName_("asuTools")
        bundle = NSBundle.mainBundle()
        info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
        if info is not None:
            info["CFBundleName"] = "asuTools"
            info["CFBundleDisplayName"] = "asuTools"
            info["CFBundleIdentifier"] = "com.asu.asutools"
            info["CFBundleExecutable"] = "asuTools"
    except Exception:
        pass


def _fix_mac_dock_icon(icon_path: Path) -> None:
    """Post-QApplication: set the Dock icon image via AppKit at runtime.

    NSBundle/LSASN tricks don't reliably set the icon when the binary lives
    outside a .app bundle. This API does, since it operates on the live NSApp.
    """
    if sys.platform != "darwin" or not icon_path.exists():
        return
    try:
        from AppKit import NSImage, NSApplication  # type: ignore
        img = NSImage.alloc().initWithContentsOfFile_(str(icon_path))
        if img is not None:
            NSApplication.sharedApplication().setApplicationIconImage_(img)
    except Exception:
        pass


_fix_mac_bundle_identity_pre()

from PyQt6.QtCore import QCoreApplication  # noqa: E402
from PyQt6.QtGui import QIcon  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

from . import paths  # noqa: E402
from .ui.main_window import MainWindow  # noqa: E402


def main() -> int:
    paths.ensure_data_dir()

    sys.argv[0] = "asuTools"
    QCoreApplication.setApplicationName("asuTools")
    QCoreApplication.setOrganizationName("asu")
    QCoreApplication.setOrganizationDomain("asu.local")

    app = QApplication(sys.argv)
    app.setApplicationName("asuTools")
    app.setApplicationDisplayName("asuTools")

    icon_path = Path(__file__).resolve().parent / "resources" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    _fix_mac_dock_icon(icon_path)

    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
