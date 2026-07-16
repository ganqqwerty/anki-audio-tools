"""Frontend build and validation commands for the dev runner."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from scripts.dev_tasks.contracts import cmd_contracts_generate
from scripts.dev_tasks.node_tools import frontend_npm_command
from scripts.dev_tasks.process import _run
from scripts.dev_tasks.python_env import _die, _warn_if_addon_symlink_mismatch

ROOT = Path(__file__).resolve().parents[2]
SETTINGS_UI_DIR = ROOT / "settings_ui"


def _frontend_validation_env() -> dict[str, str] | None:
    if os.environ.get("AQE_E2E_FFMPEG"):
        return None
    ffmpeg = shutil.which("ffmpeg")
    return {"AQE_E2E_FFMPEG": ffmpeg} if ffmpeg else None


def cmd_build_ui() -> int:
    if not SETTINGS_UI_DIR.is_dir():
        _die("settings_ui/ directory not found.")
    npm = frontend_npm_command("build", settings_ui_dir=SETTINGS_UI_DIR)
    if not npm:
        _die("npm or a supported frontend script runner not found. Install Node.js 18+.")
    contracts_rc = cmd_contracts_generate()
    if contracts_rc != 0:
        return contracts_rc
    rc = _run(npm, cwd=SETTINGS_UI_DIR, label="frontend webview bundle build")
    if rc == 0:
        _warn_if_addon_symlink_mismatch()
    return rc


def cmd_build() -> int:
    return cmd_build_ui()


def cmd_test_svelte() -> int:
    if not SETTINGS_UI_DIR.is_dir():
        print("ERROR: settings_ui/ not found; cannot validate frontend.", file=sys.stderr)
        return 1
    npm = frontend_npm_command("validate", settings_ui_dir=SETTINGS_UI_DIR)
    if not npm:
        print("ERROR: npm or a supported frontend script runner not found. Install Node.js 18+.", file=sys.stderr)
        return 1
    if not (SETTINGS_UI_DIR / "node_modules").is_dir():
        print("ERROR: settings_ui/node_modules not found. Run: python3 scripts/dev.py setup", file=sys.stderr)
        return 1
    build_rc = cmd_build_ui()
    if build_rc != 0:
        return build_rc
    lint_fix = frontend_npm_command("lint", extra_args=("--fix",), settings_ui_dir=SETTINGS_UI_DIR)
    assert lint_fix is not None
    lint_fix_rc = _run(lint_fix, cwd=SETTINGS_UI_DIR, label="frontend UI lint autofix")
    if lint_fix_rc != 0:
        return lint_fix_rc
    return _run(
        npm,
        env=_frontend_validation_env(),
        cwd=SETTINGS_UI_DIR,
        label="frontend UI validation",
    )
