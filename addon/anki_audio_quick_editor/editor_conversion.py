"""Format conversion behavior for the editor bridge."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, cast

from .audio_formats import format_label, is_same_visible_format
from .audio_state import AudioProcessingConfig
from .editor_actions import EditorCommandPayload
from .editor_session import EditorSession
from .i18n import t

if TYPE_CHECKING:
    from .editor_deps_protocols import ProcessingDeps

logger = logging.getLogger(__name__)


def convert_async(
    editor: Any,
    command: EditorCommandPayload | None = None,
    deps: ProcessingDeps | None = None,
) -> None:
    """Start format conversion for the current media."""
    if deps is None:
        deps = cast("ProcessingDeps", command)
        command = EditorCommandPayload(command="aqe:convert")
    existing = deps.sessions.get(editor)
    if existing and _has_blocking_work(existing):
        deps.eval_status(editor, deps.still_processing_message, kind="processing")
        return
    if command is not None and command.source_filename is not None:
        if not _source_bound_command_is_current(editor, command, deps):
            deps.set_busy(editor, False)
            deps.eval_status(editor, t("editor.status.playback_recovery_stale"), kind="warning")
            return
    config = AudioProcessingConfig.from_config(deps.config(editor))
    target_format = (
        command.overrides.target_format
        if command is not None and command.overrides.target_format is not None
        else config.output_format
    )
    session, current_path = deps.current_media_path(editor)
    if is_same_visible_format(current_path.name, target_format):
        session.finish_processing_without_edit(stop_playback=False)
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
    return session.processing.active


def _source_bound_command_is_current(
    editor: Any,
    command: EditorCommandPayload,
    deps: ProcessingDeps,
) -> bool:
    current_field_ord = deps.current_field_index(editor)
    if command.field_ord is None or current_field_ord != command.field_ord:
        logger.info(
            "playback recovery conversion rejected: requested_field=%s current_field=%s requested_source=%r",
            command.field_ord,
            current_field_ord,
            command.source_filename,
        )
        return False
    source_matches = deps.resolve_requested_field_media(
        editor,
        command.field_ord,
        command.source_filename,
    ) is not None
    if not source_matches:
        logger.info(
            "playback recovery conversion rejected: requested_field=%s current_field=%s requested_source=%r source_match=false",
            command.field_ord,
            current_field_ord,
            command.source_filename,
        )
    return source_matches
