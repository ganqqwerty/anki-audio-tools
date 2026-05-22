"""Frontend build and validation commands for the dev runner."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from scripts.dev_tasks.contracts import cmd_contracts_generate
from scripts.dev_tasks.process import _run
from scripts.dev_tasks.python_env import _die

ROOT = Path(__file__).resolve().parents[2]
SETTINGS_UI_DIR = ROOT / "settings_ui"


def cmd_build_ui() -> int:
    if not SETTINGS_UI_DIR.is_dir():
        _die("settings_ui/ directory not found.")
    if not shutil.which("npm"):
        _die("npm not found. Install Node.js 18+.")
    contracts_rc = cmd_contracts_generate()
    if contracts_rc != 0:
        return contracts_rc
    return _run(["npm", "run", "build"], cwd=SETTINGS_UI_DIR, label="frontend webview bundle build")


def cmd_build() -> int:
    return cmd_build_ui()


def cmd_test_svelte() -> int:
    if not SETTINGS_UI_DIR.is_dir():
        print("ERROR: settings_ui/ not found; cannot validate frontend.", file=sys.stderr)
        return 1
    if not shutil.which("npm"):
        print("ERROR: npm not found. Install Node.js 18+.", file=sys.stderr)
        return 1
    if not (SETTINGS_UI_DIR / "node_modules").is_dir():
        print("ERROR: settings_ui/node_modules not found. Run: python3 scripts/dev.py setup", file=sys.stderr)
        return 1
    build_rc = cmd_build_ui()
    if build_rc != 0:
        return build_rc
    lint_fix_rc = _run(["npm", "run", "lint", "--", "--fix"], cwd=SETTINGS_UI_DIR, label="frontend UI lint autofix")
    if lint_fix_rc != 0:
        return lint_fix_rc
    return _run(["npm", "run", "validate"], cwd=SETTINGS_UI_DIR, label="frontend UI validation")
