#!/usr/bin/env python3
"""Argument entrypoint for Anki Audio Quick Editor development commands."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.dev_cli import parse_cli_args
from scripts.dev_scripts.registry import COMMANDS
from scripts.dev_scripts.runner import run_command

_parse_cli_args = parse_cli_args


def main() -> None:
    command, command_args, verbose, idle_timeout_s = parse_cli_args(sys.argv[1:], COMMANDS)
    raise SystemExit(
        run_command(
            command,
            command_args,
            verbose=verbose,
            idle_timeout_s=idle_timeout_s,
            commands=COMMANDS,
        )
    )


if __name__ == "__main__":
    main()
