"""Shared import-safe parameter handling for editor and batch audio operations."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from .audio_formats import validate_target_format
from .audio_state import AudioProcessingConfig
from .dpdfnet_settings import normalize_dpdfnet_attn_limit_db

MIN_VOLUME_STEP_DB = 1.0
MAX_VOLUME_STEP_DB = 40.0
MIN_SPEED_STEP = 1.01
MAX_SPEED_STEP = 5.0
PAUSE_AGGRESSIVENESS = frozenset({"gentle", "normal", "aggressive"})
PAUSE_DETECTION_ALGORITHMS = frozenset({"deep_filter", "silero_vad"})
DENOISE_ALGORITHMS = frozenset({"standard", "rnnoise", "dpdfnet", "voice_only"})


@dataclass(frozen=True)
class AudioOperationParameters:
    """Validated optional parameters shared by editor and batch operations."""

    volume_step_db: float | None = None
    speed_step: float | None = None
    pause_aggressiveness: str | None = None
    pause_detection_algorithm: str | None = None
    denoise_algorithm: str | None = None
    dpdfnet_attn_limit_db: float | None = None
    target_format: str | None = None


def parameters_from_raw(
    *,
    volume_step_db: Any = None,
    speed_step: Any = None,
    pause_aggressiveness: Any = None,
    pause_detection_algorithm: Any = None,
    denoise_algorithm: Any = None,
    dpdfnet_attn_limit_db: Any = None,
    target_format: Any = None,
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
        denoise_algorithm=_denoise_algorithm_or_none(denoise_algorithm),
        dpdfnet_attn_limit_db=_dpdfnet_attn_limit_or_none(dpdfnet_attn_limit_db),
        target_format=_target_format_or_none(target_format),
    )


def effective_config_for_operation(
    operation: str,
    config: AudioProcessingConfig,
    parameters: AudioOperationParameters,
) -> AudioProcessingConfig:
    """Return the render config after applying operation-local parameters."""
    if operation == "graph":
        return config
    if operation == "convert":
        return _config_for_convert_operation(config, parameters)
    effective = _config_with_shared_operation_parameters(config, parameters)
    if operation != "remove_pauses":
        return effective
    return config_for_pause_aggressiveness(
        effective,
        parameters.pause_aggressiveness or config.pause_aggressiveness,
        parameters.pause_detection_algorithm or config.pause_detection_algorithm,
    )


def _config_for_convert_operation(
    config: AudioProcessingConfig,
    parameters: AudioOperationParameters,
) -> AudioProcessingConfig:
    return replace(config, output_format=parameters.target_format or config.output_format)


def _config_with_shared_operation_parameters(
    config: AudioProcessingConfig,
    parameters: AudioOperationParameters,
) -> AudioProcessingConfig:
    return replace(
        config,
        volume_step_db=parameters.volume_step_db or config.volume_step_db,
        speed_step=parameters.speed_step or config.speed_step,
        denoise_algorithm=parameters.denoise_algorithm or config.denoise_algorithm,
        dpdfnet_attn_limit_db=_operation_dpdfnet_attn_limit_db(config, parameters),
    )


def _operation_dpdfnet_attn_limit_db(
    config: AudioProcessingConfig,
    parameters: AudioOperationParameters,
) -> float:
    if parameters.dpdfnet_attn_limit_db is None:
        return config.dpdfnet_attn_limit_db
    return parameters.dpdfnet_attn_limit_db


def config_for_pause_aggressiveness(
    config: AudioProcessingConfig,
    aggressiveness: str,
    pause_detection_algorithm: str | None = None,
) -> AudioProcessingConfig:
    """Return pause detection thresholds for one supported aggressiveness level."""
    if aggressiveness == "gentle":
        return replace(
            config,
            internal_pause_silence_threshold_db=-42,
            internal_pause_threshold_ms=450,
            internal_pause_target_gap_ms=180,
            pause_aggressiveness=aggressiveness,
            pause_detection_algorithm=pause_detection_algorithm or config.pause_detection_algorithm,
        )
    if aggressiveness == "aggressive":
        return replace(
            config,
            internal_pause_silence_threshold_db=-52,
            internal_pause_threshold_ms=140,
            internal_pause_target_gap_ms=45,
            pause_aggressiveness=aggressiveness,
            pause_detection_algorithm=pause_detection_algorithm or config.pause_detection_algorithm,
        )
    return replace(
        config,
        pause_aggressiveness="normal",
        pause_detection_algorithm=pause_detection_algorithm or config.pause_detection_algorithm,
    )


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _float_or_none(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
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
