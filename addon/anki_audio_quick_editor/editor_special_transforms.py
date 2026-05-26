"""Editor-side special transform orchestration."""

from __future__ import annotations

import logging
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable, cast

from .audio_formats import DEFAULT_OUTPUT_FORMAT
from .audio_state import AudioEditState, AudioProcessingConfig
from .diagnostics_runtime import new_operation_id, record_breadcrumb
from .editor_actions import EditorCommandPayload
from .editor_processing_shared import (
    cancel_graph_analysis_for_processing,
    request_history_availability_after_edit,
    reset_session_visualized_graph,
    resolved_field_index,
    sync_history_availability,
)
from .editor_session import (
    EditorProcessingGuard,
    EditorSession,
    PendingEditorStatus,
    begin_processing_guard,
    clear_processing_for_stale_guard,
    processing_guard_matches_editor,
)
from .editor_special_transform_worker import run_special_transform_worker
from .editor_status import command_status_summary
from .errors import AudioProcessingError
from .i18n import t
from .media_paths import existing_media_file_path
from .permission_guidance import message_with_macos_permission_guidance
from .prosody_settings import config_with_graph_settings
from .sound_refs import replace_sound_reference, select_first_sound_reference
from .support import (
    format_denoise_support_log_block,
    format_spleeter_support_log_block,
    latest_denoise_support_incident,
    latest_spleeter_support_incident,
    record_latest_denoise_support_incident,
    record_latest_spleeter_support_incident,
)

logger = logging.getLogger(__name__)


def denoise_standard_async(editor: Any, deps: Any) -> None:
    deps.run_special_audio_transform_async(
        editor,
        label=t("editor.status.denoising_standard"),
        failure_log_label="standard denoise failed",
        renderer=deps.render_noise_reduced_audio,
        command=EditorCommandPayload(command="aqe:denoise-standard"),
    )


def rnnoise_async(editor: Any, deps: Any) -> None:
    deps.run_special_audio_transform_async(
        editor,
        label=t("editor.status.denoising_rnnoise"),
        failure_log_label="rnnoise denoise failed",
        renderer=deps.render_rnnoise_audio,
        support_hint=deps.support_report_hint,
        failure_context_recorder=deps.record_rnnoise_failure_context,
        command=EditorCommandPayload(command="aqe:rnnoise"),
    )


def dpdfnet_async(
    editor: Any,
    command: EditorCommandPayload | None = None,
    deps: Any = None,
) -> None:
    if deps is None:
        deps = command
        command = EditorCommandPayload(command="aqe:dpdfnet")
    deps.run_special_audio_transform_async(
        editor,
        label=t("editor.status.denoising_dpdfnet"),
        failure_log_label="dpdfnet denoise failed",
        renderer=deps.render_dpdfnet_audio,
        support_hint=deps.support_report_hint,
        failure_context_recorder=deps.record_dpdfnet_failure_context,
        command=command,
    )


def voice_only_async(editor: Any, deps: Any) -> None:
    deps.run_special_audio_transform_async(
        editor,
        label=t("editor.status.extracting_voice"),
        failure_log_label="voice only failed",
        renderer=deps.render_voice_only_audio,
        support_hint=deps.support_report_hint,
        failure_context_recorder=deps.record_spleeter_failure_context,
        command=EditorCommandPayload(command="aqe:voice-only"),
    )


def pitch_hum_async(
    editor: Any,
    command: EditorCommandPayload | None = None,
    deps: Any = None,
) -> None:
    if deps is None:
        deps = command
        command = EditorCommandPayload(command="aqe:pitch-hum")
    config = AudioProcessingConfig.from_config(deps.config(editor))
    deps.run_special_audio_transform_async(
        editor,
        label=t("editor.status.pitch_hum"),
        failure_log_label="pitch hum failed",
        renderer=_pitch_hum_renderer(command, deps, config.pitch_hum_mode),
        command=command,
    )


def _pitch_hum_renderer(
    command: EditorCommandPayload | None,
    deps: Any,
    default_mode: str,
) -> Callable[..., Any]:
    mode = command.overrides.pitch_hum_mode if command is not None else None
    if (mode or default_mode) == "pitch_tier":
        return cast(Callable[..., Any], deps.render_pitch_tier_hum_audio)
    return cast(Callable[..., Any], deps.render_pitch_hum_audio)


def run_special_audio_transform_async(
    editor: Any,
    *,
    label: str,
    failure_log_label: str,
    renderer: Callable[..., Any],
    support_hint: str = "",
    failure_context_recorder: Callable[[Path, AudioProcessingConfig, Exception], None] | None = None,
    command: EditorCommandPayload | None = None,
    output_format: object = DEFAULT_OUTPUT_FORMAT,
    deps: Any,
) -> None:
    operation_id = new_operation_id("transform")
    existing = deps.sessions.get(editor)
    if existing and existing.processing:
        deps.eval_status(editor, deps.still_processing_message, kind="processing")
        return
    if existing and existing.playback_preparing:
        deps.stop_session_playback(existing)
    session, current_path = deps.current_media_path(editor)
    cancel_graph_analysis_for_processing(editor, session, deps)
    config = _special_transform_config(AudioProcessingConfig.from_config(deps.config(editor)), command)
    deps.stop_session_playback(session)
    session.post_edit_playback_generation += 1
    session.next_status_summary = command_status_summary(command or EditorCommandPayload(command=""), config)
    session.processing = True
    field_index = session.field_index if session.field_index is not None else getattr(editor, "currentField", 0)
    guard = begin_processing_guard(
        session,
        field_index=int(field_index),
        source_filename=current_path.name,
    )
    session.playback_active = False
    session.playback_paused = False
    deps.set_busy(editor, True, f"{label}...")
    deps.eval_playback_state(editor, guard.field_index, "stopped", session.cursor_ms)
    record_breadcrumb(
        "editor.special_transform.started",
        source="editor",
        operation=f"editor.{failure_log_label}",
        operation_id=operation_id,
        context={"label": label, "source_filename": current_path.name},
        flush=True,
    )

    def _run() -> None:
        run_special_transform_worker(
            editor,
            session,
            current_path,
            config,
            label,
            failure_log_label,
            renderer,
            failure_context_recorder,
            support_hint,
            output_format,
            guard,
            operation_id,
            deps,
        )

    deps.threading.Thread(target=_run, daemon=True).start()


