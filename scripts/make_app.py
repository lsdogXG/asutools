"""Build asuTools.app — a lightweight Mac .app launcher that calls into the uv project.

Installs to ~/Applications/asuTools.app so Spotlight (Cmd+Space) finds it.
The launcher script invokes `uv run python -m asutools` against the source at
PROJECT_DIR. This is NOT a self-contained bundle — it depends on the source tree
staying in place. For a fully redistributable bundle, see scripts/make_dmg.py
which can wrap py2app output (separate step).
"""
import os
import shutil
import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
APP_NAME = "asuTools"
BUNDLE_ID = "com.asu.asutools"
VERSION = "0.1.0"

INSTALL_DIR = Path.home() / "Applications"
APP_PATH = INSTALL_DIR / f"{APP_NAME}.app"

INFO_PLIST = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>{APP_NAME}</string>
    <key>CFBundleDisplayName</key>
    <string>{APP_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>{BUNDLE_ID}</string>
    <key>CFBundleVersion</key>
    <string>{VERSION}</string>
    <key>CFBundleShortVersionString</key>
    <string>{VERSION}</string>
    <key>CFBundleExecutable</key>
    <string>asuTools</string>
    <key>CFBundleIconFile</key>
    <string>icon.icns</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>11.0</string>
    <key>LSUIElement</key>
    <false/>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
    <key>NSAppleScriptEnabled</key>
    <false/>
</dict>
</plist>
"""

LAUNCHER = f"""#!/bin/bash
# asuTools launcher — invokes the project .venv's python directly.
PROJECT="{PROJECT_DIR}"
VENV_PY="$PROJECT/.venv/bin/python3"

if [ ! -x "$VENV_PY" ]; then
    export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$PATH"
    if command -v uv >/dev/null 2>&1; then
        (cd "$PROJECT" && uv sync --no-dev >/dev/null 2>&1)
    fi
    if [ ! -x "$VENV_PY" ]; then
        osascript -e 'display alert "asuTools" message "未找到 .venv，请先在源码目录跑 uv sync"'
        exit 1
    fi
fi

LOG="$HOME/Library/Logs/asuTools.log"
mkdir -p "$(dirname "$LOG")"
cd "$PROJECT" || exit 1
exec -a "asuTools" "$VENV_PY" -m asutools >>"$LOG" 2>&1
"""


def build_app(dest: Path) -> Path:
    """Build the .app bundle at <dest>."""
    if dest.exists():
        shutil.rmtree(dest)
    contents = dest / "Contents"
    macos = contents / "MacOS"
    resources = contents / "Resources"
    macos.mkdir(parents=True)
    resources.mkdir(parents=True)

    (contents / "Info.plist").write_text(INFO_PLIST, encoding="utf-8")

    launcher = macos / "asuTools"
    launcher.write_text(LAUNCHER, encoding="utf-8")
    launcher.chmod(0o755)

    icon_src = PROJECT_DIR / "asutools" / "resources" / "icon.icns"
    if icon_src.exists():
        shutil.copy(icon_src, resources / "icon.icns")
    else:
        print(f"warning: {icon_src} missing — run make_icon.py first")
    return dest


def refresh_launch_services(app: Path) -> None:
    """Force Spotlight + LaunchServices + Dock to refresh icon + name."""
    lsr = (
        "/System/Library/Frameworks/CoreServices.framework/Frameworks/"
        "LaunchServices.framework/Support/lsregister"
    )
    subprocess.run(["touch", str(app)], check=False)
    # Unregister then re-register to clear stale cache entries (icon / name).
    subprocess.run([lsr, "-u", str(app)], check=False, capture_output=True)
    subprocess.run([lsr, "-f", str(app)], check=False, capture_output=True)
    subprocess.run(["mdimport", str(app)], check=False, capture_output=True)
    # Kill Dock so it reloads icon + label from the freshly registered bundle.
    subprocess.run(["killall", "Dock"], check=False, capture_output=True)


def main() -> None:
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    build_app(APP_PATH)
    refresh_launch_services(APP_PATH)
    print(f"installed: {APP_PATH}")
    print("Spotlight: 试试 Cmd+Space 输入 'asu' 或 'asuTools'")


if __name__ == "__main__":
    main()
