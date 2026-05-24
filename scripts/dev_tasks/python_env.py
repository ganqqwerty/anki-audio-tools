"""Anki Python discovery helpers for development tasks."""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADDON_DIR = ROOT / "addon" / "anki_audio_quick_editor"
ADDON_SYMLINK_ID = "1000000002"


def _load_dotenv() -> dict[str, str]:
    env_file = ROOT / ".env"
    if not env_file.is_file():
        return {}
    result: dict[str, str] = {}
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        result[key] = value
    return result


def _candidate_paths() -> list[Path]:
    system = platform.system()
    if system == "Darwin":
        base = Path.home() / "Library" / "Application Support"
        return [base / "AnkiProgramFiles" / ".venv" / "bin" / "python3"]
    if system == "Linux":
        return [
            Path.home() / ".local" / "share" / "AnkiProgramFiles" / ".venv" / "bin" / "python3",
            Path.home() / ".var" / "app" / "net.ankiweb.Anki" / "data" / "AnkiProgramFiles" / ".venv" / "bin" / "python3",
        ]
    if system == "Windows":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            return [Path(appdata) / "AnkiProgramFiles" / ".venv" / "Scripts" / "python.exe"]
    return []


def _validate_python(python: Path) -> bool:
    if not python.is_file():
        return False
    try:
        result = subprocess.run([str(python), "-c", "import anki"], capture_output=True, timeout=15)
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _die(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def _find_anki_python() -> Path:
    dotenv = _load_dotenv()
    env_value = os.environ.get("ANKI_PYTHON") or dotenv.get("ANKI_PYTHON")
    if env_value:
        candidate = Path(env_value).expanduser()
        if _validate_python(candidate):
            return candidate
        _die(f"ANKI_PYTHON is set to {env_value!r} but is not usable.")
    for candidate in _candidate_paths():
        if _validate_python(candidate):
            return candidate
    _die("Could not find Anki's bundled Python. Launch Anki once or set ANKI_PYTHON in .env.")
    raise SystemExit(1)


def _anki_bin_dir(anki_python: Path) -> Path:
    return anki_python.parent


def _anki_addons_dir() -> Path | None:
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Anki2" / "addons21"
    if system == "Linux":
        return Path.home() / ".local" / "share" / "Anki2" / "addons21"
    return None


def _addon_symlink_path() -> Path | None:
    addons_dir = _anki_addons_dir()
    if addons_dir is None:
        return None
    return addons_dir / ADDON_SYMLINK_ID


def _resolved_addon_dir() -> Path:
    return ADDON_DIR.resolve()


def _symlink_target(link: Path) -> Path | None:
    if not link.is_symlink():
        return None
    return link.resolve(strict=False)


def _format_addon_link_status() -> str:
    link = _addon_symlink_path()
    if link is None:
        return f"unsupported on {platform.system()}"
    if not link.exists() and not link.is_symlink():
        return f"missing at {link}"
    if not link.is_symlink():
        return f"real filesystem entry at {link}"
    target = _symlink_target(link)
    return f"{link} -> {target}"


def _warn_if_addon_symlink_mismatch() -> None:
    link = _addon_symlink_path()
    if link is None or not link.is_symlink():
        return
    target = _symlink_target(link)
    current = _resolved_addon_dir()
    if target != current:
        print(
            "WARNING: live Anki add-on "
            f"{ADDON_SYMLINK_ID} points at {target}, not this worktree's add-on {current}."
        )
        print("         Run: python3 scripts/dev.py link-addon")


def _print_addon_symlink_info() -> None:
    print(f"Anki add-on:  {_format_addon_link_status()}")
    _warn_if_addon_symlink_mismatch()


def _setup_addon_symlink() -> None:
    addons_dir = _anki_addons_dir()
    if addons_dir and addons_dir.is_dir():
        link = addons_dir / ADDON_SYMLINK_ID
        if link.is_symlink():
            print(f"  Already exists: {link} -> {_symlink_target(link)}")
            _warn_if_addon_symlink_mismatch()
            return
        if link.exists():
            print(f"  Already exists: {link}")
            return
        link.symlink_to(ADDON_DIR)
        print(f"  Created: {link} -> {ADDON_DIR}")
    elif addons_dir:
        print(f"  Skipped: {addons_dir} does not exist (launch Anki once first)")
    else:
        print(f"  Skipped: symlink creation not supported on {platform.system()}")


def cmd_link_addon() -> int:
    link = _addon_symlink_path()
    if link is None:
        print(f"ERROR: add-on symlink creation is not supported on {platform.system()}", file=sys.stderr)
        return 1
    if not link.parent.is_dir():
        print(f"ERROR: {link.parent} does not exist. Launch Anki once first.", file=sys.stderr)
        return 1
    current = _resolved_addon_dir()
    if link.is_symlink():
        target = _symlink_target(link)
        if target == current:
            print(f"Already linked: {link} -> {current}")
            return 0
        link.unlink()
        link.symlink_to(ADDON_DIR)
        print(f"Repointed: {link} -> {current}")
        print(f"Previous target: {target}")
        return 0
    if link.exists():
        print(f"ERROR: refusing to overwrite non-symlink add-on path: {link}", file=sys.stderr)
        return 1
    link.symlink_to(ADDON_DIR)
    print(f"Created: {link} -> {current}")
    return 0
