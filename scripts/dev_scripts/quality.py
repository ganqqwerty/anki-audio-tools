"""Quality, dependency, and security commands for scripts/dev.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from scripts.dev_tasks.process import run_capture, run_process
from scripts.dev_tasks.python_env import find_anki_python
from scripts.dev_tasks.quality import (
    format_locale_catalog_report,
    locale_catalog_violations,
    mutmut_fix_stats_prefix_mismatch,
    radon_complexity_violations,
    radon_maintainability_violations,
)

ROOT = Path(__file__).resolve().parents[2]
RADON_FAIL_MIN_RANK = "C"


def cmd_complexity(_command_args: list[str]) -> int:
    anki_python = find_anki_python()
    rc, output = run_capture(
        [
            str(anki_python),
            "-m",
            "radon",
            "cc",
            "addon/anki_audio_quick_editor/",
            "--min",
            RADON_FAIL_MIN_RANK,
            "--ignore",
            "vendor,bin,user_files",
            "--json",
        ],
        label=f"radon complexity (fail on {RADON_FAIL_MIN_RANK} or worse)",
    )
    if rc != 0:
        return rc
    try:
        report = json.loads(output or "{}")
    except json.JSONDecodeError as exc:
        print(f"ERROR: could not parse radon JSON output: {exc}", file=sys.stderr)
        return 1
    violations = radon_complexity_violations(report)
    if not violations:
        print(f"PASS: no functions or classes at radon rank {RADON_FAIL_MIN_RANK} or worse.")
        return 0
    print(f"FAIL: radon found {len(violations)} item(s) at rank {RADON_FAIL_MIN_RANK} or worse:")
    for violation in violations:
        print(f"  {violation}")
    return 1


def cmd_maintainability(_command_args: list[str]) -> int:
    anki_python = find_anki_python()
    rc, output = run_capture(
        [
            str(anki_python),
            "-m",
            "radon",
            "mi",
            "addon/anki_audio_quick_editor/",
            "--min",
            "C",
            "--max",
            "C",
            "--ignore",
            "vendor,bin,user_files",
            "--json",
        ],
        label="radon maintainability (fail on C rank)",
    )
    if rc != 0:
        return rc
    try:
        report = json.loads(output or "{}")
    except json.JSONDecodeError as exc:
        print(f"ERROR: could not parse radon maintainability JSON output: {exc}", file=sys.stderr)
        return 1
    violations = radon_maintainability_violations(report)
    if not violations:
        print("PASS: no files at radon maintainability rank C.")
        return 0
    print(f"FAIL: radon found {len(violations)} file(s) at maintainability rank C:")
    for violation in violations:
        print(f"  {violation}")
    return 1


def cmd_quality_metrics(command_args: list[str]) -> int:
    complexity_rc = cmd_complexity(command_args)
    if complexity_rc != 0:
        return complexity_rc
    return cmd_maintainability(command_args)


def cmd_i18n(_command_args: list[str]) -> int:
    violations = locale_catalog_violations()
    print(format_locale_catalog_report(violations))
    return 1 if violations else 0


def cmd_deadcode(_command_args: list[str]) -> int:
    anki_python = find_anki_python()
    paths = ["addon/anki_audio_quick_editor/"]
    whitelist = ROOT / "vulture_whitelist.py"
    if whitelist.is_file():
        paths.append(str(whitelist))
    return run_process(
        [
            str(anki_python),
            "-m",
            "vulture",
            *paths,
            "--exclude",
            "vendor,bin,user_files",
            "--min-confidence",
            "80",
        ],
        label="vulture deadcode",
    )


def cmd_security(_command_args: list[str]) -> int:
    anki_python = find_anki_python()
    return run_process(
        [
            str(anki_python),
            "-m",
            "bandit",
            "-r",
            "addon/anki_audio_quick_editor/",
            "--exclude",
            "addon/anki_audio_quick_editor/vendor,addon/anki_audio_quick_editor/bin,addon/anki_audio_quick_editor/user_files",
            "-c",
            "pyproject.toml",
            "-ll",
            "-ii",
        ],
        label="bandit security",
    )


def cmd_deps(_command_args: list[str]) -> int:
    anki_python = find_anki_python()
    return run_process([str(anki_python), "-m", "deptry", "."], label="deptry dependency check")


def cmd_muttest(command_args: list[str]) -> int:
    anki_python = find_anki_python()
    mutmut_args = command_args
    if not mutmut_args or mutmut_args[0].startswith("-"):
        mutmut_args = ["run", *mutmut_args]
    labels = {
        "run": "mutmut mutation testing",
        "results": "mutmut results",
        "show": "mutmut show mutant",
        "tests-for-mutant": "mutmut tests for mutant",
        "browse": "mutmut browse",
        "print-time-estimates": "mutmut time estimates",
        "export-cicd-stats": "mutmut CI/CD stats export",
        "apply": "mutmut apply mutant",
    }
    rc = run_process(
        [str(anki_python), "-m", "mutmut", *mutmut_args],
        label=labels.get(mutmut_args[0], f"mutmut {' '.join(mutmut_args)}"),
    )
    if rc != 0 or mutmut_args[0] != "run":
        return rc
    if not mutmut_fix_stats_prefix_mismatch():
        return rc
    print("[dev] detected mutmut stats/module prefix mismatch; rerunning with normalized stats.")
    return run_process(
        [str(anki_python), "-m", "mutmut", *mutmut_args],
        label="mutmut mutation testing (normalized stats rerun)",
    )
