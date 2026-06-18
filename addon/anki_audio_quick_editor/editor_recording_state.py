"""Learner recording state helpers for inline editor sessions."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Literal, cast

LearnerRecordingStatus = Literal["idle", "recording", "stopping", "analyzing", "ready", "failed"]
LearnerPlaybackStatus = Literal["stopped", "playing", "paused"]


@dataclass(frozen=True)
class LearnerRecordingState:
    """Learner recording attempt state owned by Python."""

    status: LearnerRecordingStatus = "idle"
    field_index: int | None = None
    generation: int = 0
    source_filename: str | None = None
    media_filename: str | None = None
    media_path: Path | None = None
    target_duration_ms: int | None = None
    start_cursor_ms: int = 0
    recording_started_at_monotonic: float | None = None
    recording_duration_ms: int | None = None
    playback_status: LearnerPlaybackStatus = "stopped"
    playback_position_ms: int = 0
    playback_started_at_monotonic: float | None = None
    playback_generation: int = 0
    prosody_payload: dict[str, object] | None = None
    failure_message: str | None = None
    graph_settings: dict[str, object] | None = None


def begin_learner_recording_state(
    session: Any,
    *,
    field_index: int,
    source_filename: str,
    target_duration_ms: int,
    media_filename: str,
    media_path: Path,
    start_cursor_ms: int = 0,
    graph_settings: dict[str, object] | None = None,
    started_at: float | None = None,
) -> LearnerRecordingState:
    """Start a new learner recording generation."""
    generation = session.learner_recording.generation + 1
    state = LearnerRecordingState(
        status="recording",
        field_index=field_index,
        generation=generation,
        source_filename=source_filename,
        media_filename=media_filename,
        media_path=media_path,
        target_duration_ms=target_duration_ms,
        start_cursor_ms=start_cursor_ms,
        recording_started_at_monotonic=started_at,
        graph_settings=graph_settings,
    )
    session.learner_recording = state
    return state


def clear_learner_recording_state(session: Any) -> LearnerRecordingState:
    """Clear learner recording state and invalidate pending callbacks."""
    state = LearnerRecordingState(generation=session.learner_recording.generation + 1)
    session.learner_recording = state
    session.learner_recording_controller = None
    return state


def reset_learner_playback_state(session: Any) -> LearnerRecordingState:
    """Stop tracked learner playback without clearing the recording sidecar."""
    state = cast(LearnerRecordingState, session.learner_recording)
    if (
        state.playback_status == "stopped"
        and state.playback_position_ms == 0
        and state.playback_started_at_monotonic is None
    ):
        return state
    next_state = replace(
        state,
        playback_status="stopped",
        playback_position_ms=0,
        playback_started_at_monotonic=None,
        playback_generation=state.playback_generation + 1,
    )
    session.learner_recording = next_state
    return next_state


def ready_learner_recording_media_path(session: Any | None) -> Path | None:
    """Return the ready learner recording media path when its sidecar still exists."""
    if session is None:
        return None
    state = session.learner_recording
    media_path = cast(Path | None, state.media_path)
    if state.status != "ready" or media_path is None or not media_path.is_file():
        return None
    return media_path


def learner_recording_is_current(
    session: Any,
    *,
    generation: int,
    field_index: int,
    source_filename: str,
) -> bool:
    """Return whether a learner recording callback still matches the active attempt."""
    state = cast(LearnerRecordingState, session.learner_recording)
    return bool(
        state.generation == generation
        and state.field_index == field_index
        and state.source_filename == source_filename
    )
