"""Coverage and Sonar helpers for the development task runner."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from scripts.dev_tasks.process import _run
from scripts.dev_tasks.python_env import (
    _die,
    _find_anki_python,
    _load_dotenv,
    _print_addon_symlink_info,
)

ROOT = Path(__file__).resolve().parents[2]
SETTINGS_UI_DIR = ROOT / "settings_ui"
PYTHON_COVERAGE_FAIL_UNDER = 80
COVERAGE_XML = ROOT / "coverage.xml"
SETTINGS_UI_LCOV = SETTINGS_UI_DIR / "coverage" / "lcov.info"


def cmd_coverage() -> int:
    anki_python = _find_anki_python()
    return _run(
        [
            str(anki_python),
            "-m",
            "pytest",
            "tests/",
            "--cov",
            "--cov-branch",
            "--cov-report=term-missing",
            f"--cov-fail-under={PYTHON_COVERAGE_FAIL_UNDER}",
        ],
        label=f"python coverage (fail under {PYTHON_COVERAGE_FAIL_UNDER}%)",
        show_output_on_failure=True,
    )


def _prefix_settings_ui_lcov_paths() -> None:
    if not SETTINGS_UI_LCOV.is_file():
        return
    lines: list[str] = []
    for line in SETTINGS_UI_LCOV.read_text().splitlines(keepends=True):
        if line.startswith("SF:src/"):
            lines.append(f"SF:settings_ui/{line[3:]}")
        else:
            lines.append(line)
    SETTINGS_UI_LCOV.write_text("".join(lines))


def _remove_stale_report(path: Path) -> None:
    if path.is_file():
        path.unlink()


def _require_report(path: Path, label: str) -> int:
    if path.is_file():
        return 0
    print(f"ERROR: {label} report was not generated: {path}", file=sys.stderr)
    return 1


def cmd_sonar() -> int:
    scanner = shutil.which("sonar-scanner")
    if not scanner:
        _die("sonar-scanner not found. Install it first if you want local Sonar analysis.")
    dotenv = _load_dotenv()
    token = os.environ.get("SONAR_TOKEN") or dotenv.get("SONAR_TOKEN")
    if not token:
        _die("SONAR_TOKEN not set.")
    host_url = (
        os.environ.get("SONAR_HOST_URL")
        or dotenv.get("SONAR_HOST_URL")
        or "http://localhost:9000"
    )
    anki_python = _find_anki_python()
    _remove_stale_report(COVERAGE_XML)
    _remove_stale_report(SETTINGS_UI_LCOV)
    python_rc = _run(
        [
            str(anki_python),
            "-m",
            "pytest",
            "tests/",
            "--cov",
            "--cov-branch",
            "--cov-report=xml",
            f"--cov-fail-under={PYTHON_COVERAGE_FAIL_UNDER}",
        ],
        label=f"python coverage for sonar (fail under {PYTHON_COVERAGE_FAIL_UNDER}%)",
        show_output_on_failure=True,
    )
    if python_rc != 0:
        return python_rc
    report_rc = _require_report(COVERAGE_XML, "Python coverage XML")
    if report_rc != 0:
        return report_rc
    if not SETTINGS_UI_DIR.is_dir():
        print("ERROR: settings_ui/ not found; cannot generate frontend coverage for sonar.", file=sys.stderr)
        return 1
    if not (SETTINGS_UI_DIR / "node_modules").is_dir():
        print("ERROR: settings_ui/node_modules not found; run: python3 scripts/dev.py setup", file=sys.stderr)
        return 1
    ui_rc = _run(
        ["npm", "run", "test:coverage"],
        cwd=SETTINGS_UI_DIR,
        label="frontend UI coverage for sonar",
    )
    if ui_rc != 0:
        return ui_rc
    _prefix_settings_ui_lcov_paths()
    report_rc = _require_report(SETTINGS_UI_LCOV, "frontend LCOV")
    if report_rc != 0:
        return report_rc
    return _run(
        [scanner, f"-Dsonar.host.url={host_url}"],
        env={"SONAR_TOKEN": token},
        label="sonar-scanner analysis",
    )


def cmd_info() -> int:
    anki_python = _find_anki_python()
    print(f"Anki Python:  {anki_python}")
    result = subprocess.run([str(anki_python), "--version"], capture_output=True, text=True)
    print(f"Python:       {result.stdout.strip()}")
    node = shutil.which("node")
    if node:
        print(
            "Node.js:      "
            f"{subprocess.run([node, '--version'], capture_output=True, text=True).stdout.strip()}"
        )
    else:
        print("Node.js:      not found")
    npm = shutil.which("npm")
    if npm:
        print(
            "npm:          "
            f"{subprocess.run([npm, '--version'], capture_output=True, text=True).stdout.strip()}"
        )
    else:
        print("npm:          not found")
    print(f"Project root: {ROOT}")
    print(f"Add-on dir:   {ROOT / 'addon' / 'anki_audio_quick_editor'}")
    _print_addon_symlink_info()
    return 0
