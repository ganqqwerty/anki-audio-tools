"""Architecture-report command for scripts/dev.py."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def cmd_architecture_report(command_args: list[str]) -> int:
    json_mode = "--json" in command_args
    root_str = str(ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    from tests.test_architecture.inspection import (
        build_architecture_report,
        format_architecture_report_json,
        format_architecture_report_text,
    )

    report = build_architecture_report()
    if json_mode:
        print(format_architecture_report_json())
    else:
        print(format_architecture_report_text())
    violations = report["violations"]
    assert isinstance(violations, list)
    return 1 if violations else 0
