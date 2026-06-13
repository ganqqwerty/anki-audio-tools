"""CLI parsing for the development task runner."""

from __future__ import annotations

import argparse
import math
from contextlib import suppress

from scripts.dev_scripts.types import CommandRegistry


def _idle_timeout_seconds(raw: str) -> float:
    try:
        value = float(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number of seconds") from exc
    if not math.isfinite(value):
        raise argparse.ArgumentTypeError("must be a finite number of seconds")
    if value < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return value


def build_parser(commands: CommandRegistry) -> argparse.ArgumentParser:
    def _escape_help(text: str) -> str:
        return text.replace("%", "%%")

    command_help_lines = ["Commands:"]
    max_name = max(len(name) for name in commands)
    for name, (_, desc) in commands.items():
        command_help_lines.append(f"  {name:<{max_name}}  {desc}")

    parser = argparse.ArgumentParser(
        prog="python3 scripts/dev.py",
        usage="python3 scripts/dev.py [--verbose] [--idle-timeout SECONDS] <command> [args ...]",
        description=(
            "First time? Run 'setup' to install dev tools:\n\n"
            "  python3 scripts/dev.py setup\n\n"
            "Default command output is concise. Add --verbose before the command for live tool output:\n\n"
            "  python3 scripts/dev.py --verbose check\n\n"
            "Tune the no-output subprocess kill threshold with --idle-timeout before the command:\n\n"
            "  python3 scripts/dev.py --idle-timeout 900 check\n\n"
            + "\n".join(command_help_lines)
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--verbose", action="store_true", help="stream subprocess output live")
    parser.add_argument(
        "--idle-timeout",
        type=_idle_timeout_seconds,
        metavar="SECONDS",
        default=None,
        help=(
            "terminate subprocesses after SECONDS without output; use 0 to disable "
            "(default: DEV_IDLE_TIMEOUT_SECS or 300)"
        ),
    )
    subparsers = parser.add_subparsers(dest="command")
    for name, (_, desc) in commands.items():
        subparser = subparsers.add_parser(name, help=_escape_help(desc), add_help=False)
        subparser.add_argument("command_args", nargs=argparse.REMAINDER)
    help_parser = subparsers.add_parser("help", help="show this help message", add_help=False)
    help_parser.add_argument("command_args", nargs=argparse.REMAINDER)
    return parser


def parse_cli_args(
    args: list[str],
    commands: CommandRegistry,
) -> tuple[str | None, list[str], bool, float | None]:
    parser = build_parser(commands)
    with suppress(ImportError):
        import argcomplete

        argcomplete.autocomplete(parser)
    namespace = parser.parse_args(args)
    command_args = list(getattr(namespace, "command_args", []))
    for global_option in ("--verbose", "--idle-timeout"):
        if any(
            argument == global_option or argument.startswith(f"{global_option}=")
            for argument in command_args
        ):
            parser.error(f"unrecognized arguments: {global_option}")
    return namespace.command, command_args, namespace.verbose, namespace.idle_timeout
