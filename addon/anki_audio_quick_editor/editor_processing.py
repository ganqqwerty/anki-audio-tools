"""Audio processing and denoise behavior for the editor bridge."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any, cast

from . import editor_special_transforms as _special_transforms
from .audio_state import AudioEditState, AudioProcessingConfig
from .diagnostics_runtime import capture_exception, new_operation_id, record_breadcrumb
from .editor_actions import (
    EditorCommandPayload,
    apply_processing_command,
    processing_config_for_command,
)
from .editor_conversion import convert_async as _convert_async
from .editor_processing_shared import (
    cancel_graph_analysis_for_processing as _cancel_graph_analysis_for_processing,
)
from .editor_processing_shared import (
    request_history_availability_after_edit as _request_history_availability_after_edit,
)
from .editor_processing_shared import (
    sync_history_availability as _sync_history_availability,
)
from .editor_session import EditorSession, PendingEditorStatus
from .editor_status import command_status_summary
from .errors import AudioProcessingError
from .i18n import t
from .sound_refs import replace_sound_reference, select_first_sound_reference

logger = logging.getLogger(__name__)
convert_async = _convert_async
denoise_standard_async = _special_transforms.denoise_standard_async
dpdfnet_async = _special_transforms.dpdfnet_async
log_special_transform_failure = _special_transforms.log_special_transform_failure
pitch_hum_async = _special_transforms.pitch_hum_async
record_dpdfnet_failure_context = _special_transforms.record_dpdfnet_failure_context
record_rnnoise_failure_context = _special_transforms.record_rnnoise_failure_context
record_spleeter_failure_context = _special_transforms.record_spleeter_failure_context
replace_current_field_after_noise_removal = _special_transforms.replace_current_field_after_noise_removal
rnnoise_async = _special_transforms.rnnoise_async
run_special_audio_transform_async = _special_transforms.run_special_audio_transform_async
voice_only_async = _special_transforms.voice_only_async


def update_state_and_render(editor: Any, command: str | EditorCommandPayload, deps: Any) -> None:
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
    deps: Any,
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
    session.playback_active = False
    session.playback_paused = False
    deps.set_busy(editor, True, t("editor.status.processing"))
    deps.eval_playback_state(editor, session.field_index, "stopped", session.cursor_ms)

    def _run() -> None:
        try:
            desired_name = deps.make_output_filename(source_path.name)
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
            saved_name = deps.write_generated_media(editor, desired_name, output_path)
            deps.main(editor, lambda: deps.replace_current_field_after_render(editor, updated_state, saved_name))
            shutil.rmtree(output_path.parent, ignore_errors=True)
        except Exception as exc:
            message = str(exc)
            capture_exception(
                "editor.worker.render",
                exc,
                operation="editor.render",
                operation_id=operation_id,
                user_message=message,
                context={"source_path": str(source_path), "state": updated_state},
                log=logger,
            )
            deps.main(editor, lambda: deps.render_failed(editor, message))

    deps.threading.Thread(target=_run, daemon=True).start()


def replace_current_field_after_render(
    editor: Any,
    updated_state: AudioEditState,
    saved_name: str,
    deps: Any,
) -> None:
    """Replace the current field after a successful standard render."""
    session = deps.sessions.get(editor)
    field_index = int(session.field_index) if session and session.field_index is not None else deps.current_field_index(editor)
    field_html = editor.note.fields[field_index]
    selection = select_first_sound_reference(field_html)
    if selection.selected is None:
        raise AudioProcessingError(deps.current_field_audio_missing)
    deps.dispose_editor_frontend_controls(editor)
    editor.note.fields[field_index] = replace_sound_reference(field_html, selection.selected, saved_name)
    should_redraw_graph = False
    if session:
        session.undo_history.push(session.state, session.current_filename, status_summary=session.status_summary)
        session.redo_history.clear()
        session.state = updated_state
        session.current_filename = saved_name
        session.field_index = field_index
        session.status_summary = session.next_status_summary or session.status_summary
        session.next_status_summary = ""
        session.pending_status = PendingEditorStatus(field_index, message=session.status_summary)
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
    editor.loadNote(focusTo=field_index)
    if session:
        session.pending_status = None
    _sync_history_availability(editor, session, deps)
    _request_history_availability_after_edit(editor, session, deps)
    deps.eval_playback_state(editor, field_index, "stopped", 0)
    if should_redraw_graph:
        deps.request_graph_redraw(editor, saved_name)
    else:
        deps.set_busy(editor, False)
    deps.request_playback_after_edit(editor, field_index)


# noinspection PyInconsistentReturns
def write_generated_media(editor: Any, desired_name: str, output_path: Path, _deps: Any) -> str:
    """Persist a rendered media file through Anki's media manager."""
    with output_path.open("rb") as file:
        return cast(str, editor.mw.col.media.write_data(desired_name, file.read()))


def render_failed(editor: Any, message: str, deps: Any) -> None:
    """Reset editor processing state and report a render failure."""
    session = deps.sessions.get(editor)
    if session:
        session.processing = False
        session.playback_active = False
        session.playback_paused = False
        session.next_status_summary = ""
        session.pending_status = None
    deps.set_busy(editor, False)
    deps.eval_status(editor, message, kind="error")
