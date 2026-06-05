"""Release-related commands for scripts/dev.py."""

from __future__ import annotations

import sys

from scripts.dev_tasks.process import run_process
from scripts.dev_tasks.python_env import find_anki_python


def cmd_release(_command_args: list[str]) -> int:
    return run_process([sys.executable, "scripts/release.py"], label="release build")


def cmd_release_assets(command_args: list[str]) -> int:
    if not command_args:
        print("Usage: python3 scripts/dev.py release-assets <subcommand> [args...]", file=sys.stderr)
        return 1
    return run_process([sys.executable, "scripts/release_assets.py", *command_args], label="release asset preparation")


def cmd_release_runtime(command_args: list[str]) -> int:
    if not command_args:
        print("Usage: python3 scripts/dev.py release-runtime <subcommand> [args...]", file=sys.stderr)
        return 1
    return run_process([sys.executable, "scripts/release_runtime_cli.py", *command_args], label="runtime release")


def cmd_vendor_wheels(command_args: list[str]) -> int:
    if not command_args:
        print("Usage: python3 scripts/dev.py vendor-wheels <verify|download> [args...]", file=sys.stderr)
        return 1
    return run_process([sys.executable, "scripts/vendor_wheels.py", *command_args], label="vendored wheels")


def cmd_release_smoke(command_args: list[str]) -> int:
    if len(command_args) != 1:
        print("Usage: python3 scripts/dev.py release-smoke <archive.ankiaddon>", file=sys.stderr)
        return 1
    anki_python = find_anki_python()
    return run_process([str(anki_python), "scripts/release_smoke.py", command_args[0]], label="release archive smoke test")
