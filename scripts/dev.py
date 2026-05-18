#!/usr/bin/env python3
"""Cross-platform task runner for Anki Audio Quick Editor development."""

from __future__ import annotations

import json
import shutil
import sys
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# isort: off
from scripts.dev_tasks.coverage import cmd_coverage, cmd_info, cmd_sonar
from scripts.dev_tasks.process import _run, _run_capture
from scripts.dev_tasks.pytest_runner import _run_pytest
from scripts.dev_tasks.python_env import (
    _anki_bin_dir,
    _die,
    _find_anki_python,
    _setup_addon_symlink,
)
from scripts.dev_tasks.quality import _mutmut_fix_stats_prefix_mismatch, _radon_complexity_violations
# isort: on

ADDON_DIR = ROOT / "addon" / "anki_audio_quick_editor"
SETTINGS_UI_DIR = ROOT / "settings_ui"
PYTHON_COVERAGE_FAIL_UNDER = 70
RADON_FAIL_MIN_RANK = "C"
DEV_DEPS = [
    "pytest-cov",
    "pytest-qt",
    "ruff",
    "mypy",
    "radon",
    "import-linter",
    "deptry",
    "vulture",
    "bandit",
    "pytest-randomly",
    "mutmut",
    "jsonschema",
    "praat-parselmouth>=0.4.7",
]


def cmd_setup() -> int:
    anki_python = _find_anki_python()
    print(f"Anki Python: {anki_python}")
    pip_rc = _run([str(anki_python), "-m", "pip", "install", *DEV_DEPS], label="installing Python dev dependencies")
    if pip_rc == 0:
        print(f"  Installed: {', '.join(DEV_DEPS)}")
    _setup_addon_symlink()
    npm_rc = 0
    if SETTINGS_UI_DIR.is_dir() and shutil.which("npm"):
        npm_cmd = ["npm", "ci", "--legacy-peer-deps"]
        if not (SETTINGS_UI_DIR / "package-lock.json").is_file():
            npm_cmd = ["npm", "install", "--legacy-peer-deps"]
        npm_rc = _run(npm_cmd, cwd=SETTINGS_UI_DIR, label="settings UI npm install")
    if pip_rc != 0:
        return pip_rc
    return npm_rc


def cmd_test() -> int:
    contracts_rc = cmd_contracts_generate()
    if contracts_rc != 0:
        return contracts_rc
    return _run_pytest("tests/", label="python tests")


def cmd_test_anki_api() -> int:
    return _run_pytest("anki_api_contract/", label="Anki API compatibility tests")


def cmd_test_e2e() -> int:
    build_rc = cmd_build_ui()
    if build_rc != 0:
        return build_rc
    return _run_pytest("e2e/", label="python e2e tests")


def cmd_lint() -> int:
    anki_python = _find_anki_python()
    return _run([str(anki_python), "-m", "ruff", "check"], label="ruff lint")


def cmd_typecheck() -> int:
    contracts_rc = cmd_contracts_generate()
    if contracts_rc != 0:
        return contracts_rc
    anki_python = _find_anki_python()
    return _run([str(anki_python), "-m", "mypy"], label="mypy typecheck")


def cmd_arch() -> int:
    anki_python = _find_anki_python()
    lint_imports = _anki_bin_dir(anki_python) / "lint-imports"
    if not lint_imports.is_file():
        _die(f"lint-imports not found at {lint_imports}. Run: python3 scripts/dev.py setup")
    return _run([str(lint_imports)], env={"PYTHONPATH": "addon"}, label="import-linter architecture check")


def cmd_architecture_report() -> int:
    json_mode = "--json" in sys.argv[2:]
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
        ],
        label="bandit security",
    )


def cmd_deps() -> int:
    anki_python = _find_anki_python()
    return _run([str(anki_python), "-m", "deptry", "."], label="deptry dependency check")


def cmd_muttest() -> int:
    anki_python = _find_anki_python()
    mutmut_args = sys.argv[2:]
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
    steps: list[tuple[str, Callable[[], int]]] = [
        ("config-schema", cmd_config_schema),
        ("contracts-generate", cmd_contracts_generate),
        ("contracts-check", cmd_contracts_check),
        ("architecture-report", cmd_architecture_report),
        ("lint", cmd_lint),
        ("file-lines", cmd_file_lines),
        ("typecheck", cmd_typecheck),
        ("security", cmd_security),
        ("deadcode", cmd_deadcode),
        ("deps", cmd_deps),
        ("complexity", cmd_complexity),
        ("arch", cmd_arch),
        ("test-anki-api", cmd_test_anki_api),
        ("test", cmd_test),
        ("test-svelte", cmd_test_svelte),
    ]
    failed: list[str] = []
    for index, (name, func) in enumerate(steps, start=1):
        print(f"\n{'=' * 60}\n  Step {index}/{len(steps)}: {name}\n{'=' * 60}\n")
        rc = func()
        if rc != 0:
            failed.append(name)
            print(f"\n  FAILED: {name}")
    print(f"\n{'=' * 60}")
    if failed:
        print(f"  {len(failed)} step(s) failed: {', '.join(failed)}")
    else:
        print("  All checks passed!")
    print(f"{'=' * 60}")
    return 1 if failed else 0


