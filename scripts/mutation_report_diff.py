"""Write a stable mutation-category report with deltas from a prior run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

CATEGORIES = (
    "killed",
    "survived",
    "timeout",
    "suspicious",
    "no_tests",
    "skipped",
    "segfault",
    "untested",
    "total",
)

MUTMUT_REPORTED_OUTCOMES = (
    "killed",
    "survived",
    "timeout",
    "suspicious",
    "no_tests",
    "skipped",
    "segfault",
    "check_was_interrupted_by_user",
)


def _counts(payload: dict[str, object]) -> dict[str, int]:
    counts = {category: int(payload.get(category, 0)) for category in CATEGORIES}
    if "untested" not in payload:
        reported = sum(int(payload.get(category, 0)) for category in MUTMUT_REPORTED_OUTCOMES)
        counts["untested"] = max(0, counts["total"] - reported)
    return counts


def build_report(current: dict[str, object], previous: dict[str, object] | None) -> dict[str, object]:
    counts = _counts(current)
    prior_counts = _counts(previous) if previous is not None else None
    deltas = (
        {category: counts[category] - prior_counts[category] for category in CATEGORIES}
        if prior_counts is not None
        else None
    )
    return {"counts": counts, "previous_counts": prior_counts, "deltas": deltas}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    current = json.loads(args.current.read_text(encoding="utf-8"))
    previous = None
    if args.previous is not None and args.previous.is_file():
        previous = json.loads(args.previous.read_text(encoding="utf-8"))
    report = build_report(current, previous)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
