"""External quality tool commands for the dev runner."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from scripts.dev_tasks.process import _run

ROOT = Path(__file__).resolve().parents[2]


def cmd_qodana() -> int:
    qodana = shutil.which("qodana")
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
