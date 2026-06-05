"""Tooling commands for linting, typing, and import boundaries."""

from __future__ import annotations

import os

from scripts.dev_tasks.contracts import cmd_contracts_generate
from scripts.dev_tasks.process import run_process
from scripts.dev_tasks.python_env import anki_bin_dir, die, find_anki_python


def cmd_lint(_command_args: list[str]) -> int:
    anki_python = find_anki_python()
    fix_rc = run_process([str(anki_python), "-m", "ruff", "check", "--fix"], label="ruff lint autofix")
    if fix_rc != 0:
        return fix_rc
    return run_process([str(anki_python), "-m", "ruff", "check"], label="ruff lint")


def run_typecheck() -> int:
    anki_python = find_anki_python()
    return run_process([str(anki_python), "-m", "mypy"], label="mypy typecheck")


def cmd_typecheck(_command_args: list[str]) -> int:
    contracts_rc = cmd_contracts_generate()
    if contracts_rc != 0:
        return contracts_rc
    return run_typecheck()


def cmd_arch(_command_args: list[str]) -> int:
    anki_python = find_anki_python()
    executable_name = "lint-imports.exe" if os.name == "nt" else "lint-imports"
    lint_imports = anki_bin_dir(anki_python) / executable_name
    if not lint_imports.is_file():
        die(f"lint-imports not found at {lint_imports}. Run: python3 scripts/dev.py setup")
    return run_process([str(lint_imports)], env={"PYTHONPATH": "addon"}, label="import-linter architecture check")
