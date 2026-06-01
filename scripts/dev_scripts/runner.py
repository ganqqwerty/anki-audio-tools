"""Parsed-command dispatch for scripts/dev.py."""

from __future__ import annotations

from scripts.dev_cli import build_parser
from scripts.dev_scripts.types import CommandRegistry
from scripts.dev_tasks.process import set_idle_timeout, set_verbose


def print_help(commands: CommandRegistry) -> None:
    build_parser(commands).print_help()


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
    print(f"[dev] selected command: {command}" + (" (verbose)" if verbose else ""))
    func, _description = commands[command]
    return func(command_args)
