"""Learner voice recording lifecycle for the editor bridge."""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from .audio_recording import (
    AudioRecordingError,
    RecordingResult,
    recording_result_from_path,
)
from .audio_state import AudioProcessingConfig
from .diagnostics_runtime import capture_exception, new_operation_id, record_breadcrumb
from .editor_recording_frontend import (
    eval_learner_recording_state,
    eval_learner_visualizer,
    learner_prosody_payload,
)
from .editor_session import (
    EditorSession,
    LearnerRecordingState,
    begin_learner_recording_state,
    learner_recording_is_current,
)
from .error_codes import AQE_MEDIA_REFERENCED_AUDIO_MISSING, AQE_RECORDING_FAILED, coded_error
from .errors import AudioProcessingError, AudioQuickEditorError
from .i18n import t
from .permission_guidance import message_with_permission_guidance
from .prosody_settings import config_with_graph_settings
from .prosody_types import ProsodyTrack
from .sound_refs import safe_media_basename

logger = logging.getLogger(__name__)
_FILENAME_SAFE_RE = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass(frozen=True)
class LearnerRecordingRequest:
    """Validated learner recording request for the active target graph."""

    field_index: int
    source_filename: str
    source_path: Path
    target_duration_ms: int
    output_filename: str
    output_path: Path
    graph_settings: dict[str, object] | None = None


def record_learner_voice(
    editor: Any,
    deps: Any,
    *,
    graph_settings: dict[str, object] | None = None,
) -> None:
    """Start learner recording for the active target graph."""
    if getattr(editor, "note", None) is None:
        return
    session = deps.sessions.setdefault(editor, EditorSession())
    if deps.is_busy(session):
        deps.eval_status(editor, deps.still_processing_message, kind="processing")
        return
    try:
        request = learner_recording_request(editor, session, graph_settings, deps)
        recorder = deps.recorder_factory(request.output_path, editor.mw, _recording_parent(editor))
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


def stop_learner_recording(editor: Any, deps: Any) -> None:
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


def learner_recording_request(
    editor: Any,
    session: EditorSession,
    graph_settings: dict[str, object] | None,
    deps: Any,
) -> LearnerRecordingRequest:
    """Validate that the current field still matches a target graph."""
    field_index = deps.current_field_index(editor)
    source_filename = session.visualized_filenames_by_field.get(field_index)
    target_duration_ms = session.visualized_durations_by_field.get(field_index)
    if not source_filename or target_duration_ms is None or target_duration_ms <= 0:
        raise AudioProcessingError(t("editor.status.graph_inactive"))
    resolved = deps.resolve_requested_field_media(editor, field_index, source_filename)
    if resolved is None:
        raise AudioProcessingError(t("editor.status.graph_audio_mismatch"))
    filename, source_path = resolved
    media_dir = Path(editor.mw.col.media.dir())
    generation = session.learner_recording.generation + 1
    output_filename = make_learner_recording_filename(filename, generation)
    return LearnerRecordingRequest(
        field_index=field_index,
        source_filename=filename,
        source_path=source_path,
        target_duration_ms=int(target_duration_ms),
        output_filename=output_filename,
        output_path=media_dir / output_filename,
        graph_settings=graph_settings,
    )


def learner_recording_request_from_state(
    editor: Any,
    state: LearnerRecordingState,
) -> LearnerRecordingRequest | None:
    """Rebuild the active request from persisted session state."""
    if (
        state.field_index is None
        or not state.source_filename
        or not state.media_filename
        or state.media_path is None
        or state.target_duration_ms is None
    ):
        return None
    return LearnerRecordingRequest(
        field_index=state.field_index,
        source_filename=state.source_filename,
        source_path=Path(editor.mw.col.media.dir()) / state.source_filename,
        target_duration_ms=state.target_duration_ms,
        output_filename=state.media_filename,
        output_path=state.media_path,
        graph_settings=state.graph_settings,
    )


def make_learner_recording_filename(
    source_filename: str,
    generation: int,
    *,
    now_ns: int | None = None,
) -> str:
    """Return an add-on-owned WAV filename for a learner recording."""
    safe_name = safe_media_basename(source_filename)
    stem = _FILENAME_SAFE_RE.sub("_", Path(safe_name).stem).strip("._") or "recording"
    trimmed_stem = stem[:48]
    stamp = now_ns if now_ns is not None else time.time_ns()
    return f"{trimmed_stem}__aqe_voice_{stamp}_{generation}.wav"


def learner_recording_completed(
    editor: Any,
    request: LearnerRecordingRequest,
    result: RecordingResult,
    deps: Any,
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
        output_path.write_bytes(result.path.read_bytes())
    recording_result_from_path(output_path, generation=result.generation)
    return output_path


def analyze_learner_recording_async(
    editor: Any,
    generation: int,
    request: LearnerRecordingRequest,
    media_path: Path,
    deps: Any,
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


def learner_recording_analysis_finished(
    editor: Any,
    generation: int,
    request: LearnerRecordingRequest,
    track: ProsodyTrack,
    deps: Any,
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
    deps: Any,
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


def play_learner_recording(editor: Any, deps: Any) -> None:
    """Play the latest learner recording if one exists."""
    session = deps.sessions.get(editor)
    if session is None:
        message = t("editor.status.referenced_audio_missing")
        deps.eval_status(editor, coded_error(AQE_MEDIA_REFERENCED_AUDIO_MISSING, message), kind="error")
        return
    state = session.learner_recording
    media_path = state.media_path
    if state.status != "ready" or media_path is None or not media_path.is_file():
        session.learner_recording = replace(
            state,
            status="failed",
            failure_message=t("editor.status.referenced_audio_missing"),
        )
        eval_learner_recording_state(editor, session.learner_recording)
        message = t("editor.status.referenced_audio_missing")
        deps.eval_status(editor, coded_error(AQE_MEDIA_REFERENCED_AUDIO_MISSING, message), kind="error")
        return

    from anki.sound import SoundOrVideoTag
    from aqt.sound import av_player

    deps.stop_session_playback(session)
    av_player.play_tags([SoundOrVideoTag(str(media_path))])
    deps.eval_status(editor, t("editor.playback.playing"))

def _recording_parent(editor: Any) -> Any:
    return getattr(editor, "parentWindow", None) or getattr(editor, "widget", None) or editor.web
