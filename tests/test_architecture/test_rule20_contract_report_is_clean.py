"""Rule 20: the shared architecture report must be violation-free."""

from __future__ import annotations

from .inspection import build_architecture_report


def test_architecture_report_is_clean() -> None:
    report = build_architecture_report()
    violations = report["violations"]
    assert isinstance(violations, list)
    assert violations == []

