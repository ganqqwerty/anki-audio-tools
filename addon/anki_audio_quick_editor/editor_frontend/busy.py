"""Editor frontend busy-state helpers."""

from __future__ import annotations

import json
from typing import Any


def set_busy(editor: Any, busy: bool, message: str, command: str, deps: Any) -> None:
    """Set busy state for the active field."""
    field_index = getattr(editor, "currentField", None)
    if field_index is None:
        field_index = getattr(editor, "last_field_index", None)
    if field_index is None:
        session = deps.sessions.get(editor)
        field_index = session.field_index if session else None
    if field_index is None:
        return
    deps.set_busy_for_field(editor, int(field_index), busy, message, command)


def set_busy_for_field(
    editor: Any,
    field_index: int,
    busy: bool,
    message: str = "",
    command: str = "",
) -> None:
    """Set busy state for a specific editor field."""
    editor.web.eval(
        "window.__aqeSetBusy && window.__aqeSetBusy("
        f"{json.dumps(int(field_index))}, {json.dumps(busy)}, "
        f"{json.dumps(message)}, {json.dumps(command)})"
    )
