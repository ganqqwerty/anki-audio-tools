"""Anki editor note-load hook callbacks."""

from __future__ import annotations

from typing import Any

from .editor_callbacks import stop_session_playback
from .editor_runtime import SESSIONS
from .editor_session import EditorSession, reset_for_note_load
from .editor_webview_injection import editor_injection_script


def on_editor_will_load_note(js: str, note: Any, editor: Any) -> str:
    """Reset note-scoped session state and append inline editor controls."""
    note_id = getattr(note, "id", None)
    reset_editor_session_for_note_load(editor, note_id)
    SESSIONS.setdefault(editor, EditorSession()).note_id = note_id
    return f"{js}\n{editor_injection_script(editor, note)}"


def reset_editor_session_for_note_load(editor: Any, note_id: int | None = None) -> None:
    """Reset an existing editor session when the editor changes notes."""
    session = SESSIONS.get(editor)
    if session is None:
        return
    if not reset_for_note_load(session, note_id):
        return
    stop_session_playback(session)
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
