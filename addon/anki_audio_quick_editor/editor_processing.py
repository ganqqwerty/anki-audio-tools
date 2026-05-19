"""Audio processing and denoise behavior for the editor bridge."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any, Callable

from .audio_state import AudioEditState, AudioProcessingConfig
from .diagnostics_runtime import capture_exception, new_operation_id, record_breadcrumb
from .editor_actions import (
    EditorCommandPayload,
    apply_processing_command,
    processing_config_for_command,
)
from .editor_session import EditorSession
from .errors import AudioProcessingError
from .sound_refs import (
    replace_sound_reference,
    safe_media_basename,
    select_first_sound_reference,
)
from .support import (
    format_rnnoise_support_log_block,
    latest_rnnoise_support_incident,
    record_latest_rnnoise_support_incident,
)

logger = logging.getLogger(__name__)


def update_state_and_render(editor: Any, command: str | EditorCommandPayload, deps: Any) -> None:
    """Apply a frontend processing command and start the render worker."""
    existing = deps.sessions.get(editor)
    if existing and deps.is_busy(existing):
        deps.eval_status(editor, deps.still_processing_message, kind="processing")
        return
    session, source_path = deps.session_and_source(editor)
    config = AudioProcessingConfig.from_config(deps.config(editor))
    state = session.state or AudioEditState(source_file=source_path.name)
    updated_state = apply_processing_command(command, state, config)
    if updated_state is None:
        deps.set_busy(editor, False)
        return
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
    session.processing = True
    session.playback_active = False
    session.playback_paused = False
    deps.set_busy(editor, True, "Processing...")
    deps.eval_playback_state(editor, session.field_index, "stopped", session.cursor_ms)

    def _run() -> None:
        try:
            desired_name = deps.make_output_filename(source_path.name)
            output_path = deps.temp_final_path(desired_name)

            def _show_command(command: tuple[str, ...]) -> None:
                rendered = deps.format_ffmpeg_command(command)
                status_message = "Processing with ffmpeg"
                command_text = ""
                if config.show_ffmpeg_commands:
                    status_message = f"{status_message}: {rendered}"
                    command_text = rendered
                deps.main(
                    editor,
                    lambda: deps.set_busy(editor, True, status_message, command_text),
                )

            deps.render_audio(
                source_path,
                updated_state,
                config,
                output_path=output_path,
                on_command=_show_command,
                artifact_root=deps.artifact_root(editor),
            )
            with output_path.open("rb") as file:
                saved_name = editor.mw.col.media.write_data(desired_name, file.read())
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
    field_index = deps.current_field_index(editor)
    field_html = editor.note.fields[field_index]
    selection = select_first_sound_reference(field_html)
    if selection.selected is None:
        raise AudioProcessingError(deps.current_field_audio_missing)
    deps.dispose_editor_frontend_controls(editor)
    editor.note.fields[field_index] = replace_sound_reference(field_html, selection.selected, saved_name)
    session = deps.sessions.get(editor)
    should_redraw_graph = False
    if session:
        session.undo_history.push(session.state, session.current_filename)
        session.redo_history.clear()
        session.state = updated_state
        session.current_filename = saved_name
        session.field_index = field_index
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
    deps.eval_status(editor, f"Updated field to {saved_name}")
    deps.eval_playback_state(editor, field_index, "stopped", 0)
    if should_redraw_graph:
        deps.request_graph_redraw(editor)
    else:
        deps.set_busy(editor, False)


def render_failed(editor: Any, message: str, deps: Any) -> None:
    """Reset editor processing state and report a render failure."""
    session = deps.sessions.get(editor)
    if session:
        session.processing = False
        session.playback_active = False
        session.playback_paused = False
    deps.set_busy(editor, False)
    deps.eval_status(editor, message, kind="error")


def denoise_standard_async(editor: Any, deps: Any) -> None:
    """Start standard DeepFilter denoise for the current media."""
    deps.run_special_audio_transform_async(
        editor,
        label="Denoising with Standard",
        failure_log_label="standard denoise failed",
        renderer=deps.render_noise_reduced_audio,
    )


def rnnoise_async(editor: Any, deps: Any) -> None:
    """Start RNNoise denoise for the current media."""
    deps.run_special_audio_transform_async(
        editor,
        label="Denoising with RNNoise",
        failure_log_label="rnnoise denoise failed",
        renderer=deps.render_rnnoise_audio,
        support_hint=deps.support_report_hint,
        failure_context_recorder=deps.record_rnnoise_failure_context,
    )


def run_special_audio_transform_async(
    editor: Any,
    *,
    label: str,
    failure_log_label: str,
    renderer: Callable[..., Any],
    support_hint: str = "",
    failure_context_recorder: Callable[[Path, AudioProcessingConfig, Exception], None] | None = None,
    deps: Any,
) -> None:
    """Run a denoise transform and replace the current audio on completion."""
    operation_id = new_operation_id("transform")
    existing = deps.sessions.get(editor)
    if existing and deps.is_busy(existing):
        deps.eval_status(editor, deps.still_processing_message, kind="processing")
        return
    session, current_path = deps.current_media_path(editor)
    config = AudioProcessingConfig.from_config(deps.config(editor))
    deps.stop_session_playback(session)
    session.processing = True
    session.playback_active = False
    session.playback_paused = False
    deps.set_busy(editor, True, f"{label}...")
    deps.eval_playback_state(editor, session.field_index, "stopped", session.cursor_ms)
    record_breadcrumb(
        "editor.special_transform.started",
        source="editor",
        operation=f"editor.{failure_log_label}",
        operation_id=operation_id,
        context={"label": label, "source_filename": current_path.name},
        flush=True,
    )

    def _run() -> None:
        output_path: Path | None = None
        try:
            desired_name = deps.make_output_filename(current_path.name)
            output_path = deps.temp_final_path(desired_name)

            def _show_command(command: tuple[str, ...]) -> None:
                rendered = deps.format_ffmpeg_command(command)
                status_message = label
                command_text = ""
                if config.show_ffmpeg_commands:
                    status_message = f"{status_message}: {rendered}"
                    command_text = rendered
                deps.main(editor, lambda: deps.set_busy(editor, True, status_message, command_text))

            renderer(
                current_path,
                config,
                output_path=output_path,
                on_command=_show_command,
            )
            with output_path.open("rb") as file:
                saved_name = editor.mw.col.media.write_data(desired_name, file.read())
            deps.main(editor, lambda: deps.replace_current_field_after_noise_removal(editor, saved_name))
        except Exception as exc:
            message = str(exc)
            rendered_message = message
            if failure_context_recorder is not None:
                failure_context_recorder(current_path, config, exc)
            deps.log_special_transform_failure(failure_log_label, message)
            capture_exception(
                f"editor.worker.{failure_log_label}",
                exc,
                operation=f"editor.{failure_log_label}",
                operation_id=operation_id,
                user_message=message,
                context={"source_path": str(current_path), "label": label},
                log=logger,
            )
            if support_hint:
                rendered_message = f"{message} {support_hint}"
            deps.main(editor, lambda: deps.render_failed(editor, rendered_message))
        finally:
            if output_path is not None:
                shutil.rmtree(output_path.parent, ignore_errors=True)

    deps.threading.Thread(target=_run, daemon=True).start()


def replace_current_field_after_noise_removal(editor: Any, saved_name: str, deps: Any) -> None:
    """Replace the current field after a successful denoise transform."""
    field_index = deps.current_field_index(editor)
    field_html = editor.note.fields[field_index]
    selection = select_first_sound_reference(field_html)
    if selection.selected is None:
        raise AudioProcessingError(deps.current_field_audio_missing)
    deps.dispose_editor_frontend_controls(editor)
    editor.note.fields[field_index] = replace_sound_reference(field_html, selection.selected, saved_name)
    session = deps.sessions.get(editor)
    should_redraw_graph = False
    if session:
        session.undo_history.push(session.state, session.current_filename)
        session.redo_history.clear()
        session.state = AudioEditState(source_file=saved_name)
        session.current_filename = saved_name
        session.field_index = field_index
        saved_path = Path(editor.mw.col.media.dir()) / safe_media_basename(saved_name)
        session.source_mtime_ns = saved_path.stat().st_mtime_ns if saved_path.is_file() else None
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
    deps.eval_status(editor, f"Updated field to {saved_name}")
    deps.eval_playback_state(editor, field_index, "stopped", 0)
    if should_redraw_graph:
        deps.request_graph_redraw(editor)
    else:
        deps.set_busy(editor, False)


def record_rnnoise_failure_context(
    source_path: Path,
    config: AudioProcessingConfig,
    exc: Exception,
) -> None:
    """Record enough RNNoise failure context for the diagnostics report."""
    record_latest_rnnoise_support_incident(
        operation="rnnoise_denoise",
        media_filename=source_path.name,
        source_path=str(source_path.resolve()),
        user_message=str(exc),
        exception_type=type(exc).__name__,
        ffmpeg_path=config.ffmpeg_path,
    )


def log_special_transform_failure(failure_log_label: str, message: str) -> None:
    """Log denoise failures, adding RNNoise diagnostics when available."""
    if failure_log_label == "rnnoise denoise failed":
        incident = latest_rnnoise_support_incident()
        if incident:
            logger.exception(
                "%s: %s\n%s",
                failure_log_label,
                message,
                format_rnnoise_support_log_block(incident),
            )
            return
        logger.exception("%s: %s", failure_log_label, message)
        return
    logger.exception("%s: %s", failure_log_label, message)
