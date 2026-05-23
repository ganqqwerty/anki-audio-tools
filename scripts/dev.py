#!/usr/bin/env python3
"""Cross-platform task runner for Anki Audio Quick Editor development."""

from __future__ import annotations

import concurrent.futures
import json
import os
import sys
import traceback
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# isort: off
from scripts.dev_tasks.contracts import cmd_config_schema, cmd_contracts_check, cmd_contracts_generate
from scripts.dev_tasks.coverage import PYTHON_COVERAGE_FAIL_UNDER, cmd_coverage, cmd_info, cmd_sonar
from scripts.dev_tasks.frontend import cmd_build, cmd_build_ui, cmd_test_svelte
from scripts.dev_tasks.process import _run, _run_capture, is_verbose, set_verbose
from scripts.dev_tasks.pytest_runner import _run_pytest
from scripts.dev_tasks.python_env import (
    _anki_bin_dir,
    _die,
    _find_anki_python,
)
from scripts.dev_tasks.quality_tools import cmd_qodana
from scripts.dev_tasks.quality import (
    _mutmut_fix_stats_prefix_mismatch,
    _radon_complexity_violations,
    _radon_maintainability_violations,
)
from scripts.dev_tasks.repository import cmd_file_lines
from scripts.dev_tasks.setup import cmd_setup
# isort: on

ADDON_DIR = ROOT / "addon" / "anki_audio_quick_editor"
RADON_FAIL_MIN_RANK = "C"
_COMMAND_ARGS: list[str] = []
CheckStep = tuple[str, Callable[[], int]]


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
    if is_verbose():
        preflight_steps = _check_preflight_steps()
        phases = _check_post_preflight_groups(contracts_prepared=False)
        steps = [*preflight_steps, *(step for _phase_name, phase_steps in phases for step in phase_steps)]
        failed = _run_check_steps_sequential(steps)
    else:
        preflight_steps = _check_preflight_steps()
        failed = _run_check_steps_sequential(preflight_steps)
        failed_preflight = set(failed)
        contracts_prepared = "contracts-generate" not in failed_preflight and "contracts-check" not in failed_preflight
        phases = _check_post_preflight_groups(contracts_prepared=contracts_prepared)
        steps = [*preflight_steps, *(step for _phase_name, phase_steps in phases for step in phase_steps)]
        for phase_name, phase_steps in phases:
            if phase_name == "parallel":
                failed.extend(_run_check_steps_parallel(phase_steps))
            else:
                failed.extend(_run_check_steps_sequential(phase_steps))
    failed = [name for name, _func in steps if name in set(failed)]
    if is_verbose():
        print(f"\n{'=' * 60}")
    if failed:
        print(f"[dev] {len(failed)} check step(s) failed: {', '.join(failed)}")
    else:
        print("[dev] all check steps passed")
    if is_verbose():
        print(f"{'=' * 60}")
    return 1 if failed else 0


def _check_preflight_steps() -> list[CheckStep]:
    return [
        ("config-schema", cmd_config_schema),
        ("contracts-generate", cmd_contracts_generate),
        ("contracts-check", cmd_contracts_check),
        ("build-ui", cmd_build_ui),
        ("lint", cmd_lint),
    ]


def _check_post_preflight_groups(*, contracts_prepared: bool) -> list[tuple[str, list[CheckStep]]]:
    parallel_steps: list[CheckStep] = [
        ("architecture-report", cmd_architecture_report),
        ("file-lines", cmd_file_lines),
    ]
    if contracts_prepared:
        parallel_steps.append(("typecheck", _run_typecheck))
    parallel_steps.extend(
        [
            ("security", cmd_security),
            ("deadcode", cmd_deadcode),
            ("deps", cmd_deps),
            ("complexity", cmd_quality_metrics),
            ("qodana", cmd_qodana),
            ("arch", cmd_arch),
            ("test-anki-api", cmd_test_anki_api),
        ],
    )
    if contracts_prepared:
        parallel_steps.append(("test", _run_test_targets))
    parallel_steps.append(("coverage", cmd_coverage))
    if contracts_prepared:
        tail_steps: list[CheckStep] = [("test-svelte", cmd_test_svelte)]
    else:
        tail_steps = [("typecheck", cmd_typecheck), ("test", cmd_test), ("test-svelte", cmd_test_svelte)]
    return [
        ("parallel", parallel_steps),
        ("tail", tail_steps),
    ]

def _check_worker_count(step_count: int) -> int:
    default_workers = 4
    raw = os.environ.get("DEV_CHECK_JOBS")
    if raw is None:
        return max(1, min(default_workers, step_count))
    try:
        workers = int(raw)
    except ValueError:
        workers = default_workers
    return max(1, min(workers, step_count))


