"""Render and transform wrappers for the audio processor facade."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from importlib import import_module
from pathlib import Path
from typing import Any, cast

from .audio_state import AudioEditState, AudioProcessingConfig
from .audio_types import AudioProcessingResult


def _facade() -> Any:
    return import_module(".audio_processor", package=__package__)


def _sync(facade: Any, name: str) -> None:
    cast(Callable[[], None], getattr(facade, name))()


def _member(facade: Any, name: str) -> Any:
    return getattr(facade, name)


def _rendering(facade: Any) -> Any:
    return _member(facade, "_audio_rendering")


def _noise(facade: Any) -> Any:
    return _member(facade, "_audio_noise_reduction")


def _pitch(facade: Any) -> Any:
    return _member(facade, "_audio_pitch_hum")


def render_audio(
    source_path: Path,
    state: AudioEditState,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
    artifact_root: Path | None = None,
) -> AudioProcessingResult:
    facade = _facade()
    _sync(facade, "_sync_rendering_dependencies")
    return cast(AudioProcessingResult, _rendering(facade).render_audio(source_path, state, config, output_path, on_command, artifact_root))


def render_converted_audio(
    source_path: Path,
    config: AudioProcessingConfig,
    target_format: object,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    facade = _facade()
    _sync(facade, "_sync_rendering_dependencies")
    return cast(AudioProcessingResult, _rendering(facade).render_converted_audio(source_path, config, target_format, output_path, on_command))


def render_audio_region_deleted(
    source_path: Path,
    selection_start_ms: int,
    selection_end_ms: int,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    facade = _facade()
    _sync(facade, "_sync_rendering_dependencies")
    return cast(AudioProcessingResult, _rendering(facade).render_audio_region_deleted(
        source_path,
        selection_start_ms,
        selection_end_ms,
        config,
        output_path,
        on_command,
    ))


def render_audio_region_kept(
    source_path: Path,
    selection_start_ms: int,
    selection_end_ms: int,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    facade = _facade()
    _sync(facade, "_sync_rendering_dependencies")
    return cast(AudioProcessingResult, _rendering(facade).render_audio_region_kept(
        source_path,
        selection_start_ms,
        selection_end_ms,
        config,
        output_path,
        on_command,
    ))


def render_playback_segment(
    source_path: Path,
    start_ms: int,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
    end_ms: int | None = None,
) -> AudioProcessingResult:
    facade = _facade()
    _sync(facade, "_sync_rendering_dependencies")
    return cast(AudioProcessingResult, _rendering(facade).render_playback_segment(
        source_path,
        start_ms,
        config,
        output_path,
        on_command,
        end_ms,
    ))


def make_output_filename(
    source_filename: str,
    now: datetime | None = None,
    token: str | None = None,
    *,
    output_format: object = "source",
) -> str:
    facade = _facade()
    _sync(facade, "_sync_rendering_dependencies")
    return cast(str, _rendering(facade).make_output_filename(source_filename, now, token, output_format=output_format))


def temp_final_path(filename: str) -> Path:
    facade = _facade()
    _sync(facade, "_sync_rendering_dependencies")
    return cast(Path, _rendering(facade).temp_final_path(filename))


def make_playback_segment_filename(source_filename: str, start_ms: int, token: str | None = None) -> str:
    facade = _facade()
    _rendering(facade).uuid = facade.uuid
    original = cast(
        Callable[[str, int, str | None], str],
        _member(facade, "_ORIGINAL_MAKE_PLAYBACK_SEGMENT_FILENAME"),
    )
    return original(source_filename, start_ms, token)


def temp_playback_path(source_filename: str, start_ms: int) -> Path:
    facade = _facade()
    _sync(facade, "_sync_rendering_dependencies")
    return cast(Path, _rendering(facade).temp_playback_path(source_filename, start_ms))


def render_noise_reduced_audio(
    source_path: Path,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    facade = _facade()
    _sync(facade, "_sync_noise_dependencies")
    return cast(AudioProcessingResult, _noise(facade).render_noise_reduced_audio(source_path, config, output_path, on_command))


def render_pitch_hum_audio(
    source_path: Path,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    facade = _facade()
    _sync(facade, "_sync_pitch_hum_dependencies")
    return cast(AudioProcessingResult, _pitch(facade).render_pitch_hum_audio(source_path, config, output_path, on_command))


def render_pitch_tier_hum_audio(
    source_path: Path,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    facade = _facade()
    _sync(facade, "_sync_pitch_hum_dependencies")
    return cast(AudioProcessingResult, _pitch(facade).render_pitch_tier_hum_audio(source_path, config, output_path, on_command))


def render_rnnoise_audio(
    source_path: Path,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    facade = _facade()
    _sync(facade, "_sync_noise_dependencies")
    return cast(AudioProcessingResult, _noise(facade).render_rnnoise_audio(source_path, config, output_path, on_command))


def render_dpdfnet_audio(
    source_path: Path,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    facade = _facade()
    _sync(facade, "_sync_noise_dependencies")
    return cast(AudioProcessingResult, _noise(facade).render_dpdfnet_audio(source_path, config, output_path, on_command))


def render_voice_only_audio(
    source_path: Path,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    facade = _facade()
    _sync(facade, "_sync_noise_dependencies")
    return cast(AudioProcessingResult, _noise(facade).render_voice_only_audio(source_path, config, output_path, on_command))
