"""Characterization tests for EditorSession invariants.

These tests lock down current behavior before refactoring (P6).
They exercise mutation patterns through the real API surface.
"""

from __future__ import annotations

from anki_audio_quick_editor.audio_state import AudioEditState
from anki_audio_quick_editor.editor_processing import (
    _replace_standard_render_session_state,
)
from anki_audio_quick_editor.editor_session import (
    EditorSession,
    PlaybackState,
    PostEditPlaybackState,
    ProcessingState,
    begin_processing_guard,
    invalidate_processing_guard,
    is_current_processing_guard,
)

# ---------------------------------------------------------------------------
# 1. Processing lifecycle (X1, X4, X5, X6)
# ---------------------------------------------------------------------------

def test_replace_standard_render_clears_processing_and_playback() -> None:
    session = EditorSession(
        state=AudioEditState("source.mp3"),
        current_filename="source.mp3",
        status_summary="original",
        processing=ProcessingState(active=True),
        playback=PlaybackState(active=True, paused=True),
    )
    session.redo_history.push(AudioEditState("old.mp3"), "old.mp3")

    _replace_standard_render_session_state(
        session, field_index=0, saved_name="output.mp3",
        updated_state=AudioEditState("output.mp3"),
    )

    assert session.processing.active is False
    assert session.playback.active is False
    assert session.playback.paused is False
    assert session.cursor_ms == 0


def test_replace_standard_render_pushes_undo_entry() -> None:
    session = EditorSession(
        state=AudioEditState("source.mp3"),
        current_filename="source.mp3",
        status_summary="original",
        processing=ProcessingState(active=True),
    )

    _replace_standard_render_session_state(
        session, field_index=0, saved_name="output.mp3",
        updated_state=AudioEditState("output.mp3"),
    )

    assert len(session.undo_history.entries) == 1
    entry = session.undo_history.entries[0]
    assert entry.state == AudioEditState("source.mp3")
    assert entry.filename == "source.mp3"
    assert entry.status_summary == "original"


def test_replace_standard_render_clears_redo_on_new_edit() -> None:
    session = EditorSession(
        state=AudioEditState("source.mp3"),
        current_filename="source.mp3",
        status_summary="original",
        processing=ProcessingState(active=True),
    )
    session.redo_history.push(AudioEditState("redo.mp3"), "redo.mp3")
    session.redo_history.push(AudioEditState("redo2.mp3"), "redo2.mp3")

    _replace_standard_render_session_state(
        session, field_index=0, saved_name="output.mp3",
        updated_state=AudioEditState("output.mp3"),
    )

    assert session.redo_history.pop() is None


def test_replace_standard_render_bumps_post_edit_generation() -> None:
    session = EditorSession(
        state=AudioEditState("source.mp3"),
        current_filename="source.mp3",
        processing=ProcessingState(active=True),
        post_edit_playback=PostEditPlaybackState(generation=10),
    )

    _replace_standard_render_session_state(
        session, field_index=0, saved_name="output.mp3",
        updated_state=AudioEditState("output.mp3"),
    )

    assert session.post_edit_playback.generation == 11


def test_replace_standard_render_uses_next_status_summary_when_set() -> None:
    session = EditorSession(
        state=AudioEditState("source.mp3"),
        current_filename="source.mp3",
        status_summary="original",
        processing=ProcessingState(next_status_summary="pending status", active=True),
    )

    _replace_standard_render_session_state(
        session, field_index=0, saved_name="output.mp3",
        updated_state=AudioEditState("output.mp3"),
    )

    assert session.status_summary == "pending status"
    assert session.processing.next_status_summary == ""


def test_replace_standard_render_falls_back_to_status_summary() -> None:
    session = EditorSession(
        state=AudioEditState("source.mp3"),
        current_filename="source.mp3",
        status_summary="original",
        processing=ProcessingState(active=True),
    )

    _replace_standard_render_session_state(
        session, field_index=0, saved_name="output.mp3",
        updated_state=AudioEditState("output.mp3"),
    )

    assert session.status_summary == "original"


# ---------------------------------------------------------------------------
# 2. Undo/redo roundtrip (X4, X5)
# ---------------------------------------------------------------------------

def test_undo_redo_roundtrip() -> None:
    session = EditorSession(
        state=AudioEditState("a.mp3"),
        current_filename="a.mp3",
        status_summary="statusA",
    )

    state_a = session.state
    filename_a = session.current_filename
    status_a = session.status_summary

    session.undo_history.push(state_a, filename_a, status_summary=status_a)
    session.state = AudioEditState("b.mp3")
    session.current_filename = "b.mp3"
    session.status_summary = "statusB"

    state_b = session.state
    filename_b = session.current_filename
    status_b = session.status_summary

    session.undo_history.push(state_b, filename_b, status_summary=status_b)

    assert len(session.undo_history.entries) == 2

    entry_b = session.undo_history.pop()
    assert entry_b is not None
    assert entry_b.filename == "b.mp3"
    session.redo_history.push(entry_b.state, entry_b.filename, status_summary=entry_b.status_summary)

    entry_a = session.undo_history.pop()
    assert entry_a is not None
    assert entry_a.filename == "a.mp3"
    session.redo_history.push(entry_a.state, entry_a.filename, status_summary=entry_a.status_summary)

    assert len(session.redo_history.entries) == 2

    redo_entry = session.redo_history.pop()
    assert redo_entry is not None
    assert redo_entry.filename == "a.mp3"


def test_undo_does_not_clear_redo() -> None:
    session = EditorSession(
        state=AudioEditState("a.mp3"),
        current_filename="a.mp3",
        status_summary="statusA",
    )
    session.undo_history.push(AudioEditState("b.mp3"), "b.mp3", status_summary="statusB")
    session.redo_history.push(AudioEditState("redo.mp3"), "redo.mp3")

    entry = session.undo_history.pop()
    assert entry is not None
    session.redo_history.push(entry.state, entry.filename, status_summary=entry.status_summary)

    assert len(session.redo_history.entries) == 2


# ---------------------------------------------------------------------------
# 3. Stale guard invalidation (D2)
# ---------------------------------------------------------------------------

def test_begin_processing_guard_bumps_generation() -> None:
    session = EditorSession(note_id=10, field_index=0, current_filename="clip.mp3")

    guard = begin_processing_guard(session, field_index=0, source_filename="clip.mp3")

    assert guard.generation == 1
    assert session.processing.generation == 1


def test_invalidate_processing_guard_bumps_generation_again() -> None:
    session = EditorSession(note_id=10, field_index=0, current_filename="clip.mp3")
    guard = begin_processing_guard(session, field_index=0, source_filename="clip.mp3")
    assert guard.generation == 1

    invalidate_processing_guard(session)

    assert session.processing.generation == 2
    assert not is_current_processing_guard(session, guard)


def test_processing_generation_is_monotonically_increasing() -> None:
    session = EditorSession(note_id=10, field_index=0, current_filename="clip.mp3")

    guard1 = begin_processing_guard(session, field_index=0, source_filename="clip.mp3")
    invalidate_processing_guard(session)
    guard2 = begin_processing_guard(session, field_index=1, source_filename="clip.mp3")
    invalidate_processing_guard(session)
    guard3 = begin_processing_guard(session, field_index=0, source_filename="clip.mp3")

    assert guard1.generation < guard2.generation < guard3.generation
    assert session.processing.generation == guard3.generation
