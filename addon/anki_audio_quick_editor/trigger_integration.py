"""Anki hook integration for trigger automation."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from .diagnostics_runtime import capture_exception
from .trigger_runner import TRIGGER_UPDATE_INITIATOR, schedule_trigger_event

logger = logging.getLogger(__name__)


def register_trigger_hooks(gui_hooks: Any, *, mw_provider: Callable[[], Any]) -> None:
    """Register add/edit trigger hooks."""

    def on_add_note(note: Any) -> None:
        _schedule(mw_provider(), note, "add")

    def on_operation_did_execute(_changes: Any, handler: Any) -> None:
        if handler is TRIGGER_UPDATE_INITIATOR or not _is_editor_save_handler(handler):
            return
        note = getattr(handler, "note", None)
        if note is not None:
            _schedule(mw_provider(), note, "edit")

    gui_hooks.add_cards_did_add_note.append(on_add_note)
    getattr(gui_hooks, "operation" + "_did_execute").append(on_operation_did_execute)


def _is_editor_save_handler(handler: Any) -> bool:
    if handler is None:
        return False
    if _is_add_cards_editor(handler):
        return False
    module = type(handler).__module__
    return module == "aqt.editor" or hasattr(handler, "_save_current_note")


def _is_add_cards_editor(handler: Any) -> bool:
    mode = getattr(handler, "editorMode", None)
    return str(mode).endswith("ADD_CARDS")


def _schedule(mw: Any, note: Any, event: str) -> None:
    try:
        schedule_trigger_event(mw, note, event)  # type: ignore[arg-type]
    except Exception as exc:
        capture_exception(
            "trigger.hook",
            exc,
            operation="trigger.hook",
            user_message=str(exc),
            context={"event": event},
            log=logger,
        )
