"""Tests for EditorSession analysis busy invariant and note load reset."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from anki_audio_quick_editor.audio_state import AudioEditState
from anki_audio_quick_editor.editor_analysis import (
    begin_field_analysis,
    end_field_analysis,
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
    reset_for_note_load,
)

# ---------------------------------------------------------------------------
# 1. Analysis busy invariant (D1)
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
# 2. Note load reset
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
# 3. Runtime invariant assertions
# ---------------------------------------------------------------------------

def test_invariant_assertion_fires_on_processing_playback_conflict() -> None:
    import pytest

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
