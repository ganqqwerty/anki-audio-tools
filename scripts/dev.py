#!/usr/bin/env python3
"""Cross-platform task runner for Anki Audio Quick Editor development."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# isort: off
from scripts import dev_check as _dev_check
from scripts.dev_cli import print_help, split_cli_args
from scripts.dev_tasks.contracts import cmd_config_schema, cmd_contracts_check, cmd_contracts_generate
from scripts.dev_tasks.coverage import PYTHON_COVERAGE_FAIL_UNDER, cmd_coverage, cmd_info, cmd_sonar
from scripts.dev_tasks.e2e_parallel import cmd_test_e2e_parallel as _cmd_test_e2e_parallel
from scripts.dev_tasks.frontend import cmd_build, cmd_build_ui, cmd_test_svelte
from scripts.dev_tasks.process import _run, _run_capture, set_verbose
from scripts.dev_tasks.pytest_runner import _run_pytest
from scripts.dev_tasks.python_env import _anki_bin_dir, _die, _find_anki_python, cmd_link_addon
from scripts.dev_tasks.quality import format_locale_catalog_report, locale_catalog_violations, _mutmut_fix_stats_prefix_mismatch, _radon_complexity_violations, _radon_maintainability_violations
from scripts.dev_tasks.quality_tools import cmd_qodana
from scripts.dev_tasks.repository import cmd_file_lines
from scripts.dev_tasks.setup import cmd_setup
# isort: on

ADDON_DIR = ROOT / "addon" / "anki_audio_quick_editor"
RADON_FAIL_MIN_RANK = "C"
_COMMAND_ARGS: list[str] = []

_check_post_preflight_groups = _dev_check._check_post_preflight_groups
_check_worker_count = _dev_check._check_worker_count
_run_check_steps_parallel = _dev_check._run_check_steps_parallel
_run_check_steps_sequential = _dev_check._run_check_steps_sequential

def _run_test_targets() -> int:
    targets = _COMMAND_ARGS or ["tests/"]
    for target in targets:
        label = f"python tests: {target}" if _COMMAND_ARGS else "python tests"
        rc = _run_pytest(target, label=label)
        if rc != 0:
            return rc
    return 0


def cmd_test() -> int:
    contracts_rc = cmd_contracts_generate()
    if contracts_rc != 0:
        return contracts_rc
    return _run_test_targets()


def cmd_test_anki_api() -> int:
    return _run_pytest("anki_api_contract/", label="Anki API compatibility tests")

def cmd_test_e2e() -> int:
    build_rc = cmd_build_ui()
    if build_rc != 0:
        return build_rc
    targets = _COMMAND_ARGS or ["e2e/"]
    for target in targets:
        label = f"python e2e tests: {target}" if _COMMAND_ARGS else "python e2e tests"
        rc = _run_pytest(target, label=label)
        if rc != 0:
            return rc
    return 0


def cmd_test_e2e_parallel() -> int:
    build_rc = cmd_build_ui()
    if build_rc != 0:
        return build_rc
    return _cmd_test_e2e_parallel(_COMMAND_ARGS)


def cmd_lint() -> int:
    anki_python = _find_anki_python()
    fix_rc = _run([str(anki_python), "-m", "ruff", "check", "--fix"], label="ruff lint autofix")
    if fix_rc != 0:
        return fix_rc
    return _run([str(anki_python), "-m", "ruff", "check"], label="ruff lint")


def cmd_typecheck() -> int:
    contracts_rc = cmd_contracts_generate()
    if contracts_rc != 0:
        return contracts_rc
    return _run_typecheck()


def _run_typecheck() -> int:
    anki_python = _find_anki_python()
    return _run([str(anki_python), "-m", "mypy"], label="mypy typecheck")

def cmd_arch() -> int:
    anki_python = _find_anki_python()
    lint_imports = _anki_bin_dir(anki_python) / "lint-imports"
    if not lint_imports.is_file():
        _die(f"lint-imports not found at {lint_imports}. Run: python3 scripts/dev.py setup")
    return _run([str(lint_imports)], env={"PYTHONPATH": "addon"}, label="import-linter architecture check")


def cmd_architecture_report() -> int:
    json_mode = "--json" in _COMMAND_ARGS
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


def cmd_complexity() -> int:
    anki_python = _find_anki_python()
    rc, output = _run_capture(
        [
            str(anki_python), "-m", "radon", "cc",
            "addon/anki_audio_quick_editor/",
            "--min", RADON_FAIL_MIN_RANK,
            "--ignore", "vendor,bin",
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
    violations = _radon_complexity_violations(report)
    if not violations:
        print(f"PASS: no functions or classes at radon rank {RADON_FAIL_MIN_RANK} or worse.")
        return 0
    print(f"FAIL: radon found {len(violations)} item(s) at rank {RADON_FAIL_MIN_RANK} or worse:")
    for violation in violations:
        print(f"  {violation}")
    return 1


def cmd_maintainability() -> int:
    anki_python = _find_anki_python()
    rc, output = _run_capture(
        [
            str(anki_python), "-m", "radon", "mi",
            "addon/anki_audio_quick_editor/",
            "--min", "C",
            "--max", "C",
            "--ignore", "vendor,bin",
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
    violations = _radon_maintainability_violations(report)
    if not violations:
        print("PASS: no files at radon maintainability rank C.")
        return 0
    print(f"FAIL: radon found {len(violations)} file(s) at maintainability rank C:")
    for violation in violations:
        print(f"  {violation}")
    return 1


def cmd_quality_metrics() -> int:
    complexity_rc = cmd_complexity()
    if complexity_rc != 0:
        return complexity_rc
    return cmd_maintainability()


def cmd_i18n() -> int:
    violations = locale_catalog_violations()
    print(format_locale_catalog_report(violations))
    return 1 if violations else 0


def cmd_deadcode() -> int:
    anki_python = _find_anki_python()
    paths = ["addon/anki_audio_quick_editor/"]
    whitelist = ROOT / "vulture_whitelist.py"
    if whitelist.is_file():
        paths.append(str(whitelist))
    return _run(
        [
            str(anki_python), "-m", "vulture",
            *paths,
            "--exclude", "vendor,bin",
            "--min-confidence", "80",
        ],
        label="vulture deadcode",
    )


def cmd_security() -> int:
    anki_python = _find_anki_python()
    return _run(
        [
            str(anki_python), "-m", "bandit",
            "-r", "addon/anki_audio_quick_editor/",
            "--exclude", "addon/anki_audio_quick_editor/vendor,addon/anki_audio_quick_editor/bin",
            "-c", "pyproject.toml",
            "-ll",
            "-ii",
        ],
        label="bandit security",
    )


def cmd_deps() -> int:
    anki_python = _find_anki_python()
    return _run([str(anki_python), "-m", "deptry", "."], label="deptry dependency check")


def cmd_muttest() -> int:
    anki_python = _find_anki_python()
    mutmut_args = _COMMAND_ARGS
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
    rc = _run(
        [str(anki_python), "-m", "mutmut", *mutmut_args],
        label=labels.get(mutmut_args[0], f"mutmut {' '.join(mutmut_args)}"),
    )
    if rc != 0 or mutmut_args[0] != "run":
        return rc
    if not _mutmut_fix_stats_prefix_mismatch():
        return rc
    print("[dev] detected mutmut stats/module prefix mismatch; rerunning with normalized stats.")
    return _run(
        [str(anki_python), "-m", "mutmut", *mutmut_args],
        label="mutmut mutation testing (normalized stats rerun)",
    )


def cmd_check() -> int:
    preflight_steps = [
        ("config-schema", cmd_config_schema),
        ("contracts-generate", cmd_contracts_generate),
        ("contracts-check", cmd_contracts_check),
        ("build-ui", cmd_build_ui),
        ("lint", cmd_lint),
        ("i18n", cmd_i18n),
    ]
    failed = _run_check_steps_sequential(preflight_steps)
    failed_preflight = set(failed)
    contracts_prepared = "contracts-generate" not in failed_preflight and "contracts-check" not in failed_preflight
    phases = _check_post_preflight_groups(
        contracts_prepared=contracts_prepared,
        cmd_architecture_report=cmd_architecture_report,
        cmd_file_lines=cmd_file_lines,
        run_typecheck=_run_typecheck,
        cmd_security=cmd_security,
        cmd_deadcode=cmd_deadcode,
        cmd_deps=cmd_deps,
        cmd_quality_metrics=cmd_quality_metrics,
        cmd_qodana=cmd_qodana,
        cmd_arch=cmd_arch,
        cmd_test_anki_api=cmd_test_anki_api,
        run_test_targets=_run_test_targets,
        cmd_coverage=cmd_coverage,
        cmd_typecheck=cmd_typecheck,
        cmd_test=cmd_test,
        cmd_test_svelte=cmd_test_svelte,
    )
    for phase_name, phase_steps in phases:
        runner = _run_check_steps_parallel if phase_name == "parallel" else _run_check_steps_sequential
        failed.extend(runner(phase_steps))
    ordered_failed = [name for name, _func in [*preflight_steps, *(step for _phase_name, steps in phases for step in steps)] if name in set(failed)]
    print(
        f"[dev] {len(ordered_failed)} check step(s) failed: {', '.join(ordered_failed)}"
        if ordered_failed
        else "[dev] all check steps passed"
    )
    return 1 if ordered_failed else 0


def cmd_release() -> int:
    return _run([sys.executable, "scripts/release.py"], label="release build")


def cmd_release_assets() -> int:
    args = _COMMAND_ARGS
    if not args:
        print("Usage: python3 scripts/dev.py release-assets <subcommand> [args...]", file=sys.stderr)
        return 1
    return _run([sys.executable, "scripts/release_assets.py", *args], label="release asset preparation")


def cmd_release_smoke() -> int:
    args = _COMMAND_ARGS
    if len(args) != 1:
        print("Usage: python3 scripts/dev.py release-smoke <archive.ankiaddon>", file=sys.stderr)
        return 1
    return _run([sys.executable, "scripts/release_smoke.py", args[0]], label="release archive smoke test")


COMMANDS: dict[str, tuple[Callable[[], int], str]] = {
    "setup": (cmd_setup, "One-time setup: install dev deps, create symlink, npm install"),
    "link-addon": (cmd_link_addon, "Point Anki's local numeric add-on symlink at this worktree"),
    "architecture-report": (cmd_architecture_report, "Inspect executable architecture contracts and report violations"),
    "test": (cmd_test, "Run unit + architecture tests"),
    "test-e2e": (cmd_test_e2e, "Build frontend bundles, then run e2e tests (requires Anki runtime)"),
    "test-e2e-parallel": (
        cmd_test_e2e_parallel,
        "Build frontend bundles, then run e2e tests in isolated local shards",
    ),
    "lint": (cmd_lint, "Run ruff safe autofix, then ruff linter"),
    "typecheck": (cmd_typecheck, "Run mypy type checker"),
    "arch": (cmd_arch, "Run import-linter architecture contracts"),
    "test-anki-api": (cmd_test_anki_api, "Run real Anki API compatibility tests"),
    "complexity": (cmd_quality_metrics, "Run radon complexity and maintainability checks"),
    "i18n": (cmd_i18n, "Check that locale catalogs exactly match en.json keys"),
    "deadcode": (cmd_deadcode, "Find dead code (vulture)"),
    "security": (cmd_security, "Run bandit security linter"),
    "deps": (cmd_deps, "Check dependencies (deptry)"),
    "qodana": (cmd_qodana, "Run Qodana code quality analysis"),
    "check": (cmd_check, "Full QC: config-schema + contracts-generate + contracts-check + architecture-report + lint + typecheck + i18n + file-lines + security + deadcode + deps + complexity + qodana + arch + test-anki-api + test + coverage + frontend validate"),
    "coverage": (cmd_coverage, f"Run tests with branch coverage report (fail under {PYTHON_COVERAGE_FAIL_UNDER}%)"),
    "sonar": (cmd_sonar, "Optional SonarQube analysis (needs SONAR_TOKEN)"),
    "muttest": (cmd_muttest, "Mutation testing (advisory, opt-in)"),
    "build": (cmd_build, "Build the settings and editor Svelte bundles"),
    "build-ui": (cmd_build_ui, "Build the settings and editor Svelte bundles"),
    "test-svelte": (cmd_test_svelte, "Build frontend bundles, run ESLint autofix, then validate: svelte-check + ESLint + tsc + Vitest coverage"),
    "config-schema": (cmd_config_schema, "Validate config.json against JSON Schema"),
    "contracts-generate": (cmd_contracts_generate, "Generate Python and TypeScript JSON contracts"),
    "contracts-check": (cmd_contracts_check, "Verify generated JSON contracts are current"),
    "file-lines": (cmd_file_lines, "Check hand-maintained Python files against line-count limits"),
    "release": (cmd_release, "Run scripts/release.py"),
    "release-assets": (cmd_release_assets, "Fetch, build, verify, and stage locked release runtime assets"),
    "release-smoke": (cmd_release_smoke, "Smoke-test a built .ankiaddon archive in isolation"),
    "info": (cmd_info, "Print discovered paths and versions"),
}


def cmd_help() -> int:
    print_help(COMMANDS)
    return 0


_split_cli_args = split_cli_args


def main() -> None:
    command, command_args, verbose = split_cli_args(sys.argv[1:])
    set_verbose(verbose)
    if command is None or command in ("help", "--help", "-h"):
        cmd_help()
        raise SystemExit(0)
    if command not in COMMANDS:
        print(f"Unknown command: {command!r}\n")
        cmd_help()
        raise SystemExit(1)
    global _COMMAND_ARGS
    _COMMAND_ARGS = command_args
    print(f"[dev] selected command: {command}" + (" (verbose)" if verbose else ""))
    func, _ = COMMANDS[command]
    raise SystemExit(func())


if __name__ == "__main__":
    main()
