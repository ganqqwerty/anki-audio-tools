"""One-time repository setup command for the dev runner."""

from __future__ import annotations

import sys
from pathlib import Path

from scripts.dev_tasks.node_tools import find_npm_install_command
from scripts.dev_tasks.process import _run
from scripts.dev_tasks.python_env import _find_anki_python, _setup_addon_symlink

ROOT = Path(__file__).resolve().parents[2]
SETTINGS_UI_DIR = ROOT / "settings_ui"
DEV_DEPS = [
    "argcomplete",
    "pytest>=9.0.2",
    "pytest-cov",
    "pytest-qt",
    "ruff",
    "mypy",
    "radon",
    "mccabe",
    "pyflakes",
    "import-linter",
    "pydeps",
    "deptry",
    "vulture>=2.14",
    "bandit",
    "pytest-randomly",
    "mutmut",
    "jsonschema",
    "praat-parselmouth>=0.4.7",
]


def cmd_setup() -> int:
    anki_python = _find_anki_python()
    print(f"Anki Python: {anki_python}")
    pip_rc = _run([str(anki_python), "-m", "pip", "install", *DEV_DEPS], label="installing Python dev dependencies")
    if pip_rc == 0:
        print(f"  Installed: {', '.join(DEV_DEPS)}")
    _setup_addon_symlink()
    npm_rc = 0
    npm = find_npm_install_command()
    if SETTINGS_UI_DIR.is_dir():
        if npm:
            npm_cmd = [*npm, "ci", "--legacy-peer-deps"]
            if not (SETTINGS_UI_DIR / "package-lock.json").is_file():
                npm_cmd = [*npm, "install", "--legacy-peer-deps"]
            npm_rc = _run(npm_cmd, cwd=SETTINGS_UI_DIR, label="settings UI npm install")
        elif (SETTINGS_UI_DIR / "node_modules").is_dir():
            print("WARNING: npm not found; keeping existing settings_ui/node_modules for frontend commands.")
            print("         Install Node.js 18+ with npm to refresh frontend dependencies on this machine.")
        else:
            print("ERROR: npm not found and settings_ui/node_modules is missing.", file=sys.stderr)
            print("       Install Node.js 18+ with npm, then rerun: python3 scripts/dev.py setup", file=sys.stderr)
            npm_rc = 1
    if pip_rc != 0:
        return pip_rc
    return npm_rc
