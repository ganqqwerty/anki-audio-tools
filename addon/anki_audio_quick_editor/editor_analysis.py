"""Prosody analysis behavior for the editor bridge."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .audio_state import AudioProcessingConfig
from .contracts_generated import ProsodyPayload
from .diagnostics_runtime import capture_exception, new_operation_id, record_breadcrumb
from .editor_session import EditorSession
from .error_codes import (
    AQE_GRAPH_ANALYSIS_FAILED,
    AQE_MEDIA_CURRENT_FIELD_AUDIO_MISSING,
    AQE_MEDIA_REFERENCED_AUDIO_MISSING,
    coded_error,
)
from .errors import AudioQuickEditorError
from .i18n import t
from .media_paths import existing_media_file_path
from .permission_guidance import message_with_permission_guidance
from .prosody_settings import config_with_graph_settings, sanitize_graph_settings
from .prosody_types import ProsodyTrack, clamp_cursor_ms
from .sound_refs import safe_media_basename


@dataclass(frozen=True)
class GraphAnalysisRequest:
    """Frontend graph analysis request normalized for backend execution."""

    field_index: int
    graph_settings: dict[str, object]
    source_filename: str


def analyze_current_async(
    editor: Any,
    deps: Any,
    *,
    graph_settings: dict[str, object] | None = None,
) -> None:
    """Analyze the active editor field for graph rendering."""
    existing = deps.sessions.get(editor)
    if existing and deps.is_busy(existing):
        deps.eval_visualizer_status(editor, deps.still_processing_message, kind="processing")
        return
    field_index = deps.current_field_index(editor)
    try:
        filename, _media_path = deps.current_sound_reference(editor, field_index)
    except AudioQuickEditorError as exc:
        message = str(exc)
        deps.fail_field_analysis_without_generation(editor, field_index, message)
        deps.eval_status(editor, _coded_analysis_error(message, deps), kind="error")
        return
    media_path = existing_media_file_path(Path(editor.mw.col.media.dir()), filename)
    if media_path is None:
        deps.fail_field_analysis_without_generation(editor, field_index, deps.referenced_audio_missing)
        deps.eval_status(
            editor,
            coded_error(AQE_MEDIA_REFERENCED_AUDIO_MISSING, deps.referenced_audio_missing),
            kind="error",
        )
        return
    deps.start_field_analysis_async(editor, field_index, filename, media_path, graph_settings)


def analyze_field_from_frontend(editor: Any, deps: Any) -> None:
    """Pop and process a field-addressed graph analysis request from the frontend."""
    deps.eval_with_callback(
        editor,
        "window.__aqePopPendingGraphAnalysisRequest ? "
        "window.__aqePopPendingGraphAnalysisRequest() : null",
        lambda request: deps.analyze_requested_field_async(editor, request),
    )


def analyze_requested_field_async(editor: Any, request: Any, deps: Any) -> None:
    """Analyze a specific frontend-requested field if it still matches the request."""
    parsed = parse_graph_analysis_request(request)
    if parsed is None:
        return
    resolved = deps.resolve_requested_field_media(editor, parsed.field_index, parsed.source_filename)
    if resolved is None:
        deps.finish_ignored_field_analysis(editor, parsed.field_index)
        return
    filename, _media_path = resolved
    media_path = existing_media_file_path(Path(editor.mw.col.media.dir()), filename)
    if media_path is None:
        deps.fail_field_analysis_without_generation(editor, parsed.field_index, deps.referenced_audio_missing)
        return
    deps.start_field_analysis_async(
        editor,
        parsed.field_index,
        filename,
        media_path,
        parsed.graph_settings,
    )


def parse_graph_analysis_request(request: Any) -> GraphAnalysisRequest | None:
    """Normalize a graph analysis request payload."""
    if not isinstance(request, dict):
        return None
    raw_ord = request.get("ord")
    if raw_ord is None:
        return None
    try:
        field_index = int(raw_ord)
    except (TypeError, ValueError):
        return None
    if field_index < 0:
        return None
    filename = safe_media_basename(str(request.get("sourceFilename") or ""))
    if not filename:
        return None
    return GraphAnalysisRequest(
        field_index=field_index,
        graph_settings=sanitize_graph_settings(request.get("graphSettings")),
        source_filename=filename,
    )


def start_field_analysis_async(
    editor: Any,
    field_index: int,
    filename: str,
    media_path: Path,
    graph_settings: dict[str, object] | None,
    deps: Any,
) -> None:
    """Start background prosody analysis for a field."""
    operation_id = new_operation_id("graph")
    session = deps.sessions.setdefault(editor, EditorSession())
    if deps.is_busy(session):
        deps.eval_visualizer_status_for_field(
            editor,
            field_index,
            deps.still_processing_message,
            kind="processing",
        )
        return
    config = config_with_graph_settings(
        AudioProcessingConfig.from_config(deps.config(editor)),
        graph_settings,
    )
    generation = begin_field_analysis(session, field_index, filename)
    deps.set_busy_for_field(editor, field_index, True, t("editor.status.analyzing"))
    deps.eval_visualizer_status_for_field(editor, field_index, t("editor.status.analyzing"), kind="processing")
    record_breadcrumb(
        "editor.graph_analysis.started",
        source="editor",
        operation="editor.graph_analysis",
        operation_id=operation_id,
        context={"field_index": field_index, "filename": filename},
        flush=True,
    )

    def _run() -> None:
        try:
            track = deps.analyze_prosody_cached(media_path, config)
            deps.main(editor, lambda: deps.analysis_finished(editor, generation, field_index, track))
        except Exception as exc:
            message = message_with_permission_guidance(str(exc), exc)
            capture_exception(
                "editor.worker.graph_analysis",
                exc,
                operation="editor.graph_analysis",
                operation_id=operation_id,
                user_message=message or t("editor.graph.failed"),
                context={"field_index": field_index, "filename": filename, "media_path": str(media_path)},
            )
            deps.main(editor, lambda: deps.analysis_failed(editor, generation, field_index, message))

    deps.threading.Thread(target=_run, daemon=True).start()


def begin_field_analysis(session: EditorSession, field_index: int, filename: str) -> int:
    """Mark a field analysis as in progress and return its generation id."""
    session.analysis_generation += 1
    generation = session.analysis_generation
    session.analysis_generations_by_field[field_index] = generation
    session.analysis_busy_fields.add(field_index)
    session.analysis_busy = True
    session.graph_active_fields.add(field_index)
    session.visualized_filenames_by_field[field_index] = filename
    session.visualized_durations_by_field.pop(field_index, None)
    return generation


def finish_ignored_field_analysis(editor: Any, field_index: int, deps: Any) -> None:
    """Clear busy state for an obsolete field analysis request."""
    deps.set_busy_for_field(editor, field_index, False)
    deps.eval_visualizer_status_for_field(editor, field_index, "", kind="info")


def fail_field_analysis_without_generation(editor: Any, field_index: int, message: str, deps: Any) -> None:
    """Report analysis failure before a generation is registered."""
    deps.set_busy_for_field(editor, field_index, False)
    display_message = message or t("editor.graph.failed")
    deps.eval_visualizer_status_for_field(
        editor,
        field_index,
        _coded_analysis_error(display_message, deps),
        kind="error",
    )


def analysis_finished(
    editor: Any,
    generation: int,
    field_index: int,
    track: ProsodyTrack,
    deps: Any,
) -> None:
    """Apply a completed prosody analysis result to the frontend."""
    session = deps.sessions.get(editor)
    if session is None or not is_current_field_analysis(session, field_index, generation):
        return
    end_field_analysis(session, field_index)
    session.visualized_filenames_by_field[field_index] = track.source_filename
    session.visualized_durations_by_field[field_index] = track.duration_ms
    cursor_ms = 0
    if session.field_index == field_index:
        session.visualized_filename = track.source_filename
        session.visualized_duration_ms = track.duration_ms
        session.cursor_ms = clamp_cursor_ms(session.cursor_ms, track.duration_ms)
        cursor_ms = session.cursor_ms
    payload = json.dumps(ProsodyPayload.from_dict(track.to_payload()).to_dict())
    cursor_payload = json.dumps(cursor_ms)
    editor.web.eval(
        "window.__aqeSetVisualizer && window.__aqeSetVisualizer("
        f"{json.dumps(int(field_index))}, {payload}, {cursor_payload})"
    )
    deps.set_busy_for_field(editor, field_index, False)


def analysis_failed(editor: Any, generation: int, field_index: int, message: str, deps: Any) -> None:
    """Report a failed prosody analysis result."""
    session = deps.sessions.get(editor)
    if session is None or not is_current_field_analysis(session, field_index, generation):
        return
    end_field_analysis(session, field_index)
    deps.set_busy_for_field(editor, field_index, False)
    display_message = message or t("editor.graph.failed")
    deps.eval_visualizer_status_for_field(
        editor,
        field_index,
        _coded_analysis_error(display_message, deps),
        kind="error",
    )


def _coded_analysis_error(message: str, deps: Any) -> dict[str, str]:
    if message == deps.current_field_audio_missing:
        return coded_error(AQE_MEDIA_CURRENT_FIELD_AUDIO_MISSING, message)
    if message == deps.referenced_audio_missing:
        return coded_error(AQE_MEDIA_REFERENCED_AUDIO_MISSING, message)
    return coded_error(AQE_GRAPH_ANALYSIS_FAILED, message)


def is_current_field_analysis(
    session: EditorSession,
    field_index: int,
    generation: int,
) -> bool:
    """Return whether the result belongs to the active field analysis generation."""
    return session.analysis_generations_by_field.get(field_index) == generation


def end_field_analysis(session: EditorSession, field_index: int) -> None:
    """Clear analysis-busy state for a field."""
    session.analysis_busy_fields.discard(field_index)
    session.analysis_generations_by_field.pop(field_index, None)
    session.analysis_busy = bool(session.analysis_busy_fields)
