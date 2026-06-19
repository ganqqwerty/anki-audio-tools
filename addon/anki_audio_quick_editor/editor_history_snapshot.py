"""Build editor undo/redo history snapshots for frontend controls."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any, TypedDict

from .editor_edit_history import UndoEntry
from .editor_history_settings import normalize_editor_history_size
from .editor_session import EditorSession
from .i18n import t


class HistorySnapshotItem(TypedDict):
    id: str
    label: str


class HistorySnapshot(TypedDict):
    canUndo: bool
    canRedo: bool
    undoItems: list[HistorySnapshotItem]
    redoItems: list[HistorySnapshotItem]


def history_snapshot_for_field(
    editor: Any,
    *,
    field_index: int | None,
    session: EditorSession | None,
    history_size: object,
    can_persistent_undo: Callable[[Any, int | None], bool],
    latest_persistent_undo_item: Callable[[Any, int | None], HistorySnapshotItem | None],
    persistent_undo_items: Callable[[Any, int | None, int], list[HistorySnapshotItem]] | None = None,
) -> HistorySnapshot:
    """Return the undo/redo menu data for one editor field."""
    limit = normalize_editor_history_size(history_size)
    undo_items: list[HistorySnapshotItem] = []
    redo_items: list[HistorySnapshotItem] = []
    if session is not None and session.field_index == field_index:
        session.undo_history.set_max_entries(limit)
        session.redo_history.set_max_entries(limit)
        undo_items = _items_from_entries(
            "undo",
            reversed(session.undo_history.entries),
            limit,
            fallback_label=t("editor.history.undo_empty_label"),
        )
        redo_items = _items_from_entries(
            "redo",
            reversed(session.redo_history.entries),
            limit,
            fallback_label=t("editor.history.redo_empty_label"),
        )
    if field_index is not None and not undo_items:
        if persistent_undo_items is not None:
            undo_items.extend(persistent_undo_items(editor, field_index, limit))
        elif can_persistent_undo(editor, field_index):
            item = latest_persistent_undo_item(editor, field_index)
            if item is not None:
                undo_items.append(item)
    return {
        "canUndo": bool(undo_items),
        "canRedo": bool(redo_items),
        "undoItems": undo_items,
        "redoItems": redo_items,
    }


def empty_history_snapshot() -> HistorySnapshot:
    """Return an empty snapshot for compatibility wrappers."""
    return {"canUndo": False, "canRedo": False, "undoItems": [], "redoItems": []}


def _items_from_entries(
    direction: str,
    entries: Iterable[UndoEntry],
    history_size: int,
    *,
    fallback_label: str,
) -> list[HistorySnapshotItem]:
    items: list[HistorySnapshotItem] = []
    for index, entry in enumerate(entries, start=1):
        if index > history_size:
            break
        items.append({"id": f"{direction}:{index}", "label": _entry_label(entry, fallback_label)})
    return items


def _entry_label(entry: UndoEntry, fallback_label: str) -> str:
    if entry.status_summary.strip():
        return entry.status_summary.strip()
    return fallback_label
