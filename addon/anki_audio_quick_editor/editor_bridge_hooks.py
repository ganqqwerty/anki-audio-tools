"""Anki editor bridge command hook callbacks."""

from __future__ import annotations

from typing import Any

from .editor_actions import BRIDGE_COMMANDS
from .editor_callbacks import handle_bridge_command


def on_editor_did_init(editor: Any) -> None:
    """Register editor WebView bridge commands for one Anki editor."""
    for command in BRIDGE_COMMANDS:
        editor._links[command] = lambda current_editor, cmd=command: handle_bridge_command(
            current_editor, cmd
        )
