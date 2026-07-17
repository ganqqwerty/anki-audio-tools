"""Learner voice recording lifecycle through the application recorder service."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .audio_recording import (
    AudioRecordingError,
    RecordingResult,
    recording_result_from_path,
)
from .audio_state import AudioProcessingConfig
from .diagnostics_runtime import capture_exception, new_operation_id, record_breadcrumb
from .editor_recording_analysis import (
    fail_learner_recording,
    learner_recording_analysis_finished,
)
from .editor_recording_frontend import eval_learner_recording_state
from .editor_recording_requests import (
    LearnerRecordingRequest,
    learner_recording_request,
    learner_recording_request_from_attempt,
    recording_parent,
)
from .editor_recording_state import clear_recorder_projection, projection_for_attempt
from .editor_session import EditorSession
from .error_codes import AQE_RECORDING_FAILED, coded_error
from .errors import AudioQuickEditorError
from .i18n import t
from .permission_guidance import message_with_permission_guidance
from .prosody_settings import config_with_graph_settings
from .recorder.model import (
    BackendMediaGeneration,
    CaptureSpec,
    FinalizedMedia,
    RecorderTarget,
    RecordingAttemptId,
)
from .recorder.service import RecorderServiceBusyError

if TYPE_CHECKING:
    from .editor_deps_protocols import RecordingDeps

logger = logging.getLogger(__name__)


def record_learner_voice(
    editor: Any,
    deps: RecordingDeps,
    *,
    field_index: int | None = None,
    graph_settings: dict[str, object] | None = None,
    start_cursor_ms: int | None = None,
) -> None:
    """Acquire the application recorder for the active editor target."""
    if getattr(editor, "note", None) is None:
        return
    session = deps.sessions.setdefault(editor, EditorSession())
    if deps.is_busy(session) or deps.recorder_service.is_busy:
        deps.eval_status(editor, deps.still_processing_message, kind="processing")
        return
    try:
        request = learner_recording_request(
            editor,
            session,
            graph_settings,
            start_cursor_ms,
            deps,
            field_index,
        )
        recorder = deps.recorder_factory(request.output_path, editor.mw, recording_parent(editor))
    except (AudioQuickEditorError, RuntimeError) as exc:
        deps.eval_status(editor, coded_error(AQE_RECORDING_FAILED, str(exc)), kind="error")
        return

    target = RecorderTarget(
        editor_session_id=session.editor_session_id,
        note_id=session.note_id,
        field_index=request.field_index,
        source_filename=request.source_filename,
        backend_media_generation=BackendMediaGeneration(
            session.backend_media_generation_for(request.field_index, request.source_filename)
        ),
    )
    capture = CaptureSpec(
        output_filename=request.output_filename,
        output_path=request.output_path,
        target_duration_ms=request.target_duration_ms,
        timeline_anchor_ms=request.start_cursor_ms,
        graph_settings=request.graph_settings,
    )
    try:
        attempt = deps.recorder_service.begin(target, capture, recorder)
    except RecorderServiceBusyError:
        recorder.dispose()
        deps.eval_status(editor, deps.still_processing_message, kind="processing")
        return

    deps.recorder_service.discard_take(session.editor_session_id)
    session.learner_take = None
    session.recorder = projection_for_attempt(attempt, "starting")
    eval_learner_recording_state(editor, session.recorder)

    def on_started(generation: int) -> None:
        attempt_id = RecordingAttemptId(generation)
        if not deps.recorder_service.mark_started(attempt_id):
            return
        current = deps.sessions.get(editor)
        if current is None or current.editor_session_id != attempt.target.editor_session_id:
            deps.recorder_service.cancel_if_owner(attempt.target.editor_session_id, "editor_closed")
            return
        current.recorder = projection_for_attempt(attempt, "recording")
        eval_learner_recording_state(editor, current.recorder)

    def on_failed(error: AudioRecordingError) -> None:
        fail_learner_recording(editor, attempt.attempt_id, str(error), deps)

    recorder.start(int(attempt.attempt_id), on_started=on_started, on_failed=on_failed)


def stop_learner_recording(editor: Any, deps: RecordingDeps) -> None:
    """Stop the application recorder only when this editor owns it."""
    session = deps.sessions.get(editor)
    if session is None:
        logger.debug("recorder stop rejected | reason=session_missing")
        _publish_no_active_error(editor, deps)
        return
    attempt = deps.recorder_service.request_stop(session.editor_session_id)
    if attempt is None:
        logger.debug(
            "recorder stop rejected | reason=owner_or_state_mismatch editor_session=%s",
            session.editor_session_id,
        )
        _publish_no_active_error(editor, deps)
        return
    logger.debug(
        "recorder stop accepted | editor_session=%s attempt=%s field=%s",
        session.editor_session_id,
        attempt.attempt_id,
        attempt.target.field_index,
    )
    request = learner_recording_request_from_attempt(editor, attempt)
    session.recorder = projection_for_attempt(attempt, "stopping")
    deps.set_busy_for_field(editor, request.field_index, True, t("editor.recording.stopping"))
    eval_learner_recording_state(editor, session.recorder)
    if not deps.recorder_service.stop_requested(
        attempt.attempt_id,
        on_completed=lambda result: learner_recording_completed(editor, request, result, deps),
        on_failed=lambda error: fail_learner_recording(
            editor,
            attempt.attempt_id,
            str(error),
            deps,
        ),
    ):
        _publish_no_active_error(editor, deps)


def cancel_learner_recording(
    editor: Any,
    deps: RecordingDeps,
    *,
    reason: str = "user",
) -> None:
    """Cancel the recorder only when the current editor owns its attempt."""
    session = deps.sessions.get(editor)
    if session is None or not deps.recorder_service.cancel_if_owner(
        session.editor_session_id,
        reason,
    ):
        return
    field_index = session.recorder.field_index
    clear_recorder_projection(session)
    if field_index is not None:
        deps.set_busy_for_field(editor, field_index, False)
    eval_learner_recording_state(editor, session.recorder)


def learner_recording_completed(
    editor: Any,
    request: LearnerRecordingRequest,
    result: RecordingResult,
    deps: RecordingDeps,
) -> None:
    """Accept one capture terminal result, persist it, and start analysis."""
    attempt_id = RecordingAttemptId(result.generation)
    attempt = deps.recorder_service.active_attempt
    if attempt is None or not deps.recorder_service.accept_capture(
        attempt_id,
        result.path,
        result.duration_ms,
    ):
        _cleanup_stale_capture(result.path, request.output_path, deps.sessions.get(editor))
        return
    session = deps.sessions.get(editor)
    if session is None or session.editor_session_id != attempt.target.editor_session_id:
        deps.recorder_service.cancel_if_owner(attempt.target.editor_session_id, "editor_closed")
        _cleanup_stale_capture(result.path, request.output_path, session)
        return
    try:
        media_path = persist_learner_recording(result, request.output_path)
        validated = recording_result_from_path(media_path, generation=result.generation)
        duration_ms = result.duration_ms if result.duration_ms is not None else validated.duration_ms
        if duration_ms is None or duration_ms <= 0:
            raise AudioRecordingError("Unable to determine finalized recording duration.")
        media = FinalizedMedia(
            path=media_path,
            filename=media_path.name,
            format=media_path.suffix.lstrip(".").lower(),
            duration_ms=duration_ms,
            ownership="unpublished_media",
        )
        if not deps.recorder_service.mark_analyzing(attempt_id, media):
            _cleanup_unpublished_media(media_path, session)
            return
    except (AudioRecordingError, OSError) as exc:
        fail_learner_recording(editor, attempt_id, str(exc), deps)
        return

    session.recorder = projection_for_attempt(attempt, "analyzing")
    deps.set_busy_for_field(editor, request.field_index, True, t("editor.status.analyzing"))
    eval_learner_recording_state(editor, session.recorder)
    analyze_learner_recording_async(editor, attempt_id, request, media, deps)


def persist_learner_recording(result: RecordingResult, output_path: Path) -> Path:
    """Ensure the completed WAV exists in Anki media under the generated filename."""
    recording_result_from_path(result.path, generation=result.generation)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if result.path.resolve() != output_path.resolve():
        shutil.copyfile(result.path, output_path)
    recording_result_from_path(output_path, generation=result.generation)
    return output_path


def analyze_learner_recording_async(
    editor: Any,
    attempt_id: RecordingAttemptId,
    request: LearnerRecordingRequest,
    media: FinalizedMedia,
    deps: RecordingDeps,
) -> None:
    """Analyze learner pitch; publication remains guarded by attempt identity."""
    operation_id = new_operation_id("learner-graph")
    config = config_with_graph_settings(
        AudioProcessingConfig.from_config(deps.config(editor)),
        request.graph_settings,
    )
    record_breadcrumb(
        "editor.learner_recording.analysis_started",
        source="editor",
        operation="editor.learner_recording",
        operation_id=operation_id,
        context={"field_index": request.field_index, "filename": media.filename},
        flush=True,
    )

    def _run() -> None:
        try:
            track = deps.analyze_prosody_cached(media.path, config)
            deps.main(
                editor,
                lambda: learner_recording_analysis_finished(
                    editor,
                    attempt_id,
                    request,
                    media,
                    track,
                    deps,
                ),
            )
        except Exception as exc:
            message = message_with_permission_guidance(str(exc), exc)
            capture_exception(
                "editor.worker.learner_recording_analysis",
                exc,
                operation="editor.learner_recording",
                operation_id=operation_id,
                user_message=message or t("editor.graph.failed"),
                context={"field_index": request.field_index, "filename": str(media.path)},
                log=logger,
            )
            deps.main(
                editor,
                lambda: fail_learner_recording(
                    editor,
                    attempt_id,
                    message or t("editor.graph.failed"),
                    deps,
                ),
            )

    deps.threading.Thread(target=_run, daemon=True).start()


def _publish_no_active_error(editor: Any, deps: RecordingDeps) -> None:
    message = t("editor.recording.none_active")
    deps.eval_status(editor, coded_error(AQE_RECORDING_FAILED, message), kind="error")


def _cleanup_stale_capture(path: Path, output_path: Path, session: EditorSession | None) -> None:
    if path.resolve() == output_path.resolve():
        _cleanup_unpublished_media(path, session)
        return
    try:
        path.unlink(missing_ok=True)
    except OSError:
        logger.info("stale attempt capture cleanup failed: %s", path)


def _cleanup_unpublished_media(path: Path, session: EditorSession | None) -> None:
    take = session.learner_take if session is not None else None
    if take is not None and take.finalized_media.path.resolve() == path.resolve():
        return
    try:
        path.unlink(missing_ok=True)
    except OSError:
        logger.info("unpublished learner media cleanup failed: %s", path)