def cmd_config_schema() -> int:
    anki_python = _find_anki_python()
    return _run([str(anki_python), "scripts/config_schema_validate.py"], label="config schema validation")


def cmd_contracts_generate() -> int:
    return _run([sys.executable, "scripts/generate_contracts.py", "--write"], label="contract generation")


def cmd_contracts_check() -> int:
    return _run([sys.executable, "scripts/generate_contracts.py", "--check"], label="contract staleness check")


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


def cmd_build_ui() -> int:
    if not SETTINGS_UI_DIR.is_dir():
        _die("settings_ui/ directory not found.")
    if not shutil.which("npm"):
        _die("npm not found. Install Node.js 18+.")
    contracts_rc = cmd_contracts_generate()
    if contracts_rc != 0:
        return contracts_rc
    return _run(["npm", "run", "build"], cwd=SETTINGS_UI_DIR, label="frontend webview bundle build")


def cmd_build() -> int:
    return cmd_build_ui()


def cmd_test_svelte() -> int:
    if not SETTINGS_UI_DIR.is_dir():
        print("ERROR: settings_ui/ not found; cannot validate frontend.", file=sys.stderr)
        return 1
    if not shutil.which("npm"):
        print("ERROR: npm not found. Install Node.js 18+.", file=sys.stderr)
        return 1
    if not (SETTINGS_UI_DIR / "node_modules").is_dir():
        print("ERROR: settings_ui/node_modules not found. Run: python3 scripts/dev.py setup", file=sys.stderr)
        return 1
    build_rc = cmd_build_ui()
    if build_rc != 0:
        return build_rc
    return _run(["npm", "run", "validate"], cwd=SETTINGS_UI_DIR, label="frontend UI validation")


def cmd_release() -> int:
    return _run([sys.executable, "scripts/release.py"], label="release build")


COMMANDS: dict[str, tuple[Callable[[], int], str]] = {
    "setup": (cmd_setup, "One-time setup: install dev deps, create symlink, npm install"),
    "architecture-report": (cmd_architecture_report, "Inspect executable architecture contracts and report violations"),
    "test": (cmd_test, "Run unit + architecture tests"),
    "test-e2e": (cmd_test_e2e, "Build frontend bundles, then run e2e tests (requires Anki runtime)"),
    "lint": (cmd_lint, "Run ruff linter"),
    "typecheck": (cmd_typecheck, "Run mypy type checker"),
    "arch": (cmd_arch, "Run import-linter architecture contracts"),
    "test-anki-api": (cmd_test_anki_api, "Run real Anki API compatibility tests"),
    "complexity": (cmd_complexity, "Run radon complexity check"),
    "deadcode": (cmd_deadcode, "Find dead code (vulture)"),
    "security": (cmd_security, "Run bandit security linter"),
    "deps": (cmd_deps, "Check dependencies (deptry)"),
    "check": (
        cmd_check,
        "Full QC: config-schema + contracts-generate + contracts-check + architecture-report + lint + typecheck + "
        "file-lines + security + deadcode + deps + complexity + arch + test-anki-api + test + frontend validate",
    ),
    "coverage": (cmd_coverage, f"Run tests with branch coverage report (fail under {PYTHON_COVERAGE_FAIL_UNDER}%)"),
    "sonar": (cmd_sonar, "Optional SonarQube analysis (needs SONAR_TOKEN)"),
    "muttest": (cmd_muttest, "Mutation testing (advisory, opt-in)"),
    "build": (cmd_build, "Build the settings and editor Svelte bundles"),
    "build-ui": (cmd_build_ui, "Build the settings and editor Svelte bundles"),
    "test-svelte": (cmd_test_svelte, "Build frontend bundles, then run validation: svelte-check + ESLint + tsc + Vitest coverage"),
    "config-schema": (cmd_config_schema, "Validate config.json against JSON Schema"),
    "contracts-generate": (cmd_contracts_generate, "Generate Python and TypeScript JSON contracts"),
    "contracts-check": (cmd_contracts_check, "Verify generated JSON contracts are current"),
    "file-lines": (cmd_file_lines, "Check hand-maintained Python files against line-count limits"),
    "release": (cmd_release, "Run scripts/release.py"),
    "info": (cmd_info, "Print discovered paths and versions"),
}


def cmd_help() -> int:
    print("Usage: python3 scripts/dev.py <command>\n")
    print("First time? Run 'setup' to install dev tools:\n")
    print("  python3 scripts/dev.py setup\n")
    print("Commands:")
    max_name = max(len(name) for name in COMMANDS)
    for name, (_, desc) in COMMANDS.items():
        print(f"  {name:<{max_name}}  {desc}")
    print(f"\n  {'help':<{max_name}}  Show this help message")
    return 0


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("help", "--help", "-h"):
        cmd_help()
        raise SystemExit(0)
    command = sys.argv[1]
    if command not in COMMANDS:
        print(f"Unknown command: {command!r}\n")
        cmd_help()
        raise SystemExit(1)
    print(f"[dev] selected command: {command}")
    func, _ = COMMANDS[command]
    raise SystemExit(func())


if __name__ == "__main__":
    main()
