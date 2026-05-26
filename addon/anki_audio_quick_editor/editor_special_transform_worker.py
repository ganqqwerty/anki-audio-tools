"""Background worker helpers for editor special transforms."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any, Callable

from .audio_state import AudioProcessingConfig
from .diagnostics_runtime import capture_exception
from .editor_session import (
    EditorProcessingGuard,
    EditorSession,
    clear_processing_for_stale_guard,
    is_current_processing_guard,
)
from .permission_guidance import message_with_macos_permission_guidance

logger = logging.getLogger(__name__)


def run_special_transform_worker(
    editor: Any,
    session: EditorSession,
    current_path: Path,
    config: AudioProcessingConfig,
    label: str,
    failure_log_label: str,
    renderer: Callable[..., Any],
    failure_context_recorder: Callable[[Path, AudioProcessingConfig, Exception], None] | None,
    support_hint: str,
    output_format: object,
    guard: EditorProcessingGuard,
    operation_id: str,
    deps: Any,
) -> None:
    """Render a special transform and schedule a guarded main-thread completion."""
    output_path: Path | None = None
    try:
        desired_name = deps.make_output_filename(current_path.name, output_format=output_format)
        output_path = deps.temp_final_path(desired_name)

        def _show_command(process_command: tuple[str, ...]) -> None:
            rendered = deps.format_ffmpeg_command(process_command)
            status_message = label
            command_text = ""
            if config.show_ffmpeg_commands:
                status_message = f"{status_message}: {rendered}"
                command_text = rendered
            deps.main(editor, lambda: deps.set_busy(editor, True, status_message, command_text))

        renderer(current_path, config, output_path=output_path, on_command=_show_command)
        _schedule_special_transform_finish(editor, session, desired_name, output_path, guard, deps)
    except Exception as exc:
        _handle_special_transform_worker_failure(
            editor,
            session,
            current_path,
            config,
            label,
            failure_log_label,
            failure_context_recorder,
            support_hint,
            output_path,
            guard,
            operation_id,
            exc,
            deps,
        )


def _schedule_special_transform_finish(
    editor: Any,
    session: EditorSession,
    desired_name: str,
    output_path: Path,
    guard: EditorProcessingGuard,
    deps: Any,
) -> None:
    if not is_current_processing_guard(session, guard):
        shutil.rmtree(output_path.parent, ignore_errors=True)
        deps.main(editor, lambda: _discard_stale_special_transform(editor, guard, deps))
        return

    def _finish() -> None:
        try:
            deps.replace_current_field_after_noise_removal(
                editor,
                desired_name,
                guard=guard,
                output_path=output_path,
            )
        finally:
            shutil.rmtree(output_path.parent, ignore_errors=True)

    deps.main(editor, _finish)


def _handle_special_transform_worker_failure(
    editor: Any,
    session: EditorSession,
    current_path: Path,
    config: AudioProcessingConfig,
    label: str,
    failure_log_label: str,
    failure_context_recorder: Callable[[Path, AudioProcessingConfig, Exception], None] | None,
    support_hint: str,
    output_path: Path | None,
    guard: EditorProcessingGuard,
    operation_id: str,
    exc: Exception,
    deps: Any,
) -> None:
    if output_path is not None:
        shutil.rmtree(output_path.parent, ignore_errors=True)
    message = message_with_macos_permission_guidance(str(exc), exc)
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
    rendered_message = f"{message} {support_hint}" if support_hint else message
    if not is_current_processing_guard(session, guard):
        deps.main(editor, lambda: _discard_stale_special_transform(editor, guard, deps))
        return
    deps.main(editor, lambda: deps.render_failed(editor, rendered_message, guard=guard))


def _discard_stale_special_transform(editor: Any, guard: EditorProcessingGuard, deps: Any) -> None:
    if clear_processing_for_stale_guard(deps.sessions.get(editor), guard):
        deps.set_busy(editor, False)
