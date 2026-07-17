from __future__ import annotations

from pathlib import Path

from anki_audio_quick_editor.editor_recording_state import (
    RecorderProjection,
    clear_recorder_projection,
    projection_for_attempt,
    recorder_projection_is_current,
)
from anki_audio_quick_editor.editor_session import EditorSession, reset_for_note_load
from anki_audio_quick_editor.recorder.model import (
    BackendMediaGeneration,
    CaptureSpec,
    RecorderTarget,
    RecordingAttempt,
    RecordingAttemptId,
)


def _attempt(tmp_path: Path) -> RecordingAttempt:
    return RecordingAttempt(
        RecordingAttemptId(7),
        RecorderTarget(1, 2, 0, "target.wav", BackendMediaGeneration(4)),
        CaptureSpec("take.wav", tmp_path / "take.wav", 1000, 125),
    )


def test_projection_contains_attempt_identity_without_native_resources(tmp_path: Path) -> None:
    state = projection_for_attempt(_attempt(tmp_path), "recording")

    assert state == RecorderProjection(
        status="recording",
        attempt_id=7,
        field_index=0,
        source_filename="target.wav",
        backend_media_generation=4,
        target_duration_ms=1000,
        start_cursor_ms=125,
    )
    assert not hasattr(state, "media_path")
    assert not hasattr(state, "playback_status")


def test_clear_projection_does_not_retain_attempt_or_take(tmp_path: Path) -> None:
    session = EditorSession(recorder=projection_for_attempt(_attempt(tmp_path), "recording"))
    cleared = clear_recorder_projection(session)

    assert cleared == RecorderProjection()
    assert session.learner_take is None


def test_projection_current_check_uses_attempt_field_and_source(tmp_path: Path) -> None:
    session = EditorSession(recorder=projection_for_attempt(_attempt(tmp_path), "recording"))
    assert recorder_projection_is_current(
        session,
        attempt_id=7,
        field_index=0,
        source_filename="target.wav",
    )
    assert not recorder_projection_is_current(
        session,
        attempt_id=8,
        field_index=0,
        source_filename="target.wav",
    )


def test_note_change_clears_projection_and_advances_media_generation(tmp_path: Path) -> None:
    session = EditorSession(
        note_id=1,
        backend_media_generation=3,
        recorder=projection_for_attempt(_attempt(tmp_path), "failed"),
    )

    assert reset_for_note_load(session, note_id=2)
    assert session.recorder == RecorderProjection()
    assert session.backend_media_generation == 4
