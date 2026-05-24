"""Small helpers for batch operation orchestration."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from .audio_processor import (
    render_dpdfnet_audio,
    render_noise_reduced_audio,
    render_rnnoise_audio,
    render_voice_only_audio,
)
from .audio_state import AudioProcessingConfig
from .audio_types import AudioProcessingResult

if TYPE_CHECKING:
    from .batch_operations import BatchNoteResult
else:
    BatchNoteResult = Any


def render_batch_denoise(
    source_path: Path,
    config: AudioProcessingConfig,
    output_path: Path,
) -> AudioProcessingResult:
    facade = import_module(".batch_operations", package=__package__)
    renderers = {
        "standard": getattr(facade, "render_noise_reduced_audio", render_noise_reduced_audio),
        "rnnoise": getattr(facade, "render_rnnoise_audio", render_rnnoise_audio),
        "dpdfnet": getattr(facade, "render_dpdfnet_audio", render_dpdfnet_audio),
        "voice_only": getattr(facade, "render_voice_only_audio", render_voice_only_audio),
    }
    return renderers.get(config.denoise_algorithm, render_noise_reduced_audio)(
        source_path,
        config,
        output_path=output_path,
    )


def skipped_batch_note(note_id: int, message: str) -> BatchNoteResult:
    facade = import_module(".batch_operations", package=__package__)
    result_type = cast(Any, facade.BatchNoteResult)
    return cast(BatchNoteResult, result_type(note_id=note_id, status="skipped", message=message))
