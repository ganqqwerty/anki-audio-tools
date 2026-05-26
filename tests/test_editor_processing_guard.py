from __future__ import annotations

from anki_audio_quick_editor.editor_session import (
    EditorSession,
    begin_processing_guard,
    invalidate_processing_guard,
    is_current_processing_guard,
    reset_for_note_load,
)


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
