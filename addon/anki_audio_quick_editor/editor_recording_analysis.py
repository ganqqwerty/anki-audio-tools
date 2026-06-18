"""Learner recording analysis result application helpers."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Any

from .editor_recording_frontend import (
    eval_learner_recording_state,
    eval_learner_visualizer,
    learner_prosody_payload,
)
from .editor_recording_requests import LearnerRecordingRequest
from .editor_recording_state import learner_recording_is_current
from .error_codes import AQE_RECORDING_FAILED, coded_error
from .prosody_types import ProsodyTrack

if TYPE_CHECKING:
    from .editor_deps_protocols import RecordingDeps


def learner_recording_analysis_finished(
    editor: Any,
    generation: int,
    request: LearnerRecordingRequest,
    track: ProsodyTrack,
    deps: RecordingDeps,
) -> None:
    """Apply a learner prosody result if it is still current."""
    session = deps.sessions.get(editor)
    if session is None or not learner_recording_is_current(
        session,
        generation=generation,
        field_index=request.field_index,
        source_filename=request.source_filename,
    ):
        return
    payload = learner_prosody_payload(track)
    session.learner_recording = replace(
        session.learner_recording,
        status="ready",
        prosody_payload=payload,
        failure_message=None,
    )
    eval_learner_recording_state(editor, session.learner_recording)
    eval_learner_visualizer(editor, request.field_index, payload)
    deps.set_busy_for_field(editor, request.field_index, False)
    deps.eval_status(editor, "")


def fail_learner_recording(
    editor: Any,
    generation: int,
    request: LearnerRecordingRequest,
    message: str,
    deps: RecordingDeps,
) -> None:
    """Mark a learner recording attempt failed if it is still current."""
    session = deps.sessions.get(editor)
    if session is None or not learner_recording_is_current(
        session,
        generation=generation,
        field_index=request.field_index,
        source_filename=request.source_filename,
    ):
        return
    session.learner_recording_controller = None
    session.learner_recording = replace(
        session.learner_recording,
        status="failed",
        failure_message=message,
    )
    deps.set_busy_for_field(editor, request.field_index, False)
    eval_learner_recording_state(editor, session.learner_recording)
    deps.eval_status(editor, coded_error(AQE_RECORDING_FAILED, message), kind="error")
