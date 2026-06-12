"""Tests for pure persistent undo chain planning."""

from __future__ import annotations

from dataclasses import replace

from anki_audio_quick_editor.persistent_history import PersistentHistoryOperation
from anki_audio_quick_editor.persistent_undo_chain import (
    PersistentUndoChainResult,
    build_persistent_undo_chain,
    persistent_undo_menu_items,
)


def test_builds_contiguous_chain_newest_first() -> None:
    first = _operation(1, "a.mp3", "b.mp3", "First edit")
    second = _operation(2, "b.mp3", "c.mp3", "Second edit")
    third = _operation(3, "c.mp3", "d.mp3", "Third edit")

    result = build_persistent_undo_chain(
        current_field_html="[sound:d.mp3]",
        operations=[third, second, first],
        old_media_available=lambda operation: operation.old_filename != "missing.mp3",
    )

    assert result == PersistentUndoChainResult(
        operations=[third, second, first],
        break_reason=None,
        break_operation_id=None,
    )


def test_stops_at_stale_newest_row_to_preserve_undo_stack_semantics() -> None:
    older = _operation(1, "a.mp3", "b.mp3", "Older edit")
    stale_newest = _operation(2, "b.mp3", "c.mp3", "Stale newest edit")

    result = build_persistent_undo_chain(
        current_field_html="[sound:b.mp3]",
        operations=[stale_newest, older],
        old_media_available=lambda _operation: True,
    )

    assert result.operations == []
    assert result.break_reason == "current_field_not_applicable"
    assert result.break_operation_id == stale_newest.id


def test_stops_at_first_missing_old_media() -> None:
    first = _operation(1, "a.mp3", "b.mp3", "First edit")
    second = _operation(2, "b.mp3", "c.mp3", "Second edit")

    result = build_persistent_undo_chain(
        current_field_html="[sound:c.mp3]",
        operations=[second, first],
        old_media_available=lambda operation: operation.id != second.id,
    )

    assert result.operations == []
    assert result.break_reason == "old_media_unavailable"
    assert result.break_operation_id == second.id


def test_menu_items_use_operation_labels_and_fallback() -> None:
    labeled = _operation(1, "a.mp3", "b.mp3", "Clean label")
    unlabeled = replace(_operation(2, "b.mp3", "c.mp3", "  "), status_summary="  ")

    assert persistent_undo_menu_items([unlabeled, labeled], empty_label="Undo generated audio") == [
        {"id": "persistent:2", "label": "Undo generated audio"},
        {"id": "persistent:1", "label": "Clean label"},
    ]


def _operation(operation_id: int, old_filename: str, new_filename: str, status: str) -> PersistentHistoryOperation:
    return PersistentHistoryOperation(
        id=operation_id,
        collection_id="collection",
        note_id=1001,
        field_index=0,
        operation_type="standard-render",
        old_field_html=f"[sound:{old_filename}]",
        new_field_html=f"[sound:{new_filename}]",
        old_filename=old_filename,
        new_filename=new_filename,
        old_state_json="",
        new_state_json="",
        old_media_sha256="old-sha",
        old_media_size=10,
        new_media_sha256="new-sha",
        new_media_size=20,
        status_summary=status,
        created_at_ms=operation_id,
        undone_at_ms=None,
        expired_at_ms=None,
    )
