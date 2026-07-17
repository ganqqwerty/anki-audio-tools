"""Region-delete behavior for the editor bridge."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from . import editor_region_delete_request as _request
from .audio_state import AudioEditState, AudioProcessingConfig
from .diagnostics_runtime import capture_exception, new_operation_id, record_breadcrumb
from .editor_media_replacement import (
    persist_generated_media,
    replace_first_sound_reference_in_field,
)
from .editor_processing_guard import (
    EditorProcessingGuard,
    clear_processing_for_stale_guard,
    processing_guard_matches_editor,
)
from .editor_processing_shared import (
    request_history_availability_after_edit as _request_history_availability_after_edit,
)
from .editor_processing_shared import (
    sync_history_availability as _sync_history_availability,
)
from .editor_region_delete_request import (
    RegionDeleteRequest,
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
from .editor_reload_status import reload_editor_with_pending_status
from .editor_session import EditorSession
from .editor_status import region_operation_status_summary
from .error_codes import (
    AQE_AUDIO_PROCESSING_FAILED,
    AQE_GRAPH_ANALYSIS_FAILED,
    coded_error,
)
from .i18n import t
from .media_paths import existing_media_file_path, media_filenames_match
from .permission_guidance import message_with_permission_guidance

if TYPE_CHECKING:
    from .editor_deps_protocols import RegionDeleteDeps

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


def delete_selection_from_frontend(editor: Any, deps: RegionDeleteDeps) -> None:
    """Pop and process a pending frontend region-delete request."""
    deps.eval_with_callback(
        editor,
        "window.__aqePopPendingRegionDeleteRequest ? "
        "window.__aqePopPendingRegionDeleteRequest() : null",
        lambda request: deps.delete_selection_with_request(editor, request),
    )


def delete_selection_with_request(editor: Any, request: Any, deps: RegionDeleteDeps) -> None:
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
    if parsed.post_edit_autoplay is not None:
        session.post_edit_autoplay_by_field[parsed.field_index] = parsed.post_edit_autoplay
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
    deps: RegionDeleteDeps,
) -> None:
    """Render a media file with the requested region removed."""
    operation_id = new_operation_id("region")
    started_at = time.monotonic()
    guard = session.begin_processing(
        field_index=request.field_index,
        source_filename=request.source_filename,
    )
    session.cursor_ms = request.cursor_ms
    deps.set_busy_for_field(editor, request.field_index, True, region_operation_busy_message(request))
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
    deps: RegionDeleteDeps,
    *,
    guard: EditorProcessingGuard | None = None,
    output_path: Path | None = None,
) -> None:
    """Replace the field after a successful region-delete render."""
    session = deps.sessions.get(editor)
    if not _accept_guarded_region_replacement(editor, session, guard, deps):
        return
    try:
        saved_name = persist_generated_media(editor, saved_name, output_path, deps)
        field_index = request.field_index
        old_field_html, new_field_html, old_filename = replace_first_sound_reference_in_field(
            editor,
            field_index=field_index,
            saved_name=saved_name,
            missing_message=deps.current_field_audio_missing,
            expected_filename=request.source_filename,
            mismatch_message=t("editor.status.graph_audio_mismatch"),
        )
        old_state = session.state if session is not None else None
        should_redraw_graph = _replace_region_delete_session_state(editor, session, field_index, saved_name, request)
        try:
            deps.record_standard_persistent_undo(
                editor,
                field_index=field_index,
                old_field_html=old_field_html,
                new_field_html=new_field_html,
                old_filename=old_filename,
                new_filename=saved_name,
                old_state=old_state,
                new_state=session.state if session is not None else AudioEditState(source_file=saved_name),
                status_summary=session.status_summary if session is not None else region_operation_status_summary(request),
            )
        except Exception:
            logger.debug(
                "Could not record persistent undo operation for region delete field_index=%s old=%s new=%s.",
                field_index,
                old_filename,
                saved_name,
                exc_info=True,
            )
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
        deps.request_playback_after_edit(
            editor,
            field_index,
            require_graph_redraw=should_redraw_graph,
        )
        reload_editor_with_pending_status(
            editor,
            session,
            field_index,
            message=session.status_summary if session is not None else "",
            deps=deps,
        )
        _sync_history_availability(editor, session, deps)
        _request_history_availability_after_edit(editor, session, deps)
        if should_redraw_graph:
            deps.request_graph_redraw(editor, saved_name)
        else:
            deps.set_busy_for_field(editor, field_index, False)
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
    deps: RegionDeleteDeps,
) -> bool:
    if guard is None or processing_guard_matches_editor(editor, session, guard, deps):
        return True
    if clear_processing_for_stale_guard(session, guard):
        deps.set_busy_for_field(editor, guard.field_index, False)
    return False


def _replace_region_delete_session_state(
    editor: Any,
    session: EditorSession | None,
    field_index: int,
    saved_name: str,
    request: RegionDeleteRequest,
) -> bool:
    if session is None:
        return False
    session.field_index = field_index
    saved_path = existing_media_file_path(Path(editor.mw.col.media.dir()), saved_name)
    mtime = saved_path.stat().st_mtime_ns if saved_path is not None else None
    return session.apply_edit_result(
        AudioEditState(source_file=saved_name),
        saved_name,
        region_operation_status_summary(request),
        update_source_mtime=True,
        new_source_mtime=mtime,
    )
