from __future__ import annotations

from scripts.mutation_report_diff import build_report


def test_mutation_report_includes_required_categories_and_prior_deltas() -> None:
    report = build_report(
        {"killed": 12, "survived": 2, "timeout": 1, "suspicious": 3, "no_tests": 4, "total": 22},
        {"killed": 10, "survived": 3, "timeout": 0, "suspicious": 1, "no_tests": 5, "total": 19},
    )

    assert report["counts"] == {
        "killed": 12,
        "survived": 2,
        "timeout": 1,
        "suspicious": 3,
        "no_tests": 4,
        "skipped": 0,
        "segfault": 0,
        "untested": 0,
        "total": 22,
    }
    assert report["deltas"] == {
        "killed": 2,
        "survived": -1,
        "timeout": 1,
        "suspicious": 2,
        "no_tests": -1,
        "skipped": 0,
        "segfault": 0,
        "untested": 0,
        "total": 3,
    }


def test_mutation_report_marks_missing_prior_run_without_inventing_deltas() -> None:
    report = build_report({"killed": 1, "total": 1}, None)
    assert report["previous_counts"] is None
    assert report["deltas"] is None


def test_mutation_report_derives_mutmuts_unexported_untested_count() -> None:
    report = build_report({"killed": 2, "survived": 1, "no_tests": 3, "total": 10}, None)
    assert report["counts"]["untested"] == 4
