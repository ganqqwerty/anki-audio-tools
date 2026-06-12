from __future__ import annotations

from types import SimpleNamespace

from anki_audio_quick_editor.audio_state import AudioEditState
from anki_audio_quick_editor.editor_history_snapshot import history_snapshot_for_field
from anki_audio_quick_editor.editor_session import EditorSession, UndoHistory


def test_history_snapshot_uses_status_summaries_and_caps_items() -> None:
    session = EditorSession(field_index=0)
    for index in range(4):
        session.undo_history.push(
            AudioEditState(f"source-{index}.mp3"),
            f"source-{index}.mp3",
            status_summary=f"Operation {index}",
        )
    session.redo_history.push(AudioEditState("redo.mp3"), "redo.mp3", status_summary="")

    snapshot = history_snapshot_for_field(
        SimpleNamespace(note=SimpleNamespace(id=123)),
        field_index=0,
        session=session,
        history_size=3,
        can_persistent_undo=lambda _editor, _field_index: False,
        latest_persistent_undo_item=lambda _editor, _field_index: None,
    )

    assert snapshot == {
        "canUndo": True,
        "canRedo": True,
        "undoItems": [
            {"id": "undo:1", "label": "Operation 3"},
            {"id": "undo:2", "label": "Operation 2"},
            {"id": "undo:3", "label": "Operation 1"},
        ],
        "redoItems": [
            {"id": "redo:1", "label": "Restored edit"},
        ],
    }


def test_history_snapshot_includes_persistent_undo_when_session_empty() -> None:
    snapshot = history_snapshot_for_field(
        SimpleNamespace(note=SimpleNamespace(id=123)),
        field_index=0,
        session=EditorSession(field_index=0),
        history_size=100,
        can_persistent_undo=lambda _editor, _field_index: True,
        latest_persistent_undo_item=lambda _editor, _field_index: {
            "id": "persistent:42",
            "label": "Shorten pauses",
        },
    )

    assert snapshot["canUndo"] is True
    assert snapshot["undoItems"] == [{"id": "persistent:42", "label": "Shorten pauses"}]
    assert snapshot["redoItems"] == []


def test_undo_history_prunes_oldest_entries_to_limit() -> None:
    history = UndoHistory(max_entries=3)
    for index in range(5):
        history.push(AudioEditState(f"source-{index}.mp3"), f"source-{index}.mp3")

    assert [entry.filename for entry in history.entries] == [
        "source-2.mp3",
        "source-3.mp3",
        "source-4.mp3",
    ]
