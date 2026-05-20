"""First-run bootstrap: migrate TH_Tools data + scan environments."""
import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from asutools import paths, store
from asutools.env_scanner import scan_all

TH_ROOT = Path.home() / "Workspace" / "security" / "tools" / "TH_Tools"
TH_TOOLS = TH_ROOT / "config" / "tools.json"
TH_CATS = TH_ROOT / "config" / "categories.json"

TYPE_MAP = {
    "JAVA8": "java",
    "JAVA11": "java",
    "Python": "python",
    "GUI应用": "gui",
    "Shell脚本": "shell",
    "命令行": "shell",
    "网页": "url",
}


def migrate_categories() -> list[dict]:
    if not TH_CATS.exists():
        return []
    raw = json.loads(TH_CATS.read_text(encoding="utf-8"))
    out = []
    for i, c in enumerate(raw if isinstance(raw, list) else raw.get("categories", [])):
        name = c if isinstance(c, str) else c.get("name", "")
        if not name:
            continue
        out.append({"id": name, "name": name, "order": i})
    return out


def migrate_tools() -> list[dict]:
    if not TH_TOOLS.exists():
        return []
    raw = json.loads(TH_TOOLS.read_text(encoding="utf-8"))
    tools_list = raw if isinstance(raw, list) else raw.get("tools", [])
    out = []
    for t in tools_list:
        path = t.get("path", "")
        if path.startswith("/tools/"):
            path = str(TH_ROOT / path.lstrip("/"))
        out.append({
            "id": str(uuid.uuid4())[:8],
            "name": t.get("name", ""),
            "type": TYPE_MAP.get(t.get("type", ""), "shell"),
            "path": path,
            "category": t.get("category", ""),
            "env_id": None,
            "args": t.get("params", ""),
            "tags": t.get("tags", []) or [],
            "description": t.get("group", ""),
        })
    return out


def main() -> None:
    paths.ensure_data_dir()

    cats = migrate_categories()
    if cats:
        store.save_categories(cats)
        print(f"  categories: {len(cats)}")

    tools = migrate_tools()
    if tools:
        store.save_tools(tools)
        print(f"  tools: {len(tools)}")

    envs = scan_all()
    py_default = next((e.id for e in envs if e.type == "python" and "brew" in e.tags), None)
    if not py_default:
        py_default = next((e.id for e in envs if e.type == "python"), None)
    java_default = next((e.id for e in envs if e.type == "java"), None)
    store.save_environments({
        "environments": [e.to_dict() for e in envs],
        "defaults": {
            "python": py_default or "",
            "java": java_default or "",
        },
    })
    print(f"  environments: {len(envs)}")
    for e in envs:
        print(f"    [{e.type:6}] {e.id:32}  {e.path}")
    print(f"\nDefaults: python={py_default}  java={java_default}")
    print(f"\nData dir: {paths.DATA_DIR}")


if __name__ == "__main__":
    main()
