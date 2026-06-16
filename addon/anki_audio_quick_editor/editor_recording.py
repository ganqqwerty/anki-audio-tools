"""Learner voice recording lifecycle for the editor bridge."""

from __future__ import annotations

import logging
import shutil
import time
from dataclasses import replace
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
from .editor_recording_frontend import (
    eval_learner_recording_state,
)
from .editor_recording_requests import (
    LearnerRecordingRequest,
    learner_recording_request,
    learner_recording_request_from_state,
    recording_parent,
)
from .editor_session import (
    EditorSession,
    LearnerRecordingState,
    begin_learner_recording_state,
    learner_recording_is_current,
    reset_learner_playback_state,
)
from .error_codes import (
    AQE_MEDIA_REFERENCED_AUDIO_MISSING,
    AQE_RECORDING_FAILED,
    coded_error,
)
from .errors import AudioQuickEditorError
from .i18n import t
from .permission_guidance import message_with_permission_guidance
from .prosody_settings import config_with_graph_settings

if TYPE_CHECKING:
    from .editor_deps_protocols import RecordingDeps

logger = logging.getLogger(__name__)


def record_learner_voice(
    editor: Any,
    deps: RecordingDeps,
    *,
    graph_settings: dict[str, object] | None = None,
    start_cursor_ms: int | None = None,
) -> None:
    """Start learner recording for the active target graph."""
    if getattr(editor, "note", None) is None:
        return
    session = deps.sessions.setdefault(editor, EditorSession())
    if deps.is_busy(session):
        deps.eval_status(editor, deps.still_processing_message, kind="processing")
        return
    try:
        request = learner_recording_request(editor, session, graph_settings, start_cursor_ms, deps)
        recorder = deps.recorder_factory(request.output_path, editor.mw, recording_parent(editor))
    except AudioQuickEditorError as exc:
        deps.eval_status(editor, coded_error(AQE_RECORDING_FAILED, str(exc)), kind="error")
        return
    except RuntimeError as exc:
        deps.eval_status(editor, coded_error(AQE_RECORDING_FAILED, str(exc)), kind="error")
        return

    deps.stop_session_playback(session)
    state = begin_learner_recording_state(
        session,
        field_index=request.field_index,
        source_filename=request.source_filename,
        target_duration_ms=request.target_duration_ms,
        media_filename=request.output_filename,
        media_path=request.output_path,
        start_cursor_ms=request.start_cursor_ms,
        graph_settings=request.graph_settings,
        started_at=time.monotonic(),
    )
    session.learner_recording_controller = recorder
    eval_learner_recording_state(editor, state)

    def on_started(generation: int) -> None:
        if not learner_recording_is_current(
            session,
            generation=generation,
            field_index=request.field_index,
            source_filename=request.source_filename,
        ):
            return
        session.learner_recording = replace(
            session.learner_recording,
            recording_started_at_monotonic=time.monotonic(),
        )
        eval_learner_recording_state(editor, session.learner_recording)

    def on_failed(error: AudioRecordingError) -> None:
        fail_learner_recording(editor, state.generation, request, str(error), deps)

    recorder.start(state.generation, on_started=on_started, on_failed=on_failed)


def stop_learner_recording(editor: Any, deps: RecordingDeps) -> None:
    """Stop the active learner recording and process the result."""
    session = deps.sessions.get(editor)
    if session is None:
        message = t("editor.recording.none_active")
        deps.eval_status(editor, coded_error(AQE_RECORDING_FAILED, message), kind="error")
        return
    state = session.learner_recording
    request = learner_recording_request_from_state(editor, state)
    recorder = session.learner_recording_controller
    if request is None or state.status != "recording" or recorder is None:
        message = t("editor.recording.none_active")
        deps.eval_status(editor, coded_error(AQE_RECORDING_FAILED, message), kind="error")
        return

    session.learner_recording = replace(state, status="stopping")
    deps.set_busy_for_field(editor, request.field_index, True, t("editor.recording.stopping"))
    eval_learner_recording_state(editor, session.learner_recording)

    recorder.stop(
        on_completed=lambda result: learner_recording_completed(editor, request, result, deps),
        on_failed=lambda error: fail_learner_recording(editor, state.generation, request, str(error), deps),
    )

def learner_recording_completed(
    editor: Any,
    request: LearnerRecordingRequest,
    result: RecordingResult,
    deps: RecordingDeps,
) -> None:
    """Persist a completed recording and start learner prosody analysis."""
    session = deps.sessions.get(editor)
    if session is None or not learner_recording_is_current(
        session,
        generation=result.generation,
        field_index=request.field_index,
        source_filename=request.source_filename,
    ):
        return
    try:
        media_path = persist_learner_recording(result, request.output_path)
    except (AudioRecordingError, OSError) as exc:
        fail_learner_recording(editor, result.generation, request, str(exc), deps)
        return

    duration_ms = result.duration_ms
    if duration_ms is None and session.learner_recording.recording_started_at_monotonic is not None:
        duration_ms = max(0, round((time.monotonic() - session.learner_recording.recording_started_at_monotonic) * 1000))
    session.learner_recording_controller = None
    session.learner_recording = replace(
        session.learner_recording,
        status="analyzing",
        media_filename=media_path.name,
        media_path=media_path,
        recording_duration_ms=duration_ms,
    )
    deps.set_busy_for_field(editor, request.field_index, True, t("editor.status.analyzing"))
    eval_learner_recording_state(editor, session.learner_recording)
    analyze_learner_recording_async(editor, result.generation, request, media_path, deps)


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
    generation: int,
    request: LearnerRecordingRequest,
    media_path: Path,
    deps: RecordingDeps,
) -> None:
    """Analyze learner pitch in the background and publish the overlay payload."""
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
        context={"field_index": request.field_index, "filename": media_path.name},
        flush=True,
    )

    def _run() -> None:
        try:
            track = deps.analyze_prosody_cached(media_path, config)
            deps.main(
                editor,
                lambda: learner_recording_analysis_finished(editor, generation, request, track, deps),
            )
        except Exception as exc:
            message = message_with_permission_guidance(str(exc), exc)
            capture_exception(
                "editor.worker.learner_recording_analysis",
                exc,
                operation="editor.learner_recording",
                operation_id=operation_id,
                user_message=message or t("editor.graph.failed"),
                context={"field_index": request.field_index, "filename": str(media_path)},
                log=logger,
            )
            deps.main(
                editor,
                lambda: fail_learner_recording(
                    editor,
                    generation,
                    request,
                    message or t("editor.graph.failed"),
                    deps,
                ),
            )

    deps.threading.Thread(target=_run, daemon=True).start()


