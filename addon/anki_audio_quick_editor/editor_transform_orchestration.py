"""Core orchestration for special audio transforms."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from .audio_formats import DEFAULT_OUTPUT_FORMAT
from .audio_state import AudioProcessingConfig
from .diagnostics_runtime import new_operation_id, record_breadcrumb
from .editor_actions import EditorCommandPayload, processing_config_for_command
from .editor_processing_shared import cancel_graph_analysis_for_processing
from .editor_session import begin_processing_guard
from .editor_special_transform_worker import run_special_transform_worker
from .editor_status import command_status_summary
from .prosody_settings import config_with_graph_settings

if TYPE_CHECKING:
    from .editor_deps_protocols import ProcessingDeps


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
    deps: ProcessingDeps,
) -> None:
    operation_id = new_operation_id("transform")
    existing = deps.sessions.get(editor)
    if existing and existing.processing.active:
        deps.eval_status(editor, deps.still_processing_message, kind="processing")
        return
    if existing and existing.playback.preparing:
        deps.stop_session_playback(existing)
    session, current_path = deps.current_media_path(editor)
    cancel_graph_analysis_for_processing(editor, session, deps)
    config = _special_transform_config(AudioProcessingConfig.from_config(deps.config(editor)), command)
    deps.stop_session_playback(session)
    session.processing.next_status_summary = command_status_summary(command or EditorCommandPayload(command=""), config)
    session.processing.active = True
    field_index = session.field_index if session.field_index is not None else getattr(editor, "currentField", 0)
    guard = begin_processing_guard(
        session,
        field_index=int(field_index),
        source_filename=current_path.name,
    )
    session.playback.active = False
    session.playback.paused = False
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
    if command.command == "aqe:reduce-size":
        return processing_config_for_command(command, config)
    if command.overrides.dpdfnet_attn_limit_db is not None:
        config = replace(config, dpdfnet_attn_limit_db=command.overrides.dpdfnet_attn_limit_db)
    if command.command == "aqe:pitch-hum":
        return config_with_graph_settings(config, command.graph_settings)
    return config
