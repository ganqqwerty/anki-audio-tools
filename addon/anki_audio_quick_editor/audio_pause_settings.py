"""Pause detection preset and parameter helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

PAUSE_AGGRESSIVENESS = frozenset({"gentle", "normal", "aggressive"})
PAUSE_DETECTION_ALGORITHMS = frozenset({"silencedetect", "silero_vad"})

MIN_SILENCEDETECT_THRESHOLD_DB = -100.0
MAX_SILENCEDETECT_THRESHOLD_DB = 0.0
MIN_SILERO_THRESHOLD = 0.0
MAX_SILERO_THRESHOLD = 1.0
MIN_PAUSE_SECONDS = 0.01
MAX_PAUSE_SECONDS = 10.0


@dataclass(frozen=True)
class PauseDetectionPreset:
    """Algorithm-specific pause detection parameters."""

    threshold: float
    min_silence_seconds: float
    min_speech_seconds: float
    preprocess_denoise: bool


SILENCEDETECT_PRESETS: dict[str, PauseDetectionPreset] = {
    "gentle": PauseDetectionPreset(-42.0, 0.45, 0.12, True),
    "normal": PauseDetectionPreset(-45.0, 0.30, 0.10, True),
    "aggressive": PauseDetectionPreset(-52.0, 0.14, 0.04, True),
}

SILERO_VAD_PRESETS: dict[str, PauseDetectionPreset] = {
    "gentle": PauseDetectionPreset(0.55, 0.70, 0.12, False),
    "normal": PauseDetectionPreset(0.50, 0.45, 0.10, False),
    "aggressive": PauseDetectionPreset(0.85, 0.15, 0.04, False),
}


def pause_detection_algorithm_or_default(value: Any) -> str:
    """Return a supported pause detector name."""
    return value if isinstance(value, str) and value in PAUSE_DETECTION_ALGORITHMS else "silencedetect"


def pause_aggressiveness_or_default(value: Any) -> str:
    """Return a supported pause preset name."""
    return value if isinstance(value, str) and value in PAUSE_AGGRESSIVENESS else "normal"


def preset_for_pause_detection(algorithm: Any, aggressiveness: Any) -> PauseDetectionPreset:
    """Return the preset for a detector/aggressiveness pair."""
    detector = pause_detection_algorithm_or_default(algorithm)
    preset = pause_aggressiveness_or_default(aggressiveness)
    if detector == "silero_vad":
        return SILERO_VAD_PRESETS[preset]
    return SILENCEDETECT_PRESETS[preset]


def clamp_pause_threshold(algorithm: Any, value: Any, default: float) -> float:
    """Clamp a pause detector threshold in the detector's native unit."""
    parsed = _float_or_default(value, default)
    if pause_detection_algorithm_or_default(algorithm) == "silero_vad":
        return _clamp_float(parsed, MIN_SILERO_THRESHOLD, MAX_SILERO_THRESHOLD)
    return _clamp_float(parsed, MIN_SILENCEDETECT_THRESHOLD_DB, MAX_SILENCEDETECT_THRESHOLD_DB)


def clamp_pause_seconds(value: Any, default: float) -> float:
    """Clamp a pause detector duration parameter."""
    return round(_clamp_float(_float_or_default(value, default), MIN_PAUSE_SECONDS, MAX_PAUSE_SECONDS), 3)


def bool_or_default(value: Any, default: bool) -> bool:
    """Return a bool config value, preserving explicit false."""
    return value if isinstance(value, bool) else default


def active_pause_detection_params(config: Any) -> dict[str, float | bool]:
    """Return active pause detector params from an AudioProcessingConfig-like object."""
    if getattr(config, "pause_detection_algorithm", None) == "silero_vad":
        return {
            "threshold": config.pause_silero_threshold,
            "min_silence_seconds": config.pause_silero_min_silence_seconds,
            "min_speech_seconds": config.pause_silero_min_speech_seconds,
            "preprocess_denoise": config.pause_silero_preprocess_denoise,
        }
    return {
        "threshold": config.pause_silencedetect_threshold_db,
        "min_silence_seconds": config.pause_silencedetect_min_silence_seconds,
        "min_speech_seconds": config.pause_silencedetect_min_speech_seconds,
        "preprocess_denoise": config.pause_silencedetect_preprocess_denoise,
    }


def pause_preprocess_denoise_enabled(config: Any) -> bool:
    """Return whether active pause detection should denoise before analysis."""
    if getattr(config, "pause_detection_algorithm", None) == "silero_vad":
        return bool(config.pause_silero_preprocess_denoise)
    return bool(config.pause_silencedetect_preprocess_denoise)


def seconds_to_pause_ms(seconds: float) -> int:
    """Return a positive millisecond duration for pause detector commands."""
    return max(1, round(float(seconds) * 1000))


def _float_or_default(value: Any, default: float) -> float:
    if isinstance(value, bool):
        return default
    if isinstance(value, int | float):
        return float(value)
    return default


def _clamp_float(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
