"""Repository structure checks for the dev runner."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def cmd_file_lines() -> int:
    root_str = str(ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    from scripts.dev_tasks.file_lines import (
        format_python_file_length_report,
        scan_python_file_lengths,
    )

    report = scan_python_file_lengths(ROOT)
    print(format_python_file_length_report(report))
    return report.exit_code
