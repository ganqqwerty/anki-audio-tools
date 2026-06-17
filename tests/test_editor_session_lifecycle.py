"""Characterization tests for EditorSession lifecycle invariants.

Covers processing-playback mutual exclusion, playback lifecycle,
learner recording lifecycle, and graph active fields accumulation.
"""

from __future__ import annotations

from pathlib import Path

from anki_audio_quick_editor.audio_state import AudioEditState
from anki_audio_quick_editor.editor_analysis import begin_field_analysis
from anki_audio_quick_editor.editor_processing import (
    _replace_standard_render_session_state,
)
from anki_audio_quick_editor.editor_runtime import is_busy as _is_busy
from anki_audio_quick_editor.editor_runtime import stop_session_playback
from anki_audio_quick_editor.editor_session import (
    AnalysisState,
    EditorSession,
    PlaybackState,
    ProcessingState,
    begin_learner_recording_state,
    clear_learner_recording_state,
    learner_recording_is_current,
    reset_for_note_load,
)

# ---------------------------------------------------------------------------
# Processing-playback mutual exclusion (X1, X2)
# ---------------------------------------------------------------------------

def test_is_busy_true_when_processing() -> None:
    session = EditorSession(processing=ProcessingState(active=True))
    assert _is_busy(session) is True


def test_is_busy_false_when_only_playback_active() -> None:
    session = EditorSession(playback=PlaybackState(active=True))
    assert _is_busy(session) is False


def test_is_busy_true_when_playback_preparing() -> None:
    session = EditorSession(playback=PlaybackState(preparing=True))
    assert _is_busy(session) is True


def test_is_busy_true_when_analysis_busy() -> None:
    session = EditorSession(analysis=AnalysisState(busy_fields={0}))
    assert _is_busy(session) is True


def test_is_busy_false_for_default_session() -> None:
    session = EditorSession()
    assert _is_busy(session) is False


def test_replace_standard_render_clears_playback_flags() -> None:
    session = EditorSession(
        state=AudioEditState("source.mp3"),
        current_filename="source.mp3",
        processing=ProcessingState(active=True),
        playback=PlaybackState(active=True, paused=True),
    )

    _replace_standard_render_session_state(
        session, field_index=0, saved_name="output.mp3",
        updated_state=AudioEditState("output.mp3"),
    )

    assert session.playback.active is False
    assert session.playback.paused is False
    assert session.processing.active is False


# ---------------------------------------------------------------------------
# Playback lifecycle (D4)
# ---------------------------------------------------------------------------

def test_stop_session_playback_bumps_generation(monkeypatch) -> None:
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_runtime.cleanup_temp_playback",
        lambda session: setattr(session.playback, "temp_path", None),
    )
    session = EditorSession(playback=PlaybackState(active=True, generation=0))

    stop_session_playback(session)

    assert session.playback.generation == 1
    assert session.playback.active is False
    assert session.playback.paused is False
    assert session.playback.preparing is False


def test_playback_generation_is_monotonically_increasing(monkeypatch) -> None:
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_runtime.cleanup_temp_playback",
        lambda session: setattr(session.playback, "temp_path", None),
    )
    session = EditorSession(playback=PlaybackState(active=True, generation=0))

    stop_session_playback(session)
    stop_session_playback(session)
    stop_session_playback(session)

    assert session.playback.generation == 3


# ---------------------------------------------------------------------------
# Learner recording lifecycle (D3)
# ---------------------------------------------------------------------------

def test_begin_learner_recording_state_bumps_generation() -> None:
    session = EditorSession()

    state = begin_learner_recording_state(
        session,
        field_index=0,
        source_filename="source.mp3",
        target_duration_ms=5000,
        media_filename="recording.mp3",
        media_path=Path("/tmp/recording.mp3"),
    )

    assert state.generation == 1
    assert state.status == "recording"
    assert session.learner_recording.generation == 1


def test_clear_learner_recording_state_bumps_generation() -> None:
    session = EditorSession()
    begin_learner_recording_state(
        session,
        field_index=0,
        source_filename="source.mp3",
        target_duration_ms=5000,
        media_filename="recording.mp3",
        media_path=Path("/tmp/recording.mp3"),
    )

    cleared = clear_learner_recording_state(session)

    assert cleared.generation == 2
    assert cleared.status == "idle"
    assert session.learner_recording.generation == 2


def test_learner_recording_generation_is_monotonically_increasing() -> None:
    session = EditorSession()

    begin_learner_recording_state(
        session,
        field_index=0,
        source_filename="source.mp3",
        target_duration_ms=5000,
        media_filename="recording.mp3",
        media_path=Path("/tmp/recording.mp3"),
    )
    clear_learner_recording_state(session)
    begin_learner_recording_state(
        session,
        field_index=1,
        source_filename="source2.mp3",
        target_duration_ms=3000,
        media_filename="recording2.mp3",
        media_path=Path("/tmp/recording2.mp3"),
    )

    assert session.learner_recording.generation == 3


def test_learner_recording_is_current_matches_params() -> None:
    session = EditorSession()
    begin_learner_recording_state(
        session,
        field_index=0,
        source_filename="source.mp3",
        target_duration_ms=5000,
        media_filename="recording.mp3",
        media_path=Path("/tmp/recording.mp3"),
    )

    assert learner_recording_is_current(
        session, generation=1, field_index=0, source_filename="source.mp3"
    ) is True


def test_learner_recording_is_current_mismatched_generation() -> None:
    session = EditorSession()
    begin_learner_recording_state(
        session,
        field_index=0,
        source_filename="source.mp3",
        target_duration_ms=5000,
        media_filename="recording.mp3",
        media_path=Path("/tmp/recording.mp3"),
    )

    assert learner_recording_is_current(
        session, generation=99, field_index=0, source_filename="source.mp3"
    ) is False


def test_learner_recording_is_current_mismatched_source() -> None:
    session = EditorSession()
    begin_learner_recording_state(
        session,
        field_index=0,
        source_filename="source.mp3",
        target_duration_ms=5000,
        media_filename="recording.mp3",
        media_path=Path("/tmp/recording.mp3"),
    )

    assert learner_recording_is_current(
        session, generation=1, field_index=0, source_filename="other.mp3"
    ) is False


# ---------------------------------------------------------------------------
# Graph active fields accumulation (D5)
# ---------------------------------------------------------------------------

def test_graph_active_fields_accumulate_across_analyses() -> None:
    session = EditorSession()

    begin_field_analysis(session, 0, "file0.mp3")
    begin_field_analysis(session, 1, "file1.mp3")

    assert session.analysis.graph_active_fields == {0, 1}


def test_graph_active_fields_cleared_on_note_load() -> None:
    session = EditorSession(note_id=10)
    begin_field_analysis(session, 0, "file0.mp3")
    begin_field_analysis(session, 1, "file1.mp3")

    reset_for_note_load(session, note_id=11)

    assert session.analysis.graph_active_fields == set()


def test_graph_active_fields_re_added_after_note_load() -> None:
    session = EditorSession(note_id=10)
    begin_field_analysis(session, 0, "file0.mp3")
    reset_for_note_load(session, note_id=11)

    begin_field_analysis(session, 0, "file0.mp3")

    assert session.analysis.graph_active_fields == {0}
