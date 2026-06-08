"""Raw-value normalization for shared audio operation parameters."""

from __future__ import annotations

from typing import Any

from .audio_formats import validate_target_format
from .audio_operation_params_types import (
    DENOISE_ALGORITHMS,
    MAX_SPEED_STEP,
    MAX_VOLUME_STEP_DB,
    MIN_SPEED_STEP,
    MIN_VOLUME_STEP_DB,
    AudioOperationParameters,
)
from .audio_pause_settings import (
    MIN_PAUSE_SECONDS,
    PAUSE_AGGRESSIVENESS,
    PAUSE_DETECTION_ALGORITHMS,
    clamp_pause_seconds,
    clamp_pause_threshold,
)
from .audio_size_reduction import (
    normalize_size_reduction_bitrate_kbps,
    normalize_size_reduction_channels,
    normalize_size_reduction_mode,
    normalize_size_reduction_sample_rate_hz,
)
from .dpdfnet_settings import normalize_dpdfnet_attn_limit_db


def parameters_from_raw(
    *,
    volume_step_db: Any = None,
    speed_step: Any = None,
    pause_aggressiveness: Any = None,
    pause_detection_algorithm: Any = None,
    pause_threshold: Any = None,
    pause_min_silence_seconds: Any = None,
    pause_min_speech_seconds: Any = None,
    pause_preprocess_denoise: Any = None,
    denoise_algorithm: Any = None,
    dpdfnet_attn_limit_db: Any = None,
    target_format: Any = None,
    size_reduction_mode: Any = None,
    size_reduction_bitrate_kbps: Any = None,
    size_reduction_sample_rate_hz: Any = None,
    size_reduction_channels: Any = None,
) -> AudioOperationParameters:
    """Normalize raw UI values into clamped operation parameters."""
    return AudioOperationParameters(
        volume_step_db=_clamp_float(
            _float_or_none(volume_step_db),
            MIN_VOLUME_STEP_DB,
            MAX_VOLUME_STEP_DB,
        ),
        speed_step=_clamp_float(
            _float_or_none(speed_step),
            MIN_SPEED_STEP,
            MAX_SPEED_STEP,
        ),
        pause_aggressiveness=_pause_aggressiveness_or_none(pause_aggressiveness),
        pause_detection_algorithm=_pause_detection_algorithm_or_none(pause_detection_algorithm),
        pause_threshold=_pause_threshold_or_none(pause_detection_algorithm, pause_threshold),
        pause_min_silence_seconds=_pause_seconds_or_none(pause_min_silence_seconds),
        pause_min_speech_seconds=_pause_seconds_or_none(pause_min_speech_seconds),
        pause_preprocess_denoise=_bool_or_none(pause_preprocess_denoise),
        denoise_algorithm=_denoise_algorithm_or_none(denoise_algorithm),
        dpdfnet_attn_limit_db=_dpdfnet_attn_limit_or_none(dpdfnet_attn_limit_db),
        target_format=_target_format_or_none(target_format),
        size_reduction_mode=_size_reduction_mode_or_none(size_reduction_mode),
        size_reduction_bitrate_kbps=_size_reduction_bitrate_or_none(
            size_reduction_bitrate_kbps
        ),
        size_reduction_sample_rate_hz=_size_reduction_sample_rate_or_none(
            size_reduction_sample_rate_hz
        ),
        size_reduction_channels=_size_reduction_channels_or_none(size_reduction_channels),
    )


def _float_or_none(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _clamp_float(value: float | None, minimum: float, maximum: float) -> float | None:
    if value is None:
        return None
    return max(minimum, min(maximum, value))


def _pause_aggressiveness_or_none(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    return value if value in PAUSE_AGGRESSIVENESS else None


def _pause_detection_algorithm_or_none(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    return value if value in PAUSE_DETECTION_ALGORITHMS else None


def _pause_threshold_or_none(algorithm: Any, value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    parsed = _float_or_none(value)
    if parsed is None:
        return None
    if isinstance(algorithm, str) and algorithm in PAUSE_DETECTION_ALGORITHMS:
        return clamp_pause_threshold(algorithm, parsed, parsed)
    return parsed


def _pause_seconds_or_none(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    return clamp_pause_seconds(value, MIN_PAUSE_SECONDS)


def _bool_or_none(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def _denoise_algorithm_or_none(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    return value if value in DENOISE_ALGORITHMS else None


def _dpdfnet_attn_limit_or_none(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return normalize_dpdfnet_attn_limit_db(value)
    except (TypeError, ValueError):
        return None


def _target_format_or_none(value: Any) -> str | None:
    try:
        return validate_target_format(value)
    except ValueError:
        return None


def _size_reduction_mode_or_none(value: Any) -> str | None:
    normalized = normalize_size_reduction_mode(value)
    return normalized if str(value).strip().lower() == normalized else None


def _size_reduction_bitrate_or_none(value: Any) -> int | None:
    parsed = _int_or_none(value)
    if parsed is None:
        return None
    return normalize_size_reduction_bitrate_kbps(parsed)


def _size_reduction_sample_rate_or_none(value: Any) -> int | None:
    parsed = _int_or_none(value)
    if parsed is None:
        return None
    return normalize_size_reduction_sample_rate_hz(parsed)


def _size_reduction_channels_or_none(value: Any) -> int | None:
    parsed = _int_or_none(value)
    if parsed is None:
        return None
    return normalize_size_reduction_channels(parsed)
