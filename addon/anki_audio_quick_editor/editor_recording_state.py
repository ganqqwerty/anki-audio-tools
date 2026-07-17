"""Per-editor recorder projections and finalized take accessors."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from .recorder.model import LearnerTake, RecordingAttempt

RecorderProjectionStatus = Literal[
    "idle",
    "starting",
    "recording",
    "stopping",
    "finalizing",
    "analyzing",
    "failed",
]


@dataclass(frozen=True)
class RecorderProjection:
    """Read-only editor projection of the application recorder service."""

    status: RecorderProjectionStatus = "idle"
    attempt_id: int | None = None
    field_index: int | None = None
    source_filename: str | None = None
    backend_media_generation: int | None = None
    target_duration_ms: int | None = None
    start_cursor_ms: int = 0
    failure_message: str | None = None


def projection_for_attempt(
    attempt: RecordingAttempt,
    status: RecorderProjectionStatus,
    *,
    failure_message: str | None = None,
) -> RecorderProjection:
    """Build a frontend-safe projection from an authoritative attempt."""
    return RecorderProjection(
        status=status,
        attempt_id=int(attempt.attempt_id),
        field_index=attempt.target.field_index,
        source_filename=attempt.target.source_filename,
        backend_media_generation=int(attempt.target.backend_media_generation),
        target_duration_ms=attempt.capture.target_duration_ms,
        start_cursor_ms=attempt.capture.timeline_anchor_ms,
        failure_message=failure_message,
    )


def clear_recorder_projection(session: Any) -> RecorderProjection:
    """Clear only the editor projection; resource cancellation belongs to the service."""
    session.recorder = RecorderProjection()
    session.learner_take = None
    cleared: RecorderProjection = session.recorder
    return cleared


def ready_learner_recording_media_path(session: Any | None) -> Path | None:
    """Return the finalized learner take path while the source-scoped take exists."""
    if session is None:
        return None
    take: LearnerTake | None = session.learner_take
    if take is None or not take.finalized_media.path.is_file():
        return None
    return take.finalized_media.path


def recorder_projection_is_current(
    session: Any,
    *,
    attempt_id: int,
    field_index: int,
    source_filename: str,
) -> bool:
    """Return whether a callback still targets the current editor projection."""
    state: RecorderProjection = session.recorder
    return bool(
        state.attempt_id == attempt_id
        and state.field_index == field_index
        and state.source_filename == source_filename
    )
