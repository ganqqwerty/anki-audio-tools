"""Editor reload lifecycle helpers for status handoff."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .editor_session import EditorSession
from .editor_session_types import PendingEditorStatus

if TYPE_CHECKING:
    from .editor_deps_protocols import EditorReloadDeps


def reload_editor_with_pending_status(
    editor: Any,
    session: EditorSession | None,
    field_index: int,
    *,
    message: str = "",
    kind: str = "info",
    deps: EditorReloadDeps,
) -> None:
    """Reload editor controls after assigning the next injected status."""
    if session is not None:
        session.pending_status = (
            PendingEditorStatus(field_index, kind=kind, message=message)
            if message
            else None
        )
    deps.dispose_editor_frontend_controls(editor)
    editor.loadNote(focusTo=field_index)
