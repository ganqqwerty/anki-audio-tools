"""Audio processing and denoise behavior for the editor bridge."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from . import editor_special_transforms as _special_transforms
from .audio_state import AudioEditState, AudioProcessingConfig
from .diagnostics_runtime import capture_exception, new_operation_id, record_breadcrumb
from .editor_actions import (
    EditorCommandPayload,
    apply_processing_command,
    processing_config_for_command,
)
from .editor_conversion import convert_async as _convert_async
from .editor_media_replacement import (
    persist_generated_media,
    replace_first_sound_reference_in_field,
)
from .editor_processing_shared import (
    cancel_graph_analysis_for_processing as _cancel_graph_analysis_for_processing,
)
from .editor_processing_shared import (
    request_history_availability_after_edit as _request_history_availability_after_edit,
)
from .editor_processing_shared import (
    sync_history_availability as _sync_history_availability,
)
from .editor_reload_status import reload_editor_with_pending_status
from .editor_session import (
    EditorProcessingGuard,
    EditorSession,
    begin_processing_guard,
    clear_processing_for_stale_guard,
    is_current_processing_guard,
    processing_guard_matches_editor,
)
from .editor_status import command_status_summary
from .error_codes import (
    AQE_AUDIO_PROCESSING_FAILED,
    AQE_MEDIA_CURRENT_FIELD_AUDIO_MISSING,
    coded_error,
)
from .i18n import t
from .permission_guidance import message_with_permission_guidance

if TYPE_CHECKING:
    from .editor_deps_protocols import ProcessingDeps

logger = logging.getLogger(__name__)
convert_async = _convert_async
denoise_standard_async = _special_transforms.denoise_standard_async
dpdfnet_async = _special_transforms.dpdfnet_async
log_special_transform_failure = _special_transforms.log_special_transform_failure
pitch_hum_async = _special_transforms.pitch_hum_async
reduce_size_async = _special_transforms.reduce_size_async
record_dpdfnet_failure_context = _special_transforms.record_dpdfnet_failure_context
record_rnnoise_failure_context = _special_transforms.record_rnnoise_failure_context
record_spleeter_failure_context = _special_transforms.record_spleeter_failure_context
replace_current_field_after_noise_removal = _special_transforms.replace_current_field_after_noise_removal
rnnoise_async = _special_transforms.rnnoise_async
run_special_audio_transform_async = _special_transforms.run_special_audio_transform_async
voice_only_async = _special_transforms.voice_only_async


def update_state_and_render(editor: Any, command: str | EditorCommandPayload, deps: ProcessingDeps) -> None:
    """Apply a frontend processing command and start the render worker."""
    existing = deps.sessions.get(editor)
    if existing and existing.processing:
        deps.eval_status(editor, deps.still_processing_message, kind="processing")
        return
    if existing and existing.playback_preparing:
        deps.stop_session_playback(existing)
    session, source_path = deps.session_and_source(editor)
    _cancel_graph_analysis_for_processing(editor, session, deps)
    config = AudioProcessingConfig.from_config(deps.config(editor))
    state = session.state or AudioEditState(source_file=source_path.name)
    updated_state = apply_processing_command(command, state, config)
    if updated_state is None:
        session.next_status_summary = ""
        deps.set_busy(editor, False)
        return
    session.next_status_summary = command_status_summary(command, config)
    deps.render_and_replace_async(
        editor,
        session,
        source_path,
        updated_state,
        processing_config_for_command(command, config),
    )


def render_and_replace_async(
    editor: Any,
    session: EditorSession,
    source_path: Path,
    updated_state: AudioEditState,
    config: AudioProcessingConfig,
    deps: ProcessingDeps,
) -> None:
    """Render an edited audio file and replace the current field on completion."""
    operation_id = new_operation_id("render")
    record_breadcrumb(
        "editor.render.started",
        source="editor",
        operation="editor.render",
        operation_id=operation_id,
        context={"source_filename": source_path.name},
        flush=True,
    )
    deps.stop_session_playback(session)
    session.post_edit_playback_generation += 1
    session.processing = True
    field_index = session.field_index if session.field_index is not None else deps.current_field_index(editor)
    guard_filename = session.current_filename or source_path.name
    guard = begin_processing_guard(session, field_index=int(field_index), source_filename=guard_filename)
    session.playback_active = False
    session.playback_paused = False
    deps.set_busy(editor, True, t("editor.status.processing"))
    deps.eval_playback_state(editor, guard.field_index, "stopped", session.cursor_ms)

    def _run() -> None:
        _run_standard_render_worker(editor, session, source_path, updated_state, config, guard, operation_id, deps)

    deps.threading.Thread(target=_run, daemon=True).start()


def _run_standard_render_worker(
    editor: Any,
    session: EditorSession,
    source_path: Path,
    updated_state: AudioEditState,
    config: AudioProcessingConfig,
    guard: EditorProcessingGuard,
    operation_id: str,
    deps: ProcessingDeps,
) -> None:
    output_path: Path | None = None
    try:
        desired_name = deps.make_output_filename(source_path.name, output_format=config.output_format)
        output_path = deps.temp_final_path(desired_name)

        def _show_command(process_command: tuple[str, ...]) -> None:
            rendered = deps.format_ffmpeg_command(process_command)
            status_message = t("editor.status.processing_ffmpeg")
            command_text = ""
            if config.show_ffmpeg_commands:
                status_message = f"{status_message}: {rendered}"
                command_text = rendered
            deps.main(editor, lambda: deps.set_busy(editor, True, status_message, command_text))

        deps.render_audio(
            source_path,
            updated_state,
            config,
            output_path=output_path,
            on_command=_show_command,
            artifact_root=deps.artifact_root(editor),
        )
        _schedule_standard_render_finish(editor, session, updated_state, desired_name, output_path, guard, deps)
    except Exception as exc:
        _handle_standard_render_worker_failure(editor, session, source_path, updated_state, output_path, guard, operation_id, exc, deps)


def _schedule_standard_render_finish(
    editor: Any,
    session: EditorSession,
    updated_state: AudioEditState,
    desired_name: str,
    output_path: Path,
    guard: EditorProcessingGuard,
    deps: ProcessingDeps,
) -> None:
    if not is_current_processing_guard(session, guard):
        shutil.rmtree(output_path.parent, ignore_errors=True)
        deps.main(editor, lambda: _discard_stale_standard_render(editor, guard, deps))
        return

    def _finish() -> None:
        try:
            deps.replace_current_field_after_render(
                editor,
                updated_state,
                desired_name,
                guard=guard,
                output_path=output_path,
            )
        finally:
            shutil.rmtree(output_path.parent, ignore_errors=True)

    deps.main(editor, _finish)


def _handle_standard_render_worker_failure(
    editor: Any,
    session: EditorSession,
    source_path: Path,
    updated_state: AudioEditState,
    output_path: Path | None,
    guard: EditorProcessingGuard,
    operation_id: str,
    exc: Exception,
    deps: ProcessingDeps,
) -> None:
    if output_path is not None:
        shutil.rmtree(output_path.parent, ignore_errors=True)
    message = message_with_permission_guidance(str(exc), exc)
    capture_exception(
        "editor.worker.render",
        exc,
        operation="editor.render",
        operation_id=operation_id,
        user_message=message,
        context={"source_path": str(source_path), "state": updated_state},
        log=logger,
    )
    if not is_current_processing_guard(session, guard):
        deps.main(editor, lambda: _discard_stale_standard_render(editor, guard, deps))
        return
    deps.main(editor, lambda: deps.render_failed(editor, message, guard=guard))


def _discard_stale_standard_render(editor: Any, guard: EditorProcessingGuard, deps: ProcessingDeps) -> None:
    if clear_processing_for_stale_guard(deps.sessions.get(editor), guard):
        deps.set_busy(editor, False)


def replace_current_field_after_render(
    editor: Any,
    updated_state: AudioEditState,
    saved_name: str,
    deps: ProcessingDeps,
    *,
    guard: EditorProcessingGuard | None = None,
    output_path: Path | None = None,
) -> None:
    """Replace the current field after a successful standard render."""
    session = deps.sessions.get(editor)
    if not _accept_guarded_render_replacement(editor, session, guard, deps):
        return
    saved_name = persist_generated_media(editor, saved_name, output_path, deps)
    field_index = _render_replacement_field_index(editor, session, deps)
    old_field_html, new_field_html, old_filename = replace_first_sound_reference_in_field(
        editor, field_index=field_index, saved_name=saved_name, missing_message=deps.current_field_audio_missing,
    )
    old_state = session.state if session else None
    status_summary = session.next_status_summary if session else ""
    try:
        deps.record_standard_persistent_undo(
            editor,
            field_index=field_index,
            old_field_html=old_field_html,
            new_field_html=new_field_html,
            old_filename=old_filename,
            new_filename=saved_name,
            old_state=old_state,
            new_state=updated_state,
            status_summary=status_summary,
        )
    except Exception:
        logger.debug(
            "Could not record persistent undo operation field_index=%s old=%s new=%s.",
            field_index,
            old_filename,
            saved_name,
            exc_info=True,
        )
    should_redraw_graph = _replace_standard_render_session_state(session, field_index, saved_name, updated_state)
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
    deps.eval_playback_state(editor, field_index, "stopped", 0)
    if should_redraw_graph:
        deps.request_graph_redraw(editor, saved_name)
    else:
        deps.set_busy(editor, False)


def _accept_guarded_render_replacement(
    editor: Any,
    session: EditorSession | None,
    guard: EditorProcessingGuard | None,
    deps: ProcessingDeps,
) -> bool:
    if guard is None or processing_guard_matches_editor(editor, session, guard, deps):
        return True
    if clear_processing_for_stale_guard(session, guard):
        deps.set_busy(editor, False)
    return False



def _render_replacement_field_index(editor: Any, session: EditorSession | None, deps: ProcessingDeps) -> int:
    if session and session.field_index is not None:
        return int(session.field_index)
    return int(deps.current_field_index(editor))


def _replace_standard_render_session_state(
    session: EditorSession | None,
    field_index: int,
    saved_name: str,
    updated_state: AudioEditState,
) -> bool:
    if session is None:
        return False
    session.undo_history.push(session.state, session.current_filename, status_summary=session.status_summary)
    session.redo_history.clear()
    session.state = updated_state
    session.current_filename = saved_name
    session.field_index = field_index
    session.status_summary = session.next_status_summary or session.status_summary
    session.next_status_summary = ""
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


# noinspection PyInconsistentReturns
def write_generated_media(editor: Any, desired_name: str, output_path: Path, _deps: ProcessingDeps) -> str:
    """Persist a rendered media file through Anki's media manager."""
    with output_path.open("rb") as file:
        return cast(str, editor.mw.col.media.write_data(desired_name, file.read()))


def render_failed(
    editor: Any,
    message: str,
    deps: ProcessingDeps,
    *,
    guard: EditorProcessingGuard | None = None,
) -> None:
    """Reset editor processing state and report a render failure."""
    session = deps.sessions.get(editor)
    if guard is not None and not processing_guard_matches_editor(editor, session, guard, deps):
        if clear_processing_for_stale_guard(session, guard):
            deps.set_busy(editor, False)
        return
    if session:
        session.processing = False
        session.playback_active = False
        session.playback_paused = False
        session.next_status_summary = ""
        session.pending_status = None
    deps.set_busy(editor, False)
    code = (
        AQE_MEDIA_CURRENT_FIELD_AUDIO_MISSING
        if message == deps.current_field_audio_missing
        else AQE_AUDIO_PROCESSING_FAILED
    )
    deps.eval_status(editor, coded_error(code, message), kind="error")
