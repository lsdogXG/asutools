"""扫描所有 java 工具的 jar，检测 manifest 主类是否引用 javafx 包；
检测到的就把 env_id 绑到第一个带 +FX 的 Java 环境。"""
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from asutools import store
from asutools.env_scanner import scan_java


FX_MARKER = b"javafx/"


def jar_uses_javafx(jar_path: str) -> bool:
    """A jar uses JavaFX if any class file references javafx/ in its constant pool
    OR the manifest mentions javafx OR a class file path starts with javafx/."""
    p = Path(jar_path)
    if not p.exists() or p.suffix != ".jar":
        return False
    try:
        with zipfile.ZipFile(p, "r") as z:
            names = z.namelist()
            for n in names:
                low = n.lower()
                if low.startswith("javafx/") or "/javafx/" in low:
                    return True
                if n.upper().endswith("MANIFEST.MF"):
                    try:
                        if b"javafx" in z.read(n).lower():
                            return True
                    except Exception:
                        pass
            # Scan all .class files (constant pool) for the byte sequence "javafx/"
            for n in names:
                if not n.endswith(".class"):
                    continue
                try:
                    data = z.read(n)
                except Exception:
                    continue
                if FX_MARKER in data:
                    return True
    except (zipfile.BadZipFile, OSError):
        return False
    return False


def main() -> None:
    java_envs = scan_java()
    fx_env = next((e for e in java_envs if e.javafx), None)
    if not fx_env:
        print("没有找到带 JavaFX 的 Java 环境。先在设置→环境里加一个（Java 8 或 Liberica Full）。")
        return
    print(f"将把命中 FX 的工具绑到: {fx_env.name}\n")

    tools = store.load_tools()
    changed = 0
    for tool in tools:
        if tool.get("type") != "java":
            continue
        path = tool.get("path", "")
        if jar_uses_javafx(path):
            old = tool.get("env_id")
            tool["env_id"] = fx_env.id
            changed += 1
            mark = "(更新)" if old and old != fx_env.id else "(新设)"
            print(f"  {mark}  {tool.get('name', ''):30}  ← {Path(path).name}")
    store.save_tools(tools)
    print(f"\n共 {changed} 个工具已绑到 {fx_env.name}")


if __name__ == "__main__":
    main()
