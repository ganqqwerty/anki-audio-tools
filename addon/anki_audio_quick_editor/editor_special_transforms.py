"""Editor-side special transform orchestration."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, cast

from .audio_state import AudioProcessingConfig
from .editor_actions import EditorCommandPayload
from .i18n import t

if TYPE_CHECKING:
    from .editor_deps_protocols import ProcessingDeps

logger = logging.getLogger(__name__)


def denoise_standard_async(editor: Any, deps: ProcessingDeps) -> None:
    deps.run_special_audio_transform_async(
        editor,
        label=t("editor.status.denoising_standard"),
        failure_log_label="standard denoise failed",
        renderer=deps.render_noise_reduced_audio,
        command=EditorCommandPayload(command="aqe:denoise-standard"),
    )


def reduce_size_async(
    editor: Any,
    command: EditorCommandPayload | None = None,
    deps: ProcessingDeps | None = None,
) -> None:
    if deps is None:
        deps = cast("ProcessingDeps", command)
        command = EditorCommandPayload(command="aqe:reduce-size")
    mode = command.overrides.size_reduction_mode if command is not None else None

    def _renderer(
        source_path: Path,
        render_config: AudioProcessingConfig,
        *,
        output_path: Path,
        on_command: Callable[[tuple[str, ...]], None] | None = None,
    ) -> Any:
        return deps.render_size_reduced_audio(
            source_path,
            render_config,
            output_path=output_path,
            on_command=on_command,
            mode=mode,
        )

    deps.run_special_audio_transform_async(
        editor,
        label=t("editor.status.reducing_size"),
        failure_log_label="size reduction failed",
        renderer=_renderer,
        command=command,
        output_format="mp3",
    )


def rnnoise_async(editor: Any, deps: ProcessingDeps) -> None:
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
    deps: ProcessingDeps | None = None,
) -> None:
    if deps is None:
        deps = cast("ProcessingDeps", command)
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


def voice_only_async(editor: Any, deps: ProcessingDeps) -> None:
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
    deps: ProcessingDeps | None = None,
) -> None:
    if deps is None:
        deps = cast("ProcessingDeps", command)
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
    deps: ProcessingDeps,
    default_mode: str,
) -> Callable[..., Any]:
    mode = command.overrides.pitch_hum_mode if command is not None else None
    if (mode or default_mode) == "pitch_tier":
        return deps.render_pitch_tier_hum_audio
    return deps.render_pitch_hum_audio
