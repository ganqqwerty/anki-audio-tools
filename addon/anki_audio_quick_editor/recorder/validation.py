"""Pure recorder-state invariant validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .model import Analyzing, RecorderState, state_attempt


@dataclass(frozen=True)
class RecorderViolation:
    invariant_id: Literal["R-01", "R-04"]
    message: str


def validate_recorder_state(state: RecorderState) -> tuple[RecorderViolation, ...]:
    """Return stable invariant violations for an otherwise typed state."""
    attempt = state_attempt(state)
    if attempt is not None and (
        attempt.capture.target_duration_ms <= 0 or attempt.capture.timeline_anchor_ms < 0
    ):
        return (RecorderViolation("R-01", "recording attempt has invalid capture coordinates"),)
    if isinstance(state, Analyzing) and (
        state.media.duration_ms <= 0
        or not state.media.filename
        or not state.media.format
        or state.media.path.name != state.media.filename
    ):
        return (RecorderViolation("R-04", "finalized learner media is incomplete"),)
    return ()
