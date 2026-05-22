"""One-time repository setup command for the dev runner."""

from __future__ import annotations

import shutil
from pathlib import Path

from scripts.dev_tasks.process import _run
from scripts.dev_tasks.python_env import _find_anki_python, _setup_addon_symlink

ROOT = Path(__file__).resolve().parents[2]
SETTINGS_UI_DIR = ROOT / "settings_ui"
DEV_DEPS = [
    "pytest>=9.0.2",
    "pytest-cov",
    "pytest-qt",
    "ruff",
    "mypy",
    "radon",
    "import-linter",
    "deptry",
    "vulture",
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
    if SETTINGS_UI_DIR.is_dir() and shutil.which("npm"):
        npm_cmd = ["npm", "ci", "--legacy-peer-deps"]
        if not (SETTINGS_UI_DIR / "package-lock.json").is_file():
            npm_cmd = ["npm", "install", "--legacy-peer-deps"]
        npm_rc = _run(npm_cmd, cwd=SETTINGS_UI_DIR, label="settings UI npm install")
    if pip_rc != 0:
        return pip_rc
    return npm_rc
