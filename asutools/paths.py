from pathlib import Path

APP_NAME = "asuTools"
DATA_DIR = Path.home() / "Library" / "Application Support" / APP_NAME
_LEGACY_DIR = Path.home() / "Library" / "Application Support" / "asutools"
TOOLS_JSON = DATA_DIR / "tools.json"
CATEGORIES_JSON = DATA_DIR / "categories.json"
ENVIRONMENTS_JSON = DATA_DIR / "environments.json"
SETTINGS_JSON = DATA_DIR / "settings.json"


def ensure_data_dir() -> None:
    if _LEGACY_DIR.exists() and not DATA_DIR.exists():
        _LEGACY_DIR.rename(DATA_DIR)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
