"""Pure recorder lifecycle model with attempt-scoped facts and effects."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, NewType

RecordingAttemptId = NewType("RecordingAttemptId", int)
BackendMediaGeneration = NewType("BackendMediaGeneration", int)
LearnerTakeId = NewType("LearnerTakeId", int)
OutputOwnership = Literal["attempt_temp", "unpublished_media", "published_media"]


@dataclass(frozen=True)
class RecorderTarget:
    """Authoritative backend target captured by one recording attempt."""

    editor_session_id: int
    note_id: int | None
    field_index: int
    source_filename: str
    backend_media_generation: BackendMediaGeneration


@dataclass(frozen=True)
class CaptureSpec:
    """Capture settings and attempt-owned output destination."""

    output_filename: str
    output_path: Path
    target_duration_ms: int
    timeline_anchor_ms: int
    graph_settings: dict[str, object] | None = None


@dataclass(frozen=True)
class RecordingAttempt:
    attempt_id: RecordingAttemptId
    target: RecorderTarget
    capture: CaptureSpec


@dataclass(frozen=True)
class FinalizedMedia:
    path: Path
    filename: str
    format: str
    duration_ms: int
    ownership: OutputOwnership


@dataclass(frozen=True)
class LearnerTake:
    take_id: LearnerTakeId
    attempt_id: RecordingAttemptId
    origin: RecorderTarget
    finalized_media: FinalizedMedia
    timeline_anchor_ms: int
    target_duration_ms: int
    analysis_payload: dict[str, object]


@dataclass(frozen=True)
class Idle:
    kind: Literal["idle"] = "idle"


@dataclass(frozen=True)
class Starting:
    attempt: RecordingAttempt
    kind: Literal["starting"] = "starting"


@dataclass(frozen=True)
class Recording:
    attempt: RecordingAttempt
    kind: Literal["recording"] = "recording"


@dataclass(frozen=True)
class Stopping:
    attempt: RecordingAttempt
    kind: Literal["stopping"] = "stopping"


@dataclass(frozen=True)
class Finalizing:
    attempt: RecordingAttempt
    capture_path: Path
    duration_ms: int | None
    kind: Literal["finalizing"] = "finalizing"


@dataclass(frozen=True)
class Analyzing:
    attempt: RecordingAttempt
    media: FinalizedMedia
    kind: Literal["analyzing"] = "analyzing"


@dataclass(frozen=True)
class Failed:
    attempt_id: RecordingAttemptId
    target: RecorderTarget
    message: str
    kind: Literal["failed"] = "failed"


RecorderState = Idle | Starting | Recording | Stopping | Finalizing | Analyzing | Failed


@dataclass(frozen=True)
class StartRequested:
    attempt: RecordingAttempt


@dataclass(frozen=True)
class Started:
    attempt_id: RecordingAttemptId


@dataclass(frozen=True)
class StopRequested:
    pass


@dataclass(frozen=True)
class CaptureCompleted:
    attempt_id: RecordingAttemptId
    path: Path
    duration_ms: int | None


@dataclass(frozen=True)
class PersistenceCompleted:
    attempt_id: RecordingAttemptId
    media: FinalizedMedia


@dataclass(frozen=True)
class AnalysisCompleted:
    attempt_id: RecordingAttemptId


@dataclass(frozen=True)
class RecorderFailure:
    attempt_id: RecordingAttemptId
    message: str


@dataclass(frozen=True)
class CancelRequested:
    reason: str


RecorderFact = (
    StartRequested
    | Started
    | StopRequested
    | CaptureCompleted
    | PersistenceCompleted
    | AnalysisCompleted
    | RecorderFailure
    | CancelRequested
)

RecorderEffectType = Literal[
    "start_capture",
    "stop_capture",
    "cancel_capture",
    "dispose_capture",
    "persist",
    "analyze",
    "store_take",
    "cleanup_unpublished",
    "publish",
]


@dataclass(frozen=True)
class RecorderEffect:
    type: RecorderEffectType
    attempt_id: RecordingAttemptId | None = None
    reason: str | None = None


@dataclass(frozen=True)
class RecorderTransition:
    state: RecorderState
    effects: tuple[RecorderEffect, ...] = ()


def reduce_recorder(state: RecorderState, fact: RecorderFact) -> RecorderTransition:
    """Reduce one recorder fact without executing external side effects."""
    if isinstance(fact, StartRequested):
        return _start_transition(state, fact)
    if isinstance(fact, Started):
        return _started_transition(state, fact)
    if isinstance(fact, StopRequested):
        return _stop_transition(state)
    if isinstance(fact, CaptureCompleted):
        return _capture_transition(state, fact)
    if isinstance(fact, PersistenceCompleted):
        return _persistence_transition(state, fact)
    if isinstance(fact, AnalysisCompleted):
        return _analysis_transition(state, fact)
    if isinstance(fact, RecorderFailure):
        return _failure_transition(state, fact)
    return _cancel_transition(state, fact)


def _start_transition(state: RecorderState, fact: StartRequested) -> RecorderTransition:
    if isinstance(state, (Idle, Failed)):
        return RecorderTransition(
            Starting(fact.attempt),
            (_effect("start_capture", fact.attempt.attempt_id), _effect("publish")),
        )
    return RecorderTransition(state)


def _started_transition(state: RecorderState, fact: Started) -> RecorderTransition:
    if isinstance(state, Starting) and _matches(state, fact.attempt_id):
        return RecorderTransition(Recording(state.attempt), (_effect("publish"),))
    return RecorderTransition(state)


def _stop_transition(state: RecorderState) -> RecorderTransition:
    if isinstance(state, Recording):
        return RecorderTransition(
            Stopping(state.attempt),
            (_effect("stop_capture", state.attempt.attempt_id), _effect("publish")),
        )
    return RecorderTransition(state)


def _capture_transition(state: RecorderState, fact: CaptureCompleted) -> RecorderTransition:
    if isinstance(state, Stopping) and _matches(state, fact.attempt_id):
        return RecorderTransition(
            Finalizing(state.attempt, fact.path, fact.duration_ms),
            (
                _effect("dispose_capture", fact.attempt_id),
                _effect("persist", fact.attempt_id),
                _effect("publish"),
            ),
        )
    return RecorderTransition(state)


def _persistence_transition(
    state: RecorderState,
    fact: PersistenceCompleted,
) -> RecorderTransition:
    if isinstance(state, Finalizing) and _matches(state, fact.attempt_id):
        return RecorderTransition(
            Analyzing(state.attempt, fact.media),
            (_effect("analyze", fact.attempt_id), _effect("publish")),
        )
    return RecorderTransition(state)


def _analysis_transition(state: RecorderState, fact: AnalysisCompleted) -> RecorderTransition:
    if isinstance(state, Analyzing) and _matches(state, fact.attempt_id):
        return RecorderTransition(
            Idle(),
            (_effect("store_take", fact.attempt_id), _effect("publish")),
        )
    return RecorderTransition(state)


def _failure_transition(state: RecorderState, fact: RecorderFailure) -> RecorderTransition:
    attempt = _attempt_for(state) if _matches(state, fact.attempt_id) else None
    if attempt is None:
        return RecorderTransition(state)
    effects = _terminal_effects(state, fact.attempt_id)
    return RecorderTransition(
        Failed(fact.attempt_id, attempt.target, fact.message),
        (*effects, _effect("publish")),
    )


def _cancel_transition(state: RecorderState, fact: CancelRequested) -> RecorderTransition:
    attempt = _attempt_for(state)
    if attempt is None:
        return RecorderTransition(state)
    effects = _terminal_effects(state, attempt.attempt_id, fact.reason)
    return RecorderTransition(Idle(), (*effects, _effect("publish")))


def _terminal_effects(
    state: RecorderState,
    attempt_id: RecordingAttemptId,
    reason: str | None = None,
) -> tuple[RecorderEffect, ...]:
    if isinstance(state, (Starting, Recording, Stopping)):
        return (
            RecorderEffect("cancel_capture", attempt_id, reason),
            _effect("dispose_capture", attempt_id),
        )
    if isinstance(state, (Finalizing, Analyzing)):
        return (_effect("cleanup_unpublished", attempt_id),)
    return ()


def state_attempt(state: RecorderState) -> RecordingAttempt | None:
    """Return the attempt owned by an active lifecycle state."""
    return _attempt_for(state)


def state_owns_handle(state: RecorderState) -> bool:
    return isinstance(state, (Starting, Recording, Stopping))


def _attempt_for(state: RecorderState) -> RecordingAttempt | None:
    if isinstance(state, (Starting, Recording, Stopping, Finalizing, Analyzing)):
        return state.attempt
    return None


def _matches(state: RecorderState, attempt_id: RecordingAttemptId) -> bool:
    attempt = _attempt_for(state)
    return attempt is not None and attempt.attempt_id == attempt_id


def _effect(
    effect_type: RecorderEffectType,
    attempt_id: RecordingAttemptId | None = None,
) -> RecorderEffect:
    return RecorderEffect(effect_type, attempt_id)
