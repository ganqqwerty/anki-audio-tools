"""Narrow frontend-to-backend editor cursor projection."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .prosody_types import clamp_cursor_ms

if TYPE_CHECKING:
    from .editor_deps_protocols import CursorDeps


def set_cursor_from_web(editor: Any, deps: CursorDeps) -> None:
    """Project the stopped frontend edit cursor into the editor session."""

    def apply(value: Any) -> None:
        if getattr(editor, "note", None) is None:
            return
        session, _source_path = deps.session_and_source(editor)
        cursor_value = value.get("cursorMs") if isinstance(value, dict) else value
        field_index = deps.current_field_index(editor)
        duration_ms = deps.visualized_duration_for_field(
            session,
            field_index,
            session.current_filename,
        )
        session.cursor_ms = clamp_cursor_ms(cursor_value, duration_ms)

    deps.eval_with_callback(
        editor,
        "window.__aqeGetCursorIntent ? window.__aqeGetCursorIntent() : "
        "(window.__aqeGetCursorMs ? window.__aqeGetCursorMs() : 0)",
        apply,
    )
