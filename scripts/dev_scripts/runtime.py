"""Managed-runtime development commands."""

from __future__ import annotations

import sys

from scripts.dev_tasks.process import run_process
from scripts.dev_tasks.python_env import find_anki_python


def cmd_runtime_install(command_args: list[str]) -> int:
    if command_args:
        print("Usage: python scripts/dev.py runtime-install", file=sys.stderr)
        return 1
    return _run_runtime_helper("install", label="managed runtime install")


def cmd_runtime_preflight() -> int:
    runtime_rc = _run_runtime_helper("require-ready", label="managed runtime readiness")
    if runtime_rc != 0:
        return runtime_rc
    return run_process(
        [sys.executable, "scripts/vendor_wheels.py", "verify"],
        label="vendored runtime wheels",
        show_output_on_failure=True,
    )


def _run_runtime_helper(action: str, *, label: str) -> int:
    anki_python = find_anki_python()
    return run_process(
        [str(anki_python), "scripts/dev_runtime.py", action],
        label=label,
        show_output_on_failure=True,
    )
