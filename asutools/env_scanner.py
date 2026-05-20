import os
import re
import subprocess
from pathlib import Path

from .models import Environment

_PY_VERSION_RE = re.compile(r"Python (\d+\.\d+\.\d+)")
_JAVA_VERSION_RE = re.compile(r'version "([^"]+)"')


def _probe_python(path: Path) -> str:
    try:
        out = subprocess.run(
            [str(path), "--version"],
            capture_output=True, text=True, timeout=2,
        )
        text = (out.stdout or out.stderr).strip()
        m = _PY_VERSION_RE.search(text)
        return m.group(1) if m else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def _probe_java(home: Path) -> str:
    java_bin = home / "bin" / "java"
    if not java_bin.exists():
        return ""
    try:
        out = subprocess.run(
            [str(java_bin), "-version"],
            capture_output=True, text=True, timeout=2,
        )
        text = out.stderr or out.stdout
        m = _JAVA_VERSION_RE.search(text)
        return m.group(1) if m else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def _slug(*parts: str) -> str:
    s = "-".join(p for p in parts if p)
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", s).strip("-").lower()


def scan_python() -> list[Environment]:
    seen: set[Path] = set()
    out: list[Environment] = []

    candidates: list[Path] = []
    search_paths = [
        Path("/usr/bin"),
        Path("/usr/local/bin"),
        Path("/opt/homebrew/bin"),
        Path.home() / ".local" / "bin",
    ]
    for sp in search_paths:
        if not sp.is_dir():
            continue
        for entry in sp.iterdir():
            n = entry.name
            if n == "python3" or re.fullmatch(r"python3\.\d+", n):
                candidates.append(entry)

    for p in candidates:
        try:
            resolved = p.resolve()
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        version = _probe_python(p)
        if not version:
            continue
        tag = "system"
        if "/opt/homebrew/" in str(p) or "/usr/local/" in str(p):
            tag = "brew"
        elif ".local" in str(p):
            tag = "user"
        out.append(Environment(
            id=_slug("py", tag, version),
            name=f"Python {version} ({tag})",
            type="python",
            path=str(p),
            version=version,
            source="auto",
            tags=[tag],
        ))
    return out


def scan_venvs() -> list[Environment]:
    out: list[Environment] = []
    venv_roots = [
        Path.home() / ".venvs",
        Path.home() / "venvs",
        Path.home() / ".virtualenvs",
    ]
    for root in venv_roots:
        if not root.is_dir():
            continue
        for venv in root.iterdir():
            py = venv / "bin" / "python"
            if not py.exists():
                continue
            version = _probe_python(py)
            out.append(Environment(
                id=_slug("venv", venv.name),
                name=f"{venv.name} (venv)",
                type="venv",
                path=str(venv),
                version=version,
                source="auto",
                tags=["venv"],
            ))
    return out


def scan_conda() -> list[Environment]:
    out: list[Environment] = []
    conda_roots = [
        Path("/opt/homebrew/Caskroom/miniforge/base"),
        Path.home() / "miniforge3",
        Path.home() / "miniconda3",
        Path.home() / "anaconda3",
    ]
    for root in conda_roots:
        if not root.is_dir():
            continue
        base_py = root / "bin" / "python"
        if base_py.exists():
            v = _probe_python(base_py)
            out.append(Environment(
                id=_slug("conda", root.name, "base"),
                name=f"{root.name} base ({v})",
                type="conda",
                path=str(root),
                version=v,
                source="auto",
                tags=["conda", "base"],
            ))
        envs_dir = root / "envs"
        if envs_dir.is_dir():
            for env in envs_dir.iterdir():
                py = env / "bin" / "python"
                if not py.exists():
                    continue
                v = _probe_python(py)
                out.append(Environment(
                    id=_slug("conda", env.name),
                    name=f"{env.name} (conda)",
                    type="conda",
                    path=str(env),
                    version=v,
                    source="auto",
                    tags=["conda"],
                ))
    return out


