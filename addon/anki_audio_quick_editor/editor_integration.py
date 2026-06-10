"""Anki editor hook registration adapter."""

from __future__ import annotations

from typing import Any, Callable

from . import editor_runtime
from .editor_actions import BRIDGE_COMMANDS
from .editor_callbacks import _handle_bridge_command, _stop_session_playback
from .editor_runtime import SESSIONS as _SESSIONS
from .editor_runtime import SettingsLifecycleCallbacks
from .editor_session import EditorSession, reset_for_note_load
from .editor_webview_injection import editor_injection_script

SettingsOpener = Callable[[SettingsLifecycleCallbacks | None], None]
_SETTINGS_OPENER: SettingsOpener | None = None
__all__ = [
    "BRIDGE_COMMANDS",
    "EditorSession",
    "editor_injection_script",
    "register_editor_hooks",
]


def register_editor_hooks(
    gui_hooks: Any,
    *,
    settings_opener: SettingsOpener | None = None,
) -> None:
    """Register all editor hooks used by the add-on."""
    global _SETTINGS_OPENER
    _SETTINGS_OPENER = settings_opener
    editor_runtime.SETTINGS_OPENER = settings_opener
    gui_hooks.editor_did_init.append(_on_editor_did_init)
    gui_hooks.editor_will_load_note.append(_on_editor_will_load_note)


def _on_editor_did_init(editor: Any) -> None:
    for command in BRIDGE_COMMANDS:
        editor._links[command] = lambda current_editor, cmd=command: _handle_bridge_command(
            current_editor, cmd
        )


def _on_editor_will_load_note(js: str, note: Any, editor: Any) -> str:
    _reset_editor_session_for_note_load(editor, getattr(note, "id", None))
    _SESSIONS.setdefault(editor, EditorSession()).note_id = getattr(note, "id", None)
    return f"{js}\n{editor_injection_script(editor, note)}"


def _reset_editor_session_for_note_load(editor: Any, note_id: int | None = None) -> None:
    session = _SESSIONS.get(editor)
    if session is None:
        return
    if not reset_for_note_load(session, note_id):
        return
    _stop_session_playback(session)
    if not hasattr(editor, "web"):
        return
    editor.web.eval(
        "(() => {"
        "window.__aqeHistoryAvailabilityByField = {};"
        "document.querySelectorAll('.aqe-controls').forEach((controls) => {"
        "const ord = Number(controls.dataset.aqeFieldOrd || '0');"
        "window.__aqeSetHistoryAvailability && window.__aqeSetHistoryAvailability(ord, false, false);"
        "});"
        "})()"
    )
