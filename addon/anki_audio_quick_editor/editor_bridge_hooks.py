"""Anki editor bridge command hook callbacks."""

from __future__ import annotations

import weakref
from typing import Any

from .editor_actions import BRIDGE_COMMANDS
from .editor_callbacks import handle_bridge_command
from .editor_runtime import dispose_editor_session


def on_editor_did_init(editor: Any) -> None:
    """Register editor WebView bridge commands for one Anki editor."""
    for command in BRIDGE_COMMANDS:
        # noinspection PyProtectedMember
        editor._links[command] = lambda current_editor, cmd=command: handle_bridge_command(
            current_editor, cmd
        )
    _register_editor_disposer(editor)


def _register_editor_disposer(editor: Any) -> None:
    """Cancel editor-owned resources when Anki destroys the editor widget."""
    destroyed = getattr(getattr(editor, "widget", None), "destroyed", None)
    if destroyed is None or not hasattr(destroyed, "connect"):
        return
    editor_ref = weakref.ref(editor)

    def dispose(*_args: object) -> None:
        current_editor = editor_ref()
        if current_editor is not None:
            dispose_editor_session(current_editor, reason="editor_closed")

    destroyed.connect(dispose)
