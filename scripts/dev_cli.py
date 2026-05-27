"""CLI parsing for the development task runner."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from contextlib import suppress


def build_parser(commands: dict[str, tuple[Callable[[], int], str]]) -> argparse.ArgumentParser:
    def _escape_help(text: str) -> str:
        return text.replace("%", "%%")

    command_help_lines = ["Commands:"]
    max_name = max(len(name) for name in commands)
    for name, (_, desc) in commands.items():
        command_help_lines.append(f"  {name:<{max_name}}  {desc}")

    parser = argparse.ArgumentParser(
        prog="python3 scripts/dev.py",
        usage="python3 scripts/dev.py [--verbose] <command> [args ...]",
        description=(
            "First time? Run 'setup' to install dev tools:\n\n"
            "  python3 scripts/dev.py setup\n\n"
            "Default command output is concise. Add --verbose before the command for live tool output:\n\n"
            "  python3 scripts/dev.py --verbose check\n\n"
            + "\n".join(command_help_lines)
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--verbose", action="store_true", help="stream subprocess output live")
    subparsers = parser.add_subparsers(dest="command")
    for name, (_, desc) in commands.items():
        subparser = subparsers.add_parser(name, help=_escape_help(desc), add_help=False)
        subparser.add_argument("command_args", nargs=argparse.REMAINDER)
    help_parser = subparsers.add_parser("help", help="show this help message", add_help=False)
    help_parser.add_argument("command_args", nargs=argparse.REMAINDER)
    return parser


def parse_cli_args(
    args: list[str],
    commands: dict[str, tuple[Callable[[], int], str]],
) -> tuple[str | None, list[str], bool]:
    parser = build_parser(commands)
    with suppress(ImportError):
        import argcomplete

        argcomplete.autocomplete(parser)
    namespace = parser.parse_args(args)
    command_args = list(getattr(namespace, "command_args", []))
    if "--verbose" in command_args:
        parser.error("unrecognized arguments: --verbose")
    return namespace.command, command_args, namespace.verbose
