"""Prosody analysis behavior for the editor bridge."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .audio_state import AudioProcessingConfig
from .contracts_generated import ProsodyPayload
from .editor_session import EditorSession
from .errors import AudioQuickEditorError
from .media_paths import existing_media_file_path
from .prosody_types import ProsodyTrack, clamp_cursor_ms
from .sound_refs import safe_media_basename


def analyze_current_async(editor: Any, deps: Any) -> None:
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
        deps.eval_status(editor, message, kind="error")
        return
    media_path = existing_media_file_path(Path(editor.mw.col.media.dir()), filename)
    if media_path is None:
        deps.fail_field_analysis_without_generation(editor, field_index, deps.referenced_audio_missing)
        deps.eval_status(editor, deps.referenced_audio_missing, kind="error")
        return
    deps.start_field_analysis_async(editor, field_index, filename, media_path)


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
    field_index, expected_filename = parsed
    resolved = deps.resolve_requested_field_media(editor, field_index, expected_filename)
    if resolved is None:
        deps.finish_ignored_field_analysis(editor, field_index)
        return
    filename, _media_path = resolved
    media_path = existing_media_file_path(Path(editor.mw.col.media.dir()), filename)
    if media_path is None:
        deps.fail_field_analysis_without_generation(editor, field_index, deps.referenced_audio_missing)
        return
    deps.start_field_analysis_async(editor, field_index, filename, media_path)


def parse_graph_analysis_request(request: Any) -> tuple[int, str] | None:
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
    return (field_index, filename) if filename else None


def start_field_analysis_async(
    editor: Any,
    field_index: int,
    filename: str,
    media_path: Path,
    deps: Any,
) -> None:
    """Start background prosody analysis for a field."""
    session = deps.sessions.setdefault(editor, EditorSession())
    if deps.is_busy(session):
        deps.eval_visualizer_status_for_field(
            editor,
            field_index,
            deps.still_processing_message,
            kind="processing",
        )
        return
    config = AudioProcessingConfig.from_config(deps.config(editor))
    generation = begin_field_analysis(session, field_index, filename)
    deps.set_busy_for_field(editor, field_index, True, "Analyzing...")
    deps.eval_visualizer_status_for_field(editor, field_index, "Analyzing...", kind="processing")

    def _run() -> None:
        try:
            track = deps.analyze_prosody_cached(media_path, config)
            deps.main(editor, lambda: deps.analysis_finished(editor, generation, field_index, track))
        except Exception as exc:
            message = str(exc)
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
    deps.eval_visualizer_status_for_field(
        editor,
        field_index,
        message or "Audio visualization failed.",
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
    editor.web.eval(
        "window.__aqeSetVisualizerStatus && window.__aqeSetVisualizerStatus("
        f"{json.dumps(int(field_index))}, "
        f"{json.dumps(message or 'Audio visualization failed.')}, "
        f"{json.dumps('error')})"
    )


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