def _run_check_steps_sequential(steps: list[CheckStep]) -> list[str]:
    failed: list[str] = []
    total_steps = len(steps)
    for index, (name, func) in enumerate(steps, start=1):
        if is_verbose():
            print(f"\n{'=' * 60}\n  Step {index}/{total_steps}: {name}\n{'=' * 60}\n")
        else:
            print(f"[dev] check {index}/{total_steps}: {name}")
        rc = _run_check_step(name, func)
        if rc != 0:
            failed.append(name)
            print(f"[dev] FAILED: {name}")
    return failed


def _run_check_steps_parallel(steps: list[CheckStep]) -> list[str]:
    if not steps:
        return []
    workers = _check_worker_count(len(steps))
    print(f"[dev] check parallel phase: {len(steps)} step(s), {workers} worker(s)")
    failed: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_name = {
            executor.submit(_run_check_step, name, func): name
            for name, func in steps
        }
        results: dict[str, int] = {}
        for future in concurrent.futures.as_completed(future_to_name):
            name = future_to_name[future]
            rc = future.result()
            results[name] = rc
            if rc != 0:
                failed.append(name)
                print(f"[dev] FAILED: {name}")
    return [name for name, _func in steps if results.get(name, 0) != 0]


def _run_check_step(name: str, func: Callable[[], int]) -> int:
    try:
        return func()
    except Exception as exc:
        print(f"[dev] exception in check step {name}: {exc}", file=sys.stderr)
        if is_verbose():
            traceback.print_exc()
        return 1


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
    "architecture-report": (cmd_architecture_report, "Inspect executable architecture contracts and report violations"),
    "test": (cmd_test, "Run unit + architecture tests"),
    "test-e2e": (cmd_test_e2e, "Build frontend bundles, then run e2e tests (requires Anki runtime)"),
    "lint": (cmd_lint, "Run ruff safe autofix, then ruff linter"),
    "typecheck": (cmd_typecheck, "Run mypy type checker"),
    "arch": (cmd_arch, "Run import-linter architecture contracts"),
    "test-anki-api": (cmd_test_anki_api, "Run real Anki API compatibility tests"),
    "complexity": (cmd_quality_metrics, "Run radon complexity and maintainability checks"),
    "deadcode": (cmd_deadcode, "Find dead code (vulture)"),
    "security": (cmd_security, "Run bandit security linter"),
    "deps": (cmd_deps, "Check dependencies (deptry)"),
    "qodana": (cmd_qodana, "Run Qodana code quality analysis"),
    "check": (
        cmd_check,
        "Full QC: config-schema + contracts-generate + contracts-check + architecture-report + lint + typecheck + "
        "file-lines + security + deadcode + deps + complexity + qodana + arch + test-anki-api + test + coverage + "
        "frontend validate",
    ),
    "coverage": (cmd_coverage, f"Run tests with branch coverage report (fail under {PYTHON_COVERAGE_FAIL_UNDER}%)"),
    "sonar": (cmd_sonar, "Optional SonarQube analysis (needs SONAR_TOKEN)"),
    "muttest": (cmd_muttest, "Mutation testing (advisory, opt-in)"),
    "build": (cmd_build, "Build the settings and editor Svelte bundles"),
    "build-ui": (cmd_build_ui, "Build the settings and editor Svelte bundles"),
    "test-svelte": (
        cmd_test_svelte,
        "Build frontend bundles, run ESLint autofix, then validate: svelte-check + ESLint + tsc + Vitest coverage",
    ),
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
    print("Usage: python3 scripts/dev.py <command>\n")
    print("First time? Run 'setup' to install dev tools:\n")
    print("  python3 scripts/dev.py setup\n")
    print("Default command output is concise. Add --verbose after any command for live tool output:\n")
    print("  python3 scripts/dev.py check --verbose\n")
    print("Commands:")
    max_name = max(len(name) for name in COMMANDS)
    for name, (_, desc) in COMMANDS.items():
        print(f"  {name:<{max_name}}  {desc}")
    print(f"\n  {'help':<{max_name}}  Show this help message")
    return 0


def _split_cli_args(args: list[str]) -> tuple[str | None, list[str], bool]:
    command: str | None = None
    command_args: list[str] = []
    verbose = False
    for arg in args:
        if arg == "--verbose":
            verbose = True
        elif command is None:
            command = arg
        else:
            command_args.append(arg)
    return command, command_args, verbose


def main() -> None:
    command, command_args, verbose = _split_cli_args(sys.argv[1:])
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
