"""External quality tool commands for the dev runner."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from scripts.dev_tasks.process import _run

ROOT = Path(__file__).resolve().parents[2]


def _find_qodana() -> str | None:
    qodana = shutil.which("qodana")
    if qodana:
        return qodana
    if os.name == "nt":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            candidates = sorted(
                Path(local_app_data)
                .joinpath("Microsoft", "WinGet", "Packages")
                .glob("JetBrains.QodanaCLI_*\\qodana.exe"),
                reverse=True,
            )
            for candidate in candidates:
                if candidate.is_file():
                    return str(candidate)
    return None


def cmd_qodana() -> int:
    qodana = _find_qodana()
    if not qodana:
        print("ERROR: qodana not found. Install the Qodana CLI and ensure it is on PATH.", file=sys.stderr)
        return 1
    return _run(
        [
            qodana,
            "--disable-update-checks",
            "scan",
            "--config",
            "qodana.yaml",
            "--project-dir",
            str(ROOT),
            "--print-problems",
        ],
        label="qodana code quality",
    )
