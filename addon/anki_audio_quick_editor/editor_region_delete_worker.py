"""Background worker helpers for editor selected-region operations."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

from .audio_state import AudioProcessingConfig
from .diagnostics_runtime import capture_exception
from .editor_region_delete_request import (
    REGION_KEEP_OPERATION,
    region_operation_command_status,
)
from .editor_session import (
    EditorProcessingGuard,
    EditorSession,
    RegionDeleteRequest,
    clear_processing_for_stale_guard,
    is_current_processing_guard,
)
from .permission_guidance import message_with_permission_guidance

logger = logging.getLogger(__name__)


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


def run_region_delete_worker(
    editor: Any,
    session: EditorSession,
    source_path: Path,
    request: RegionDeleteRequest,
    config: AudioProcessingConfig,
    guard: EditorProcessingGuard,
    started_at: float,
    operation_id: str,
    deps: Any,
) -> None:
    """Render a region operation and schedule a guarded main-thread completion."""
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

        result = render_region_operation(deps, source_path, request, config, output_path, _show_command)
        _schedule_region_delete_finish(editor, session, request, desired_name, output_path, result.duration_ms, started_at, guard, deps)
    except Exception as exc:
        _handle_region_delete_worker_failure(editor, session, request, output_path, guard, operation_id, exc, deps)


def _schedule_region_delete_finish(
    editor: Any,
    session: EditorSession,
    request: RegionDeleteRequest,
    desired_name: str,
    output_path: Path,
    output_duration_ms: int | None,
    started_at: float,
    guard: EditorProcessingGuard,
    deps: Any,
) -> None:
    if not is_current_processing_guard(session, guard):
        shutil.rmtree(output_path.parent, ignore_errors=True)
        deps.main(editor, lambda: _discard_stale_region_delete(editor, guard, deps))
        return

    def _finish() -> None:
        try:
            deps.replace_current_field_after_region_delete(
                editor,
                request,
                desired_name,
                output_duration_ms,
                started_at,
                guard=guard,
                output_path=output_path,
            )
        finally:
            shutil.rmtree(output_path.parent, ignore_errors=True)

    deps.main(editor, _finish)


def _handle_region_delete_worker_failure(
    editor: Any,
    session: EditorSession,
    request: RegionDeleteRequest,
    output_path: Path | None,
    guard: EditorProcessingGuard,
    operation_id: str,
    exc: Exception,
    deps: Any,
) -> None:
    if output_path is not None:
        shutil.rmtree(output_path.parent, ignore_errors=True)
    message = message_with_permission_guidance(str(exc), exc)
    capture_exception(
        "editor.worker.region_delete",
        exc,
        operation="editor.region_delete",
        operation_id=operation_id,
        user_message=message,
        context=region_delete_log_context(request),
        log=logger,
    )
    if not is_current_processing_guard(session, guard):
        deps.main(editor, lambda: _discard_stale_region_delete(editor, guard, deps))
        return
    deps.main(editor, lambda: deps.render_failed(editor, message, guard=guard))


def _discard_stale_region_delete(editor: Any, guard: EditorProcessingGuard, deps: Any) -> None:
    if clear_processing_for_stale_guard(deps.sessions.get(editor), guard):
        deps.set_busy_for_field(editor, guard.field_index, False)


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