def _special_transform_config(
    config: AudioProcessingConfig,
    command: EditorCommandPayload | None,
) -> AudioProcessingConfig:
    if command is None:
        return config
    if command.overrides.dpdfnet_attn_limit_db is not None:
        config = replace(config, dpdfnet_attn_limit_db=command.overrides.dpdfnet_attn_limit_db)
    if command.command == "aqe:pitch-hum":
        return config_with_graph_settings(config, command.graph_settings)
    return config


def replace_current_field_after_noise_removal(
    editor: Any,
    saved_name: str,
    deps: Any,
    *,
    guard: EditorProcessingGuard | None = None,
    output_path: Path | None = None,
) -> None:
    session = deps.sessions.get(editor)
    if guard is not None and not processing_guard_matches_editor(editor, session, guard, deps):
        if clear_processing_for_stale_guard(session, guard):
            deps.set_busy(editor, False)
        return
    if output_path is not None:
        saved_name = deps.write_generated_media(editor, saved_name, output_path)
    field_index = resolved_field_index(session, editor, deps)
    field_html = editor.note.fields[field_index]
    selection = select_first_sound_reference(field_html)
    if selection.selected is None:
        raise AudioProcessingError(deps.current_field_audio_missing)
    deps.dispose_editor_frontend_controls(editor)
    editor.note.fields[field_index] = replace_sound_reference(field_html, selection.selected, saved_name)
    should_redraw_graph = _replace_noise_reduction_session_state(editor, session, field_index, saved_name)
    editor.loadNote(focusTo=field_index)
    if session:
        session.pending_status = None
    sync_history_availability(editor, session, deps)
    request_history_availability_after_edit(editor, session, deps)
    deps.eval_playback_state(editor, field_index, "stopped", 0)
    if should_redraw_graph:
        deps.request_graph_redraw(editor, saved_name)
    else:
        deps.set_busy(editor, False)
    deps.request_playback_after_edit(editor, field_index)


def _replace_noise_reduction_session_state(
    editor: Any,
    session: EditorSession | None,
    field_index: int,
    saved_name: str,
) -> bool:
    if session is None:
        return False
    session.undo_history.push(session.state, session.current_filename, status_summary=session.status_summary)
    session.redo_history.clear()
    session.state = AudioEditState(source_file=saved_name)
    session.current_filename = saved_name
    session.field_index = field_index
    session.status_summary = session.next_status_summary or session.status_summary
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
        reset_session_visualized_graph(session, field_index)
    return should_redraw_graph


def record_rnnoise_failure_context(source_path: Path, config: AudioProcessingConfig, exc: Exception) -> None:
    record_latest_denoise_support_incident(
        operation="rnnoise_denoise",
        media_filename=source_path.name,
        source_path=str(source_path.resolve()),
        user_message=message_with_macos_permission_guidance(str(exc), exc),
        exception_type=type(exc).__name__,
        ffmpeg_path=config.ffmpeg_path,
    )


def record_dpdfnet_failure_context(source_path: Path, config: AudioProcessingConfig, exc: Exception) -> None:
    record_latest_denoise_support_incident(
        operation="dpdfnet_denoise",
        media_filename=source_path.name,
        source_path=str(source_path.resolve()),
        user_message=message_with_macos_permission_guidance(str(exc), exc),
        exception_type=type(exc).__name__,
        ffmpeg_path=config.ffmpeg_path,
    )


def record_spleeter_failure_context(source_path: Path, config: AudioProcessingConfig, exc: Exception) -> None:
    record_latest_spleeter_support_incident(
        operation="voice_only",
        media_filename=source_path.name,
        source_path=str(source_path.resolve()),
        user_message=message_with_macos_permission_guidance(str(exc), exc),
        exception_type=type(exc).__name__,
        ffmpeg_path=config.ffmpeg_path,
    )


def log_special_transform_failure(failure_log_label: str, message: str) -> None:
    if failure_log_label in {"rnnoise denoise failed", "dpdfnet denoise failed"}:
        incident = latest_denoise_support_incident()
        if incident:
            logger.exception("%s: %s\n%s", failure_log_label, message, format_denoise_support_log_block(incident))
            return
        logger.exception("%s: %s", failure_log_label, message)
        return
    if failure_log_label == "voice only failed":
        incident = latest_spleeter_support_incident()
        if incident:
            logger.exception("%s: %s\n%s", failure_log_label, message, format_spleeter_support_log_block(incident))
            return
        logger.exception("%s: %s", failure_log_label, message)
        return
    logger.exception("%s: %s", failure_log_label, message)
