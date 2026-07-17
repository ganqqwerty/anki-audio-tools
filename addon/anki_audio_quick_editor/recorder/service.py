"""Application-scoped recorder service and exact resource ownership."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, Callable, Protocol

from .model import (
    AnalysisCompleted,
    Analyzing,
    BackendMediaGeneration,
    CancelRequested,
    CaptureCompleted,
    CaptureSpec,
    FinalizedMedia,
    Idle,
    LearnerTake,
    LearnerTakeId,
    PersistenceCompleted,
    RecorderFailure,
    RecorderState,
    RecorderTarget,
    RecordingAttempt,
    RecordingAttemptId,
    Started,
    StartRequested,
    Stopping,
    StopRequested,
    reduce_recorder,
    state_attempt,
    state_owns_handle,
)
from .validation import RecorderViolation, validate_recorder_state


class RecorderServiceBusyError(RuntimeError):
    """Raised when a second editor tries to acquire the microphone."""


class RecorderInvariantError(RuntimeError):
    """Raised in tests when recorder resource invariants are violated."""


class RecorderController(Protocol):
    """External capture handle retained only by the recorder service."""

    def stop(
        self,
        *,
        on_completed: Callable[[Any], None],
        on_failed: Callable[[Exception], None],
    ) -> None: ...

    def cancel(self, reason: str) -> None: ...

    def dispose(self) -> None: ...


class RecorderService:
    """Serialize microphone ownership and suppress stale attempt callbacks."""

    def __init__(self) -> None:
        self.state: RecorderState = Idle()
        self._controller: RecorderController | None = None
        self._next_attempt_id = 0
        self._next_take_id = 0
        self._capture_terminal_attempts: set[RecordingAttemptId] = set()
        self._takes: dict[int, LearnerTake] = {}

    @property
    def active_attempt(self) -> RecordingAttempt | None:
        return state_attempt(self.state)

    @property
    def is_busy(self) -> bool:
        return self.active_attempt is not None

    def begin(
        self,
        target: RecorderTarget,
        capture: CaptureSpec,
        controller: RecorderController,
    ) -> RecordingAttempt:
        if self.is_busy or self._controller is not None:
            raise RecorderServiceBusyError("Another editor already owns the microphone.")
        self._next_attempt_id += 1
        attempt = RecordingAttempt(RecordingAttemptId(self._next_attempt_id), target, capture)
        self._controller = controller
        self.state = reduce_recorder(self.state, StartRequested(attempt)).state
        self._assert_valid()
        return attempt

    def mark_started(self, attempt_id: RecordingAttemptId) -> bool:
        next_state = reduce_recorder(self.state, Started(attempt_id)).state
        if next_state == self.state:
            return False
        self.state = next_state
        self._assert_valid()
        return True

    def request_stop(self, editor_session_id: int) -> RecordingAttempt | None:
        attempt = self.active_attempt
        if attempt is None or attempt.target.editor_session_id != editor_session_id:
            return None
        next_state = reduce_recorder(self.state, StopRequested()).state
        if next_state == self.state:
            return None
        self.state = next_state
        self._assert_valid()
        return attempt

    def stop_requested(
        self,
        attempt_id: RecordingAttemptId,
        *,
        on_completed: Callable[[Any], None],
        on_failed: Callable[[Exception], None],
    ) -> bool:
        """Execute a previously accepted stop without exposing the native handle."""
        attempt = self.active_attempt
        controller = self._controller
        if (
            attempt is None
            or attempt.attempt_id != attempt_id
            or not isinstance(self.state, Stopping)
            or controller is None
        ):
            return False
        controller.stop(on_completed=on_completed, on_failed=on_failed)
        return True

    def accept_capture(
        self,
        attempt_id: RecordingAttemptId,
        path: Path,
        duration_ms: int | None,
    ) -> bool:
        if attempt_id in self._capture_terminal_attempts:
            return False
        next_state = reduce_recorder(
            self.state,
            CaptureCompleted(attempt_id, path, duration_ms),
        ).state
        if next_state == self.state:
            return False
        self._capture_terminal_attempts.add(attempt_id)
        self.state = next_state
        self._dispose_controller()
        self._assert_valid()
        return True

    def mark_analyzing(
        self,
        attempt_id: RecordingAttemptId,
        media: FinalizedMedia,
    ) -> bool:
        next_state = reduce_recorder(
            self.state,
            PersistenceCompleted(attempt_id, media),
        ).state
        if next_state == self.state:
            return False
        self.state = next_state
        self._assert_valid()
        return True

    def finish_analysis(
        self,
        attempt_id: RecordingAttemptId,
        media: FinalizedMedia,
        payload: dict[str, object],
    ) -> LearnerTake | None:
        if not isinstance(self.state, Analyzing) or self.state.attempt.attempt_id != attempt_id:
            return None
        attempt = self.state.attempt
        next_state = reduce_recorder(self.state, AnalysisCompleted(attempt_id)).state
        if next_state == self.state:
            return None
        self._next_take_id += 1
        published_media = replace(media, ownership="published_media")
        take = LearnerTake(
            take_id=LearnerTakeId(self._next_take_id),
            attempt_id=attempt.attempt_id,
            origin=attempt.target,
            finalized_media=published_media,
            timeline_anchor_ms=attempt.capture.timeline_anchor_ms,
            target_duration_ms=attempt.capture.target_duration_ms,
            analysis_payload=payload,
        )
        self._takes[attempt.target.editor_session_id] = take
        self.state = next_state
        self._assert_valid()
        return take

    def fail(self, attempt_id: RecordingAttemptId, message: str) -> bool:
        next_state = reduce_recorder(self.state, RecorderFailure(attempt_id, message)).state
        if next_state == self.state:
            return False
        self.state = next_state
        self._cancel_controller("dispose")
        self._assert_valid()
        return True

    def cancel_if_owner(self, editor_session_id: int, reason: str) -> bool:
        attempt = self.active_attempt
        if attempt is None or attempt.target.editor_session_id != editor_session_id:
            return False
        self.state = reduce_recorder(self.state, CancelRequested(reason)).state
        self._cancel_controller(reason)
        self._assert_valid()
        return True

    def clear_owner(self, editor_session_id: int, reason: str) -> None:
        self.cancel_if_owner(editor_session_id, reason)
        self._takes.pop(editor_session_id, None)

    def current_take(self, editor_session_id: int) -> LearnerTake | None:
        return self._takes.get(editor_session_id)

    def discard_take(self, editor_session_id: int) -> None:
        """Forget one source-scoped take without touching recorder lifecycle state."""
        self._takes.pop(editor_session_id, None)

    def dispose(self, reason: str) -> None:
        attempt = self.active_attempt
        if attempt is not None:
            self.cancel_if_owner(attempt.target.editor_session_id, reason)
        else:
            self._cancel_controller(reason)
        self._takes.clear()
        self.state = Idle()

    def validate_resources(self) -> tuple[RecorderViolation, ...]:
        violations = list(validate_recorder_state(self.state))
        if state_owns_handle(self.state) != (self._controller is not None):
            violations.append(
                RecorderViolation("R-01", "native recorder handle does not match recorder state")
            )
        return tuple(violations)

    def _assert_valid(self) -> None:
        violations = self.validate_resources()
        if not violations:
            return
        self._cancel_controller("dispose")
        self.state = Idle()
        raise RecorderInvariantError(
            "; ".join(f"{item.invariant_id}: {item.message}" for item in violations)
        )

    def _cancel_controller(self, reason: str) -> None:
        controller = self._controller
        self._controller = None
        if controller is None:
            return
        try:
            controller.cancel(reason)
        finally:
            controller.dispose()

    def _dispose_controller(self) -> None:
        controller = self._controller
        self._controller = None
        if controller is not None:
            controller.dispose()


__all__ = [
    "BackendMediaGeneration",
    "RecorderService",
    "RecorderServiceBusyError",
]
