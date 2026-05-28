"""Region-delete behavior for the editor bridge."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, cast

from . import editor_region_delete_request as _request
from .audio_state import AudioEditState, AudioProcessingConfig
from .diagnostics_runtime import capture_exception, new_operation_id, record_breadcrumb
from .editor_processing_shared import (
    request_history_availability_after_edit as _request_history_availability_after_edit,
)
from .editor_processing_shared import (
    sync_history_availability as _sync_history_availability,
)
from .editor_region_delete_request import (
    parse_region_delete_request as _parse_region_delete_request,
)
from .editor_region_delete_worker import (
    region_delete_log_context as _region_delete_log_context,
)
from .editor_region_delete_worker import (
    render_region_operation as _render_region_operation,
)
from .editor_region_delete_worker import (
    run_region_delete_worker,
)
from .editor_session import (
    EditorProcessingGuard,
    EditorSession,
    PendingEditorStatus,
    RegionDeleteRequest,
    begin_processing_guard,
    clear_processing_for_stale_guard,
    processing_guard_matches_editor,
)
from .editor_status import region_operation_status_summary
from .error_codes import (
    AQE_AUDIO_PROCESSING_FAILED,
    AQE_GRAPH_ANALYSIS_FAILED,
    coded_error,
)
from .errors import AudioProcessingError
from .i18n import t
from .media_paths import existing_media_file_path, media_filenames_match
from .permission_guidance import message_with_permission_guidance
from .sound_refs import replace_sound_reference, select_first_sound_reference

logger = logging.getLogger(__name__)
parse_region_delete_request = _request.parse_region_delete_request
required_region_delete_values = _request.required_region_delete_values
region_delete_source_filename = _request.region_delete_source_filename
region_delete_trigger = _request.region_delete_trigger
region_delete_log_context = _region_delete_log_context
render_region_operation = _render_region_operation
region_operation_busy_message = _request.region_operation_busy_message
region_operation_command_status = _request.region_operation_command_status
region_operation_whole_clip_message = _request.region_operation_whole_clip_message


def delete_selection_from_frontend(editor: Any, deps: Any) -> None:
    """Pop and process a pending frontend region-delete request."""
    deps.eval_with_callback(
        editor,
        "window.__aqePopPendingRegionDeleteRequest ? "
        "window.__aqePopPendingRegionDeleteRequest() : null",
        lambda request: deps.delete_selection_with_request(editor, request),
    )


def delete_selection_with_request(editor: Any, request: Any, deps: Any) -> None:
    """Validate a region-delete payload and start deletion."""
    parsed = _parse_region_delete_request(request)
    if parsed is None:
        deps.set_busy(editor, False)
        deps.eval_status(
            editor,
            coded_error(AQE_AUDIO_PROCESSING_FAILED, t("editor.status.region_read_failed")),
            kind="error",
        )
        return
    existing = deps.sessions.get(editor)
    if existing and deps.is_busy(existing):
        deps.eval_status(editor, deps.still_processing_message, kind="processing")
        return
    active_field = deps.current_field_index(editor)
    if active_field != parsed.field_index:
        deps.set_busy_for_field(editor, parsed.field_index, False)
        deps.eval_status(
            editor,
            coded_error(AQE_GRAPH_ANALYSIS_FAILED, t("editor.status.graph_inactive")),
            kind="error",
        )
        return
    resolved = deps.resolve_requested_field_media(editor, parsed.field_index, parsed.source_filename)
    if resolved is None:
        deps.set_busy_for_field(editor, parsed.field_index, False)
        deps.eval_status(
            editor,
            coded_error(AQE_GRAPH_ANALYSIS_FAILED, t("editor.status.graph_audio_mismatch")),
            kind="error",
        )
        return
    session, current_path = deps.current_media_path(editor)
    if not media_filenames_match(current_path.name, parsed.source_filename):
        deps.set_busy_for_field(editor, parsed.field_index, False)
        deps.eval_status(
            editor,
            coded_error(AQE_GRAPH_ANALYSIS_FAILED, t("editor.status.graph_audio_mismatch")),
            kind="error",
        )
        return
    if parsed.selection_start_ms <= 0 and parsed.selection_end_ms >= parsed.duration_ms:
        logger.info("region delete rejected whole clip: %s", region_delete_log_context(parsed))
        deps.set_busy_for_field(editor, parsed.field_index, False)
        deps.eval_status(editor, region_operation_whole_clip_message(parsed), kind="warning")
        return
    delete_selection_async(
        editor,
        session,
        current_path,
        parsed,
        AudioProcessingConfig.from_config(deps.config(editor)),
        deps,
    )

def delete_selection_async(
    editor: Any,
    session: EditorSession,
    source_path: Path,
    request: RegionDeleteRequest,
    config: AudioProcessingConfig,
    deps: Any,
) -> None:
    """Render a media file with the requested region removed."""
    operation_id = new_operation_id("region")
    started_at = time.monotonic()
    deps.stop_session_playback(session)
    session.post_edit_playback_generation += 1
    session.processing = True
    session.field_index = request.field_index
    guard = begin_processing_guard(
        session,
        field_index=request.field_index,
        source_filename=request.source_filename,
    )
    session.playback_active = False
    session.playback_paused = False
    session.cursor_ms = request.cursor_ms
    deps.set_busy_for_field(editor, request.field_index, True, region_operation_busy_message(request))
    deps.eval_playback_state(editor, request.field_index, "stopped", request.cursor_ms)
    logger.info("region delete accepted: %s", region_delete_log_context(request))
    record_breadcrumb(
        "editor.region_delete.accepted",
        source="editor",
        operation="editor.region_delete",
        operation_id=operation_id,
        context=region_delete_log_context(request),
        flush=True,
    )

    def _run() -> None:
        run_region_delete_worker(editor, session, source_path, request, config, guard, started_at, operation_id, deps)

    deps.threading.Thread(target=_run, daemon=True).start()


def replace_current_field_after_region_delete(
    editor: Any,
    request: RegionDeleteRequest,
    saved_name: str,
    output_duration_ms: int | None,
    started_at: float,
    deps: Any,
    *,
    guard: EditorProcessingGuard | None = None,
    output_path: Path | None = None,
) -> None:
    """Replace the field after a successful region-delete render."""
    session = deps.sessions.get(editor)
    if not _accept_guarded_region_replacement(editor, session, guard, deps):
        return
    try:
        saved_name = _persist_region_delete_output(editor, saved_name, output_path)
        field_index = request.field_index
        field_html = editor.note.fields[field_index]
        selection = select_first_sound_reference(field_html)
        if selection.selected is None:
            raise AudioProcessingError(deps.current_field_audio_missing)
        if not media_filenames_match(selection.selected.filename, request.source_filename):
            raise AudioProcessingError(t("editor.status.graph_audio_mismatch"))
        deps.dispose_editor_frontend_controls(editor)
        editor.note.fields[field_index] = replace_sound_reference(field_html, selection.selected, saved_name)
        should_redraw_graph = _replace_region_delete_session_state(editor, session, field_index, saved_name, request)
        logger.info(
            "region delete completed: %s",
            {
                **region_delete_log_context(request),
                "generated_filename": saved_name,
                "removed_duration_ms": request.removed_duration_ms,
                "output_duration_ms": output_duration_ms,
                "elapsed_ms": round((time.monotonic() - started_at) * 1000),
            },
        )
        record_breadcrumb(
            "editor.region_delete.completed",
            source="editor",
            operation="editor.region_delete",
            context={
                **region_delete_log_context(request),
                "generated_filename": saved_name,
                "output_duration_ms": output_duration_ms,
            },
            flush=True,
        )
        editor.loadNote(focusTo=field_index)
        if session:
            session.pending_status = None
        _sync_history_availability(editor, session, deps)
        _request_history_availability_after_edit(editor, session, deps)
        deps.eval_playback_state(editor, field_index, "stopped", 0)
        if should_redraw_graph:
            deps.request_graph_redraw(editor, saved_name)
        else:
            deps.set_busy_for_field(editor, field_index, False)
        deps.request_playback_after_edit(editor, field_index)
    except Exception as exc:
        message = message_with_permission_guidance(str(exc), exc)
        capture_exception(
            "editor.main.region_delete_replacement",
            exc,
            operation="editor.region_delete",
            user_message=message,
            context=region_delete_log_context(request),
            log=logger,
        )
        deps.render_failed(editor, message)


def _accept_guarded_region_replacement(
    editor: Any,
    session: EditorSession | None,
    guard: EditorProcessingGuard | None,
    deps: Any,
) -> bool:
    if guard is None or processing_guard_matches_editor(editor, session, guard, deps):
        return True
    if clear_processing_for_stale_guard(session, guard):
        deps.set_busy_for_field(editor, guard.field_index, False)
    return False


def _persist_region_delete_output(editor: Any, saved_name: str, output_path: Path | None) -> str:
    if output_path is None:
        return saved_name
    return cast(str, editor.mw.col.media.write_data(saved_name, output_path.read_bytes()))


def _replace_region_delete_session_state(
    editor: Any,
    session: EditorSession | None,
    field_index: int,
    saved_name: str,
    request: RegionDeleteRequest,
) -> bool:
    if session is None:
        return False
    session.undo_history.push(session.state, session.current_filename, status_summary=session.status_summary)
    session.redo_history.clear()
    session.state = AudioEditState(source_file=saved_name)
    session.current_filename = saved_name
    session.field_index = field_index
    session.status_summary = region_operation_status_summary(request)
    session.next_status_summary = ""
    session.pending_status = PendingEditorStatus(field_index, message=session.status_summary)
    saved_path = existing_media_file_path(Path(editor.mw.col.media.dir()), saved_name)
    session.source_mtime_ns = saved_path.stat().st_mtime_ns if saved_path is not None else None
    session.processing = False
    session.cursor_ms = 0
    session.playback_active = False
    session.playback_paused = False
    should_redraw_graph = field_index in session.graph_active_fields or session.visualized_filename is not None
    if should_redraw_graph:
        session.visualized_filename = None
        session.visualized_duration_ms = None
        session.visualized_filenames_by_field.pop(field_index, None)
        session.visualized_durations_by_field.pop(field_index, None)
    return should_redraw_graph
