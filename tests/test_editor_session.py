"""Characterization tests for EditorSession invariants.

These tests lock down current behavior before refactoring (P6).
They exercise mutation patterns through the real API surface.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from anki_audio_quick_editor.audio_state import AudioEditState
from anki_audio_quick_editor.editor_analysis import (
    begin_field_analysis,
    end_field_analysis,
)
from anki_audio_quick_editor.editor_processing import (
    _replace_standard_render_session_state,
)
from anki_audio_quick_editor.editor_processing_shared import (
    cancel_graph_analysis_for_processing,
)
from anki_audio_quick_editor.editor_session import (
    AnalysisState,
    EditorSession,
    GraphVisualizationState,
    PlaybackState,
    PostEditPlaybackState,
    ProcessingState,
    begin_processing_guard,
    invalidate_processing_guard,
    is_current_processing_guard,
    reset_for_note_load,
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


# ---------------------------------------------------------------------------
# 4. Analysis busy invariant (D1)
# ---------------------------------------------------------------------------

def test_begin_field_analysis_marks_busy() -> None:
    session = EditorSession()

    begin_field_analysis(session, 0, "file.mp3")

    assert session.analysis.busy is True
    assert 0 in session.analysis.busy_fields


def test_analysis_busy_with_two_active_fields() -> None:
    session = EditorSession()

    begin_field_analysis(session, 0, "file0.mp3")
    begin_field_analysis(session, 1, "file1.mp3")

    assert session.analysis.busy is True
    assert session.analysis.busy_fields == {0, 1}


def test_end_field_analysis_one_field_still_busy() -> None:
    session = EditorSession()
    begin_field_analysis(session, 0, "file0.mp3")
    begin_field_analysis(session, 1, "file1.mp3")

    end_field_analysis(session, 0)

    assert session.analysis.busy is True
    assert session.analysis.busy_fields == {1}


def test_end_all_field_analysis_clears_busy() -> None:
    session = EditorSession()
    begin_field_analysis(session, 0, "file0.mp3")
    begin_field_analysis(session, 1, "file1.mp3")

    end_field_analysis(session, 0)
    end_field_analysis(session, 1)

    assert session.analysis.busy is False
    assert session.analysis.busy_fields == set()


def test_cancel_graph_analysis_for_processing_clears_all() -> None:
    session = EditorSession()
    begin_field_analysis(session, 0, "file0.mp3")
    begin_field_analysis(session, 1, "file1.mp3")

    deps = MagicMock()
    cancel_graph_analysis_for_processing(MagicMock(), session, deps)

    assert session.analysis.busy is False
    assert session.analysis.busy_fields == set()
    assert session.analysis.generations_by_field == {}


# ---------------------------------------------------------------------------
# 9. Note load reset
# ---------------------------------------------------------------------------

def test_note_load_reset_clears_all_fields() -> None:
    session = EditorSession(
        note_id=10,
        state=AudioEditState("source.mp3", left_trim_ms=100),
        field_index=2,
        current_filename="generated.mp3",
        source_mtime_ns=123,
        cursor_ms=450,
        processing=ProcessingState(active=True, generation=2, next_status_summary="pending"),
        analysis=AnalysisState(
            busy=True,
            busy_fields={2},
            generation=3,
            generations_by_field={2: 3},
            graph_active_fields={2},
        ),
        graph=GraphVisualizationState(
            visualized_filename="generated.mp3",
            visualized_duration_ms=1200,
            filenames_by_field={2: "generated.mp3"},
            durations_by_field={2: 1200},
        ),
        playback=PlaybackState(
            active=True,
            paused=True,
            preparing=True,
            preserve_status=True,
            generation=4,
            temp_path=Path("/tmp/playback.mp3"),
        ),
        post_edit_playback=PostEditPlaybackState(
            generation=5,
            pending_field_index=2,
            pending_generation=3,
            pending_requires_graph_redraw=True,
            pending_source_filename="generated.mp3",
        ),
        status_summary="current",
    )
    session.undo_history.push(AudioEditState("old.mp3"), "old.mp3")
    session.redo_history.push(AudioEditState("redo.mp3"), "redo.mp3")

    result = reset_for_note_load(session, note_id=11)

    assert result is True
    assert session.note_id == 11
    assert session.state is None
    assert session.field_index is None
    assert session.current_filename is None
    assert session.processing.active is False
    assert session.analysis.busy is False
    assert session.analysis.busy_fields == set()
    assert session.source_mtime_ns is None
    assert session.cursor_ms == 0
    assert session.processing.generation == 3
    assert session.analysis.generation == 4
    assert session.analysis.generations_by_field == {}
    assert session.analysis.graph_active_fields == set()
    assert session.graph.visualized_filename is None
    assert session.graph.visualized_duration_ms is None
    assert session.graph.filenames_by_field == {}
    assert session.graph.durations_by_field == {}
    assert session.playback.active is False
    assert session.playback.paused is False
    assert session.playback.preparing is False
    assert session.playback.generation == 4
    assert session.post_edit_playback.generation == 6
    assert session.post_edit_playback.pending_field_index is None
    assert session.post_edit_playback.pending_generation is None
    assert session.post_edit_playback.pending_requires_graph_redraw is False
    assert session.post_edit_playback.pending_source_filename is None
    assert session.processing.next_status_summary == ""
    assert session.status_summary == ""
    assert session.pending_status is None
    assert session.undo_history.pop() is None
    assert session.redo_history.pop() is None
    assert session.learner_recording.status == "idle"
    assert session.learner_recording.generation == 1
    assert session.learner_recording.media_path is None
    assert session.learner_recording_controller is None


# ---------------------------------------------------------------------------
# 10. Runtime invariant assertions
# ---------------------------------------------------------------------------

def test_invariant_assertion_fires_on_processing_playback_conflict() -> None:
    session = EditorSession()
    session.processing.active = True
    session.playback.active = True
    try:
        session._assert_invariants()
        pytest.fail("Expected AssertionError")
    except AssertionError as exc:
        assert "X1 violated" in str(exc)


def test_invariant_assertion_passes_for_clean_session() -> None:
    session = EditorSession()
    session._assert_invariants()  # Should not raise


def test_note_load_reset_returns_false_for_same_note() -> None:
    session = EditorSession(note_id=10, state=AudioEditState("source.mp3"))

    result = reset_for_note_load(session, note_id=10)

    assert result is False
    assert session.state == AudioEditState("source.mp3")
