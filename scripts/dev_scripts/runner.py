"""Parsed-command dispatch for scripts/dev.py."""

from __future__ import annotations

from collections.abc import Callable

from scripts.dev_cli import build_parser
from scripts.dev_scripts.types import CommandRegistry
from scripts.dev_tasks.process import quiet_test_output, set_idle_timeout, set_verbose

QUIET_TEST_COMMANDS = frozenset(
    {"test", "test-anki-api", "test-e2e", "test-e2e-parallel", "test-svelte", "coverage"}
)


def print_help(commands: CommandRegistry) -> None:
    build_parser(commands).print_help()


def _run_quiet_command(func: Callable[[list[str]], int], command_args: list[str]) -> int:
    result: int | None = None
    with quiet_test_output():
        result = func(command_args)
    assert result is not None
    return result


def run_command(
    command: str | None,
    command_args: list[str],
    *,
    verbose: bool,
    idle_timeout_s: float | None,
    commands: CommandRegistry,
) -> int:
    set_verbose(verbose)
    set_idle_timeout(idle_timeout_s)
    if command is None or command in ("help", "--help", "-h"):
        print_help(commands)
        return 0
    func, _description = commands[command]
    if verbose or command not in QUIET_TEST_COMMANDS:
        print(f"[dev] selected command: {command}" + (" (verbose)" if verbose else ""))
        return func(command_args)
    return _run_quiet_command(func, command_args)
