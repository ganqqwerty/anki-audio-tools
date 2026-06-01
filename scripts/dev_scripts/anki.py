"""Real Anki launch commands for scripts/dev.py."""

from __future__ import annotations

from scripts.dev_tasks.frontend import cmd_build_ui
from scripts.dev_tasks.python_env import cmd_launch_anki, cmd_link_addon


def cmd_run_anki(_command_args: list[str]) -> int:
    build_rc = cmd_build_ui()
    if build_rc != 0:
        return build_rc
    link_rc = cmd_link_addon()
    if link_rc != 0:
        return link_rc
    return cmd_launch_anki()
