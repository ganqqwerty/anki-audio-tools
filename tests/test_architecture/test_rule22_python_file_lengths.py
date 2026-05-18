"""Rule 22: hand-maintained Python files stay below the hard line limit."""

from __future__ import annotations

from pathlib import Path

from scripts.dev_tasks.file_lines import (
    ERROR_LIMIT,
    format_python_file_length_report,
    scan_python_file_lengths,
)


def test_hand_maintained_python_files_stay_under_hard_limit() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    report = scan_python_file_lengths(repo_root)

    assert not report.errors, (
        f"Hand-maintained Python files must stay under {ERROR_LIMIT} lines.\n"
        f"{format_python_file_length_report(report)}"
    )
