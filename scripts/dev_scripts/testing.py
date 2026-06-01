"""Python and e2e test commands for scripts/dev.py."""

from __future__ import annotations

from scripts.dev_tasks.contracts import cmd_contracts_generate
from scripts.dev_tasks.e2e_parallel import (
    cmd_test_e2e_parallel as _cmd_test_e2e_parallel,
)
from scripts.dev_tasks.frontend import cmd_build_ui
from scripts.dev_tasks.pytest_runner import run_pytest


def run_test_targets(command_args: list[str]) -> int:
    targets = command_args or ["tests/"]
    for target in targets:
        label = f"python tests: {target}" if command_args else "python tests"
        rc = run_pytest(target, label=label)
        if rc != 0:
            return rc
    return 0


def cmd_test(command_args: list[str]) -> int:
    contracts_rc = cmd_contracts_generate()
    if contracts_rc != 0:
        return contracts_rc
    return run_test_targets(command_args)


def cmd_test_anki_api(_command_args: list[str]) -> int:
    return run_pytest("anki_api_contract/", label="Anki API compatibility tests")


def cmd_test_e2e(command_args: list[str]) -> int:
    build_rc = cmd_build_ui()
    if build_rc != 0:
        return build_rc
    targets = command_args or ["e2e/"]
    for target in targets:
        label = f"python e2e tests: {target}" if command_args else "python e2e tests"
        rc = run_pytest(target, label=label)
        if rc != 0:
            return rc
    return 0


def cmd_test_e2e_parallel(command_args: list[str]) -> int:
    build_rc = cmd_build_ui()
    if build_rc != 0:
        return build_rc
    return _cmd_test_e2e_parallel(command_args)
