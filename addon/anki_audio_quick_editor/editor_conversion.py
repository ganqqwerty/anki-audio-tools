"""Format conversion behavior for the editor bridge."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .audio_formats import format_label, is_same_visible_format
from .audio_state import AudioProcessingConfig
from .editor_actions import EditorCommandPayload
from .editor_session import EditorSession
from .i18n import t


def convert_async(
    editor: Any,
    command: EditorCommandPayload | None = None,
    deps: Any = None,
) -> None:
    """Start format conversion for the current media."""
    if deps is None:
        deps = command
        command = None
    existing = deps.sessions.get(editor)
    if existing and _has_blocking_work(existing):
        deps.eval_status(editor, deps.still_processing_message, kind="processing")
        return
    config = AudioProcessingConfig.from_config(deps.config(editor))
    target_format = (
        command.overrides.target_format
        if command is not None and command.overrides.target_format is not None
        else config.output_format
    )
    session, current_path = deps.current_media_path(editor)
    if is_same_visible_format(current_path.name, target_format):
        session.processing = False
        deps.set_busy(editor, False)
        deps.eval_status(
            editor,
            t("editor.status.already_target_format", {"format": format_label(target_format)}),
        )
        return

    def _renderer(
        source_path: Path,
        render_config: AudioProcessingConfig,
        *,
        output_path: Path,
        on_command: Callable[[tuple[str, ...]], None] | None = None,
    ) -> None:
        deps.render_converted_audio(
            source_path,
            render_config,
            target_format,
            output_path=output_path,
            on_command=on_command,
        )

    deps.run_special_audio_transform_async(
        editor,
        label=t("editor.status.converting", {"format": format_label(target_format)}),
        failure_log_label="convert failed",
        renderer=_renderer,
        command=command,
        output_format=target_format,
    )


def _has_blocking_work(session: EditorSession) -> bool:
    return session.processing
