"""Full check command wiring for scripts/dev.py."""

from __future__ import annotations

from scripts.dev_scripts import check_runner
from scripts.dev_scripts.architecture import cmd_architecture_report
from scripts.dev_scripts.quality import (
    cmd_deadcode,
    cmd_deps,
    cmd_i18n,
    cmd_quality_metrics,
    cmd_security,
)
from scripts.dev_scripts.testing import cmd_test, cmd_test_anki_api, run_test_targets
from scripts.dev_scripts.tooling import cmd_arch, cmd_lint, cmd_typecheck, run_typecheck
from scripts.dev_tasks.contracts import (
    cmd_config_schema,
    cmd_contracts_check,
    cmd_contracts_generate,
)
from scripts.dev_tasks.coverage import cmd_coverage
from scripts.dev_tasks.frontend import cmd_build_ui, cmd_test_svelte
from scripts.dev_tasks.quality_tools import cmd_qodana
from scripts.dev_tasks.repository import cmd_file_lines


def cmd_check(_command_args: list[str]) -> int:
    print("Typically takes 3-4 minutes. More than")
    return check_runner.cmd_check(
        cmd_config_schema=cmd_config_schema,
        cmd_contracts_generate=cmd_contracts_generate,
        cmd_contracts_check=cmd_contracts_check,
        cmd_build_ui=cmd_build_ui,
        cmd_lint=lambda: cmd_lint([]),
        cmd_i18n=lambda: cmd_i18n([]),
        cmd_architecture_report=lambda: cmd_architecture_report([]),
        cmd_file_lines=cmd_file_lines,
        run_typecheck=run_typecheck,
        cmd_security=lambda: cmd_security([]),
        cmd_deadcode=lambda: cmd_deadcode([]),
        cmd_deps=lambda: cmd_deps([]),
        cmd_quality_metrics=lambda: cmd_quality_metrics([]),
        cmd_qodana=cmd_qodana,
        cmd_arch=lambda: cmd_arch([]),
        cmd_test_anki_api=lambda: cmd_test_anki_api([]),
        run_test_targets=lambda: run_test_targets([]),
        cmd_coverage=cmd_coverage,
        cmd_typecheck=lambda: cmd_typecheck([]),
        cmd_test=lambda: cmd_test([]),
        cmd_test_svelte=cmd_test_svelte,
    )