def play_learner_recording(editor: Any, deps: RecordingDeps) -> None:
    """Toggle playback for the latest learner recording if one exists."""
    session = deps.sessions.get(editor)
    if session is None:
        message = t("editor.status.referenced_audio_missing")
        deps.eval_status(editor, coded_error(AQE_MEDIA_REFERENCED_AUDIO_MISSING, message), kind="error")
        return
    state = session.learner_recording
    media_path = state.media_path
    if state.status != "ready" or media_path is None or not media_path.is_file():
        reset_learner_playback_state(session)
        session.learner_recording = replace(
            session.learner_recording,
            status="failed",
            failure_message=t("editor.status.referenced_audio_missing"),
        )
        eval_learner_recording_state(editor, session.learner_recording)
        message = t("editor.status.referenced_audio_missing")
        deps.eval_status(editor, coded_error(AQE_MEDIA_REFERENCED_AUDIO_MISSING, message), kind="error")
        return

    from aqt.sound import av_player

    if state.playback_status in {"playing", "paused"}:
        try:
            av_player.toggle_pause()
        except Exception as exc:  # pragma: no cover - depends on active Anki audio backend
            logger.info("learner recording pause/resume failed: %s", exc)
            deps.eval_status(editor, t("editor.playback.pause_unavailable"), kind="warning")
            return
        now = time.monotonic()
        if state.playback_status == "playing":
            position_ms = _learner_playback_position_ms(state, now)
            session.learner_recording = replace(
                state,
                playback_status="paused",
                playback_position_ms=position_ms,
                playback_started_at_monotonic=None,
                playback_generation=state.playback_generation + 1,
            )
            eval_learner_recording_state(editor, session.learner_recording)
            deps.eval_status(editor, t("editor.playback.paused"))
            return
        session.learner_recording = replace(
            state,
            playback_status="playing",
            playback_started_at_monotonic=now,
            playback_generation=state.playback_generation + 1,
        )
        eval_learner_recording_state(editor, session.learner_recording)
        _schedule_learner_playback_finished(editor, session, session.learner_recording, deps)
        deps.eval_status(editor, t("editor.playback.playing"))
        return

    from anki.sound import SoundOrVideoTag

    deps.stop_session_playback(session)
    state = session.learner_recording
    av_player.play_tags([SoundOrVideoTag(str(media_path))])
    session.learner_recording = replace(
        state,
        playback_status="playing",
        playback_position_ms=0,
        playback_started_at_monotonic=time.monotonic(),
        playback_generation=state.playback_generation + 1,
    )
    eval_learner_recording_state(editor, session.learner_recording)
    _schedule_learner_playback_finished(editor, session, session.learner_recording, deps)
    deps.eval_status(editor, t("editor.playback.playing"))


def _schedule_learner_playback_finished(
    editor: Any,
    session: EditorSession,
    state: LearnerRecordingState,
    deps: RecordingDeps,
) -> None:
    duration_ms = int(state.recording_duration_ms or state.target_duration_ms or 0)
    remaining_ms = max(0, duration_ms - int(state.playback_position_ms or 0))
    if remaining_ms <= 0:
        remaining_ms = 1
    playback_generation = state.playback_generation
    recording_generation = state.generation

    def _finish() -> None:
        current = session.learner_recording
        if (
            current.generation != recording_generation
            or current.playback_generation != playback_generation
            or current.playback_status != "playing"
        ):
            return
        session.learner_recording = replace(
            current,
            playback_status="stopped",
            playback_position_ms=0,
            playback_started_at_monotonic=None,
            playback_generation=current.playback_generation + 1,
        )
        eval_learner_recording_state(editor, session.learner_recording)

    from aqt.qt import QTimer

    QTimer.singleShot(remaining_ms, lambda: deps.main(editor, _finish))


def _learner_playback_position_ms(state: LearnerRecordingState, now: float) -> int:
    if state.playback_started_at_monotonic is None:
        return int(state.playback_position_ms or 0)
    elapsed_ms = round((now - state.playback_started_at_monotonic) * 1000)
    duration_ms = int(state.recording_duration_ms or state.target_duration_ms or 0)
    return _clamp_ms(int(state.playback_position_ms or 0) + elapsed_ms, duration_ms)


def _clamp_ms(value: int | None, duration_ms: int) -> int:
    if value is None:
        return 0
    return max(0, min(int(value), max(0, int(duration_ms))))
