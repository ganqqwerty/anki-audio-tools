"""Config schema and generated contract commands for the dev runner."""

from __future__ import annotations

import sys

from scripts.dev_tasks.process import _run
from scripts.dev_tasks.python_env import _find_anki_python


def cmd_config_schema() -> int:
    anki_python = _find_anki_python()
    return _run([str(anki_python), "scripts/config_schema_validate.py"], label="config schema validation")


def cmd_contracts_generate() -> int:
    return _run([sys.executable, "scripts/generate_contracts.py", "--write"], label="contract generation")


def cmd_contracts_check() -> int:
    return _run([sys.executable, "scripts/generate_contracts.py", "--check"], label="contract staleness check")
