"""CLI parsing and help rendering for the development task runner."""

from __future__ import annotations

from collections.abc import Callable


def print_help(commands: dict[str, tuple[Callable[[], int], str]]) -> None:
    print("Usage: python3 scripts/dev.py <command>\n")
    print("First time? Run 'setup' to install dev tools:\n")
    print("  python3 scripts/dev.py setup\n")
    print("Default command output is concise. Add --verbose after any command for live tool output:\n")
    print("  python3 scripts/dev.py check --verbose\n")
    print("Commands:")
    max_name = max(len(name) for name in commands)
    for name, (_, desc) in commands.items():
        print(f"  {name:<{max_name}}  {desc}")
    print(f"\n  {'help':<{max_name}}  Show this help message")


def split_cli_args(args: list[str]) -> tuple[str | None, list[str], bool]:
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
