from __future__ import annotations

from pathlib import Path

from anki_audio_quick_editor.editor_session import (
    EditorSession,
    LearnerRecordingState,
    begin_learner_recording_state,
    learner_recording_is_current,
    reset_for_note_load,
)


def test_editor_session_starts_with_idle_learner_recording_state() -> None:
    session = EditorSession()

    assert session.learner_recording == LearnerRecordingState()


def test_begin_learner_recording_state_records_field_source_duration_and_generation() -> None:
    session = EditorSession()

    state = begin_learner_recording_state(
        session,
        field_index=2,
        source_filename="target.wav",
        target_duration_ms=1234,
    )

    assert state == LearnerRecordingState(
        status="countdown",
        field_index=2,
        generation=1,
        source_filename="target.wav",
        target_duration_ms=1234,
    )
    assert session.learner_recording == state


def test_reset_for_note_load_clears_learner_recording_and_invalidates_generation() -> None:
    session = EditorSession(note_id=1)
    begin_learner_recording_state(
        session,
        field_index=0,
        source_filename="target.wav",
        target_duration_ms=2000,
    )
    session.learner_recording = LearnerRecordingState(
        status="ready",
        field_index=0,
        generation=session.learner_recording.generation,
        source_filename="target.wav",
        target_duration_ms=2000,
        media_filename="learner.wav",
        media_path=Path("/tmp/learner.wav"),
        prosody_payload={"durationMs": 2000},
    )

    changed = reset_for_note_load(session, note_id=2)

    assert changed is True
    assert session.learner_recording == LearnerRecordingState(generation=2)


def test_reset_for_same_note_keeps_learner_recording_state() -> None:
    session = EditorSession(note_id=1)
    state = begin_learner_recording_state(
        session,
        field_index=0,
        source_filename="target.wav",
        target_duration_ms=2000,
    )

    changed = reset_for_note_load(session, note_id=1)

    assert changed is False
    assert session.learner_recording == state


def test_learner_recording_is_current_rejects_stale_generation_field_or_source() -> None:
    session = EditorSession()
    state = begin_learner_recording_state(
        session,
        field_index=1,
        source_filename="target.wav",
        target_duration_ms=2000,
    )

    assert learner_recording_is_current(
        session,
        generation=state.generation,
        field_index=1,
        source_filename="target.wav",
    )
    assert not learner_recording_is_current(
        session,
        generation=state.generation - 1,
        field_index=1,
        source_filename="target.wav",
    )
    assert not learner_recording_is_current(
        session,
        generation=state.generation,
        field_index=2,
        source_filename="target.wav",
    )
    assert not learner_recording_is_current(
        session,
        generation=state.generation,
        field_index=1,
        source_filename="other.wav",
    )
