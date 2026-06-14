from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.editor_history import undo
from anki_audio_quick_editor.editor_session import (
    AudioEditState,
    EditorSession,
    UndoEntry,
    begin_processing_guard,
    invalidate_processing_guard,
    is_current_processing_guard,
    reset_for_note_load,
)


def test_undo_during_busy_processing_is_blocked_and_shows_processing_status() -> None:
    editor = SimpleNamespace(currentField=0, web=MagicMock(), note=SimpleNamespace(fields=[]))
    session = EditorSession(
        state=AudioEditState("clip.mp3"),
        field_index=0,
        current_filename="clip.mp3",
    )
    entry = UndoEntry(AudioEditState("clip.mp3", speed=2.0), "generated.mp3")
    session.undo_history.push(entry.state, entry.filename, status_summary=entry.status_summary)

    deps = MagicMock()
    deps.session_and_source.return_value = (session, "clip.mp3")
    deps.is_busy.return_value = True
    deps.still_processing_message = "Still processing. Please wait."
    deps.restore_persistent_undo = MagicMock()
    deps.restore_history_entry = MagicMock()
    deps.eval_status = MagicMock()

    undo(editor, deps)

    deps.eval_status.assert_called_once_with(
        editor,
        "Still processing. Please wait.",
        kind="processing",
    )
    assert session.undo_history.entries == [entry]
    deps.restore_persistent_undo.assert_not_called()
    deps.restore_history_entry.assert_not_called()


def test_processing_guard_matches_only_current_generation_note_field_and_source() -> None:
    session = EditorSession(note_id=10, field_index=1, current_filename="clip.mp3")

    guard = begin_processing_guard(session, field_index=1, source_filename="clip.mp3")

    assert is_current_processing_guard(session, guard)
    session.field_index = 2
    assert not is_current_processing_guard(session, guard)
    session.field_index = 1
    session.current_filename = "other.mp3"
    assert not is_current_processing_guard(session, guard)


def test_processing_guard_does_not_rewrite_current_filename() -> None:
    session = EditorSession(note_id=10, field_index=0, current_filename="generated.mp3")

    guard = begin_processing_guard(session, field_index=0, source_filename="source.mp3")

    assert session.current_filename == "generated.mp3"
    assert not is_current_processing_guard(session, guard)


def test_processing_guard_is_invalidated_by_note_load() -> None:
    session = EditorSession(note_id=10, field_index=0, current_filename="clip.mp3")
    guard = begin_processing_guard(session, field_index=0, source_filename="clip.mp3")

    reset_for_note_load(session, note_id=11)

    assert not is_current_processing_guard(session, guard)


def test_processing_guard_can_be_invalidated_without_note_change() -> None:
    session = EditorSession(note_id=10, field_index=0, current_filename="clip.mp3")
    guard = begin_processing_guard(session, field_index=0, source_filename="clip.mp3")

    invalidate_processing_guard(session)

    assert not is_current_processing_guard(session, guard)
