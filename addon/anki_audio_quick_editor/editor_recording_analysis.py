"""Attempt-safe learner recording analysis publication."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .editor_recording_frontend import (
    eval_learner_recording_state,
    eval_learner_visualizer,
    learner_prosody_payload,
)
from .editor_recording_requests import LearnerRecordingRequest
from .editor_recording_state import RecorderProjection, projection_for_attempt
from .error_codes import AQE_RECORDING_FAILED, coded_error
from .prosody_types import ProsodyTrack
from .recorder.model import FinalizedMedia, RecordingAttemptId

if TYPE_CHECKING:
    from .editor_deps_protocols import RecordingDeps


def learner_recording_analysis_finished(
    editor: Any,
    attempt_id: RecordingAttemptId,
    request: LearnerRecordingRequest,
    media: FinalizedMedia,
    track: ProsodyTrack,
    deps: RecordingDeps,
) -> None:
    """Publish a learner take only if its analysis still owns the attempt."""
    payload = learner_prosody_payload(track)
    take = deps.recorder_service.finish_analysis(attempt_id, media, payload)
    session = deps.sessions.get(editor)
    if take is None or session is None or session.editor_session_id != take.origin.editor_session_id:
        _cleanup_unpublished(media, session)
        return
    session.learner_take = take
    session.recorder = RecorderProjection()
    eval_learner_recording_state(editor, session.recorder, take)
    eval_learner_visualizer(editor, request.field_index, payload)
    deps.set_busy_for_field(editor, request.field_index, False)
    deps.eval_status(editor, "")


def fail_learner_recording(
    editor: Any,
    attempt_id: RecordingAttemptId,
    message: str,
    deps: RecordingDeps,
) -> None:
    """Fail only the current attempt and suppress every later callback."""
    attempt = deps.recorder_service.active_attempt
    if attempt is None or attempt.attempt_id != attempt_id:
        return
    if not deps.recorder_service.fail(attempt_id, message):
        return
    session = deps.sessions.get(editor)
    if session is None or session.editor_session_id != attempt.target.editor_session_id:
        return
    session.recorder = projection_for_attempt(attempt, "failed", failure_message=message)
    deps.set_busy_for_field(editor, attempt.target.field_index, False)
    eval_learner_recording_state(editor, session.recorder, session.learner_take)
    deps.eval_status(editor, coded_error(AQE_RECORDING_FAILED, message), kind="error")


def _cleanup_unpublished(finalized_media: FinalizedMedia, session: Any | None) -> None:
    take = session.learner_take if session is not None else None
    if take is not None and take.finalized_media.path.resolve() == finalized_media.path.resolve():
        return
    try:
        finalized_media.path.unlink(missing_ok=True)
    except OSError:
        pass
