"""Small helpers for batch operation orchestration."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path

from .audio_processor import (
    render_dpdfnet_audio,
    render_noise_reduced_audio,
    render_rnnoise_audio,
    render_voice_only_audio,
)
from .audio_state import AudioProcessingConfig
from .audio_types import AudioProcessingResult
from .batch_operation_types import BatchNoteResult

BatchDenoiseRenderers = Mapping[str, Callable[..., AudioProcessingResult]]


def render_batch_denoise(
    source_path: Path,
    config: AudioProcessingConfig,
    output_path: Path,
    renderers: BatchDenoiseRenderers | None = None,
) -> AudioProcessingResult:
    resolved_renderers = renderers or {
        "standard": render_noise_reduced_audio,
        "rnnoise": render_rnnoise_audio,
        "dpdfnet": render_dpdfnet_audio,
        "voice_only": render_voice_only_audio,
    }
    return resolved_renderers.get(config.denoise_algorithm, render_noise_reduced_audio)(
        source_path,
        config,
        output_path=output_path,
    )


def skipped_batch_note(note_id: int, message: str) -> BatchNoteResult:
    return BatchNoteResult(note_id=note_id, status="skipped", message=message)
