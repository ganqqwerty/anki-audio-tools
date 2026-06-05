"""Command registry for scripts/dev.py."""

from __future__ import annotations

from collections.abc import Callable

from scripts.dev_scripts.anki import cmd_run_anki
from scripts.dev_scripts.architecture import cmd_architecture_report
from scripts.dev_scripts.check import cmd_check
from scripts.dev_scripts.quality import (
    cmd_deadcode,
    cmd_deps,
    cmd_i18n,
    cmd_muttest,
    cmd_quality_metrics,
    cmd_security,
)
from scripts.dev_scripts.release import (
    cmd_release,
    cmd_release_assets,
    cmd_release_runtime,
    cmd_release_smoke,
    cmd_vendor_wheels,
)
from scripts.dev_scripts.testing import (
    cmd_test,
    cmd_test_anki_api,
    cmd_test_e2e,
    cmd_test_e2e_parallel,
)
from scripts.dev_scripts.tooling import cmd_arch, cmd_lint, cmd_typecheck
from scripts.dev_scripts.types import Command, CommandRegistry
from scripts.dev_tasks.contracts import (
    cmd_config_schema,
    cmd_contracts_check,
    cmd_contracts_generate,
)
from scripts.dev_tasks.coverage import (
    PYTHON_COVERAGE_FAIL_UNDER,
    cmd_coverage,
    cmd_info,
    cmd_sonar,
)
from scripts.dev_tasks.frontend import cmd_build, cmd_build_ui, cmd_test_svelte
from scripts.dev_tasks.python_env import cmd_link_addon
from scripts.dev_tasks.quality_tools import cmd_qodana
from scripts.dev_tasks.repository import cmd_file_lines
from scripts.dev_tasks.setup import cmd_setup


def no_args(command: Callable[[], int]) -> Command:
    return lambda _command_args: command()


COMMANDS: CommandRegistry = {
    "setup": (no_args(cmd_setup), "One-time setup: install dev deps, create symlink, npm install"),
    "link-addon": (no_args(cmd_link_addon), "Point Anki's local numeric add-on symlink at this worktree"),
    "run-anki": (cmd_run_anki, "Build UI, link this worktree add-on, and launch real Anki"),
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
    "qodana": (no_args(cmd_qodana), "Run Qodana code quality analysis"),
    "check": (
        cmd_check,
        "Full QC: config-schema + contracts-generate + contracts-check + architecture-report + lint + typecheck + i18n + file-lines + security + deadcode + deps + complexity + qodana + arch + test-anki-api + test + coverage + frontend validate",
    ),
    "coverage": (
        no_args(cmd_coverage),
        f"Run tests with branch coverage report (fail under {PYTHON_COVERAGE_FAIL_UNDER}%)",
    ),
    "sonar": (no_args(cmd_sonar), "Optional SonarQube analysis (needs SONAR_TOKEN)"),
    "muttest": (cmd_muttest, "Mutation testing (advisory, opt-in)"),
    "build": (no_args(cmd_build), "Build the settings and editor Svelte bundles"),
    "build-ui": (no_args(cmd_build_ui), "Build the settings and editor Svelte bundles"),
    "test-svelte": (
        no_args(cmd_test_svelte),
        "Build frontend bundles, run ESLint autofix, then validate: svelte-check + ESLint + tsc + Vitest coverage",
    ),
    "config-schema": (no_args(cmd_config_schema), "Validate config.json against JSON Schema"),
    "contracts-generate": (no_args(cmd_contracts_generate), "Generate Python and TypeScript JSON contracts"),
    "contracts-check": (no_args(cmd_contracts_check), "Verify generated JSON contracts are current"),
    "file-lines": (no_args(cmd_file_lines), "Check hand-maintained Python files against line-count limits"),
    "release": (cmd_release, "Run scripts/release.py"),
    "release-assets": (cmd_release_assets, "Fetch, build, verify, and stage locked release runtime assets"),
    "release-runtime": (cmd_release_runtime, "Build, upload, and verify decoupled runtime release packs"),
    "vendor-wheels": (cmd_vendor_wheels, "Verify or download locked vendored Python runtime wheels"),
    "release-smoke": (cmd_release_smoke, "Smoke-test a built .ankiaddon archive in isolation"),
    "info": (no_args(cmd_info), "Print discovered paths and versions"),
}
