"""Region-delete behavior for the editor bridge."""

from __future__ import annotations

import logging
import shutil
import time
from pathlib import Path
from typing import Any

from . import editor_region_delete_request as _request
from .audio_state import AudioEditState, AudioProcessingConfig
from .diagnostics_runtime import capture_exception, new_operation_id, record_breadcrumb
from .editor_region_delete_request import (
    REGION_KEEP_OPERATION,
)
from .editor_region_delete_request import (
    parse_region_delete_request as _parse_region_delete_request,
)
from .editor_session import (
    EditorSession,
    PendingEditorStatus,
    RegionDeleteRequest,
)
from .editor_status import region_operation_status_summary
from .errors import AudioProcessingError
from .i18n import t
from .media_paths import existing_media_file_path, media_filenames_match
from .sound_refs import replace_sound_reference, select_first_sound_reference

logger = logging.getLogger(__name__)
parse_region_delete_request = _request.parse_region_delete_request
required_region_delete_values = _request.required_region_delete_values
region_delete_source_filename = _request.region_delete_source_filename
region_delete_trigger = _request.region_delete_trigger
region_operation_busy_message = _request.region_operation_busy_message
region_operation_command_status = _request.region_operation_command_status
region_operation_whole_clip_message = _request.region_operation_whole_clip_message


def _sync_history_availability(editor: Any, session: Any, deps: Any) -> None:
    if session is None:
        return
    deps.eval_history_availability(
        editor,
        session.field_index,
        bool(session.undo_history.entries),
        bool(session.redo_history.entries),
    )


def _request_history_availability_after_edit(editor: Any, session: Any, deps: Any) -> None:
    if session is None:
        return
    deps.request_history_availability_after_edit(
        editor,
        session.field_index,
        bool(session.undo_history.entries),
        bool(session.redo_history.entries),
    )

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
        deps.eval_status(editor, t("editor.status.region_read_failed"), kind="error")
        return
    existing = deps.sessions.get(editor)
    if existing and deps.is_busy(existing):
        deps.eval_status(editor, deps.still_processing_message, kind="processing")
        return
    active_field = deps.current_field_index(editor)
    if active_field != parsed.field_index:
        deps.set_busy_for_field(editor, parsed.field_index, False)
        deps.eval_status(editor, t("editor.status.graph_inactive"), kind="error")
        return
    resolved = deps.resolve_requested_field_media(editor, parsed.field_index, parsed.source_filename)
    if resolved is None:
        deps.set_busy_for_field(editor, parsed.field_index, False)
        deps.eval_status(editor, t("editor.status.graph_audio_mismatch"), kind="error")
        return
    session, current_path = deps.current_media_path(editor)
    if not media_filenames_match(current_path.name, parsed.source_filename):
        deps.set_busy_for_field(editor, parsed.field_index, False)
        deps.eval_status(editor, t("editor.status.graph_audio_mismatch"), kind="error")
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




def render_region_operation(
    deps: Any,
    source_path: Path,
    request: RegionDeleteRequest,
    config: AudioProcessingConfig,
    output_path: Path,
    on_command: Any,
) -> Any:
    """Render the requested selected-region operation."""
    renderer = (
        deps.render_audio_region_kept
        if request.operation == REGION_KEEP_OPERATION
        else deps.render_audio_region_deleted
    )
    return renderer(
        source_path,
        request.selection_start_ms,
        request.selection_end_ms,
        config,
        output_path=output_path,
        on_command=on_command,
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
        output_path: Path | None = None
        try:
            desired_name = deps.make_output_filename(source_path.name)
            output_path = deps.temp_final_path(desired_name)

            def _show_command(command: tuple[str, ...]) -> None:
                rendered = deps.format_ffmpeg_command(command)
                status_message = region_operation_command_status(request)
                command_text = ""
                if config.show_ffmpeg_commands:
                    status_message = f"{status_message}: {rendered}"
                    command_text = rendered
                deps.main(
                    editor,
                    lambda: deps.set_busy_for_field(
                        editor,
                        request.field_index,
                        True,
                        status_message,
                        command_text,
                    ),
                )

            result = render_region_operation(
                deps,
                source_path,
                request,
                config,
                output_path,
                _show_command,
            )
            with output_path.open("rb") as file:
                saved_name = editor.mw.col.media.write_data(desired_name, file.read())
            deps.main(
                editor,
                lambda: deps.replace_current_field_after_region_delete(
                    editor,
                    request,
                    saved_name,
                    result.duration_ms,
                    started_at,
                ),
            )
        except Exception as exc:
            capture_exception(
                "editor.worker.region_delete",
                exc,
                operation="editor.region_delete",
                operation_id=operation_id,
                user_message=str(exc),
                context=region_delete_log_context(request),
                log=logger,
            )
            message = str(exc)
            deps.main(editor, lambda: deps.render_failed(editor, message))
        finally:
            if output_path is not None:
                shutil.rmtree(output_path.parent, ignore_errors=True)

    deps.threading.Thread(target=_run, daemon=True).start()


def replace_current_field_after_region_delete(
    editor: Any,
    request: RegionDeleteRequest,
    saved_name: str,
    output_duration_ms: int | None,
    started_at: float,
    deps: Any,
) -> None:
    """Replace the field after a successful region-delete render."""
    try:
        field_index = request.field_index
        field_html = editor.note.fields[field_index]
        selection = select_first_sound_reference(field_html)
        if selection.selected is None:
            raise AudioProcessingError(deps.current_field_audio_missing)
        if not media_filenames_match(selection.selected.filename, request.source_filename):
            raise AudioProcessingError(t("editor.status.graph_audio_mismatch"))
        deps.dispose_editor_frontend_controls(editor)
        editor.note.fields[field_index] = replace_sound_reference(field_html, selection.selected, saved_name)
        session = deps.sessions.get(editor)
        should_redraw_graph = False
        if session:
            session.undo_history.push(
                session.state,
                session.current_filename,
                status_summary=session.status_summary,
            )
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
        capture_exception(
            "editor.main.region_delete_replacement",
            exc,
            operation="editor.region_delete",
            user_message=str(exc),
            context=region_delete_log_context(request),
            log=logger,
        )
        deps.render_failed(editor, str(exc))


def region_delete_log_context(request: RegionDeleteRequest) -> dict[str, object]:
    """Return structured logging context for a region-delete request."""
    return {
        "field_index": request.field_index,
        "source_filename": request.source_filename,
        "selection_start_ms": request.selection_start_ms,
        "selection_end_ms": request.selection_end_ms,
        "duration_ms": request.duration_ms,
        "trigger": request.trigger,
        "playback_active": request.playback_active,
        "operation": request.operation,
    }
