"""Shared types and constants for audio operation parameter handling."""

from __future__ import annotations

from dataclasses import dataclass

MIN_VOLUME_STEP_DB = 1.0
MAX_VOLUME_STEP_DB = 40.0
MIN_SPEED_STEP = 1.01
MAX_SPEED_STEP = 5.0
DENOISE_ALGORITHMS = frozenset({"standard", "rnnoise", "dpdfnet", "voice_only"})


@dataclass(frozen=True)
class AudioOperationParameters:
    """Validated optional parameters shared by editor and batch operations."""

    volume_step_db: float | None = None
    speed_step: float | None = None
    pause_aggressiveness: str | None = None
    pause_detection_algorithm: str | None = None
    pause_threshold: float | None = None
    pause_min_silence_seconds: float | None = None
    pause_min_speech_seconds: float | None = None
    pause_preprocess_denoise: bool | None = None
    denoise_algorithm: str | None = None
    dpdfnet_attn_limit_db: float | None = None
    target_format: str | None = None
    size_reduction_mode: str | None = None
    size_reduction_bitrate_kbps: int | None = None
    size_reduction_sample_rate_hz: int | None = None
    size_reduction_channels: int | None = None