def _has_javafx(home: Path) -> bool:
    """Detect JavaFX presence. Java 8 ships jfxrt.jar; Java 11+ ships javafx.* modules."""
    j8_paths = [
        home / "jre" / "lib" / "ext" / "jfxrt.jar",
        home / "lib" / "ext" / "jfxrt.jar",
        home / "jre" / "lib" / "jfxrt.jar",
    ]
    for p in j8_paths:
        if p.exists():
            return True
    for d in (home / "lib", home / "jmods"):
        if d.is_dir():
            for f in d.iterdir():
                if "javafx" in f.name.lower():
                    return True
    return False


def _make_java_env(home: Path, name_hint: str, extra_tags: list[str]) -> Environment | None:
    version = _probe_java(home)
    if not version:
        return None
    fx = _has_javafx(home)
    tags = list(extra_tags)
    if fx:
        tags.append("javafx")
    fx_label = "  +FX" if fx else ""
    return Environment(
        id=_slug("java", name_hint, version),
        name=f"{name_hint} ({version}){fx_label}",
        type="java",
        path=str(home),
        version=version,
        source="auto",
        tags=tags,
        javafx=fx,
    )


def _scan_bundled_jdks() -> list[Environment]:
    """Find JDKs bundled inside user projects (TH_Tools-style)."""
    out: list[Environment] = []
    seen: set[Path] = set()
    workspace = Path.home() / "Workspace"
    if not workspace.is_dir():
        return out
    patterns = [
        "*/Java_path/Java_*/Contents/Home",
        "**/Java_path/Java_*/Contents/Home",
        "*/tools/*/Java_path/Java_*/Contents/Home",
    ]
    for pat in patterns:
        for home in workspace.glob(pat):
            if not home.is_dir():
                continue
            try:
                resolved = home.resolve()
            except OSError:
                continue
            if resolved in seen:
                continue
            seen.add(resolved)
            # Name hint from path: e.g., TH_Tools/Java_path/Java_8_Mac → "Java_8_Mac (TH_Tools)"
            parts = home.parts
            try:
                project = parts[parts.index("Java_path") - 1]
                folder = parts[parts.index("Java_path") + 1]
                name_hint = f"{folder} ({project})"
            except (ValueError, IndexError):
                name_hint = home.parent.parent.name
            env = _make_java_env(home, name_hint, ["bundled"])
            if env:
                out.append(env)
    return out


def scan_java() -> list[Environment]:
    out: list[Environment] = []
    jvm_root = Path("/Library/Java/JavaVirtualMachines")
    if jvm_root.is_dir():
        for jdk in jvm_root.iterdir():
            home = jdk / "Contents" / "Home"
            if not home.is_dir():
                continue
            env = _make_java_env(home, jdk.name, ["jdk"])
            if env:
                out.append(env)
    brew_opt = Path("/opt/homebrew/opt")
    if brew_opt.is_dir():
        for d in brew_opt.iterdir():
            if not d.name.startswith("openjdk"):
                continue
            home = d / "libexec" / "openjdk.jdk" / "Contents" / "Home"
            if not home.is_dir():
                home = d
            env = _make_java_env(home, d.name, ["jdk", "brew"])
            if env:
                out.append(env)
    # JetBrains-installed JDKs
    jb_root = Path.home() / ".jdks"
    if jb_root.is_dir():
        for jdk in jb_root.iterdir():
            home = jdk
            if (jdk / "Contents" / "Home").is_dir():
                home = jdk / "Contents" / "Home"
            env = _make_java_env(home, jdk.name, ["jdk", "jetbrains"])
            if env:
                out.append(env)
    # Bundled JDKs inside ~/Workspace projects (TH_Tools etc.)
    out.extend(_scan_bundled_jdks())
    jhome = os.environ.get("JAVA_HOME")
    if jhome and Path(jhome).is_dir():
        env = _make_java_env(Path(jhome), "$JAVA_HOME", ["jdk", "env"])
        if env:
            out.append(env)
    return out


def scan_all() -> list[Environment]:
    found: dict[str, Environment] = {}
    for env in scan_python() + scan_venvs() + scan_conda() + scan_java():
        found.setdefault(env.id, env)
    return list(found.values())
