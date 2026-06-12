"""Pure helpers for building executable persistent undo chains."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from .errors import AudioQuickEditorError
from .media_paths import media_filenames_match
from .persistent_history import PersistentHistoryOperation
from .sound_refs import replace_sound_reference, select_first_sound_reference


@dataclass(frozen=True)
class PersistentUndoChainResult:
    operations: list[PersistentHistoryOperation]
    break_reason: str | None
    break_operation_id: int | None


def build_persistent_undo_chain(
    *,
    current_field_html: str,
    operations: Iterable[PersistentHistoryOperation],
    old_media_available: Callable[[PersistentHistoryOperation], bool],
) -> PersistentUndoChainResult:
    """Return the contiguous executable undo chain from the current field state."""
    chain: list[PersistentHistoryOperation] = []
    current_html = current_field_html
    for operation in operations:
        if not old_media_available(operation):
            return PersistentUndoChainResult(chain, "old_media_unavailable", operation.id)
        restored_html = restored_field_html(current_html, operation)
        if restored_html is None:
            return PersistentUndoChainResult(chain, "current_field_not_applicable", operation.id)
        chain.append(operation)
        current_html = restored_html
    return PersistentUndoChainResult(chain, None, None)


def persistent_undo_menu_items(
    operations: Iterable[PersistentHistoryOperation],
    *,
    empty_label: str,
) -> list[dict[str, str]]:
    """Return frontend menu items for persistent undo operations."""
    return [
        {
            "id": f"persistent:{operation.id}",
            "label": operation.status_summary.strip() or empty_label,
        }
        for operation in operations
    ]


def restored_field_html(field_html: str, operation: PersistentHistoryOperation) -> str | None:
    """Return field HTML after applying one persistent undo row, if applicable."""
    if field_html == operation.new_field_html:
        return operation.old_field_html
    try:
        selection = select_first_sound_reference(field_html)
    except AudioQuickEditorError:
        return None
    if selection.selected is not None and media_filenames_match(selection.selected.filename, operation.new_filename):
        return replace_sound_reference(field_html, selection.selected, operation.old_filename)
    return None
