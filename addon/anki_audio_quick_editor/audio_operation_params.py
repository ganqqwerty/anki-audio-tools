"""Shared import-safe parameter handling for editor and batch audio operations."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from .audio_state import AudioProcessingConfig
from .dpdfnet_settings import normalize_dpdfnet_attn_limit_db

MIN_TRIM_OVERRIDE_MS = 50
MAX_TRIM_OVERRIDE_MS = 10_000
MIN_VOLUME_STEP_DB = 0.5
MAX_VOLUME_STEP_DB = 12.0
MIN_SPEED_STEP = 0.01
MAX_SPEED_STEP = 0.25
PAUSE_AGGRESSIVENESS = frozenset({"gentle", "normal", "aggressive"})
DENOISE_ALGORITHMS = frozenset({"standard", "rnnoise", "dpdfnet", "voice_only"})


@dataclass(frozen=True)
class AudioOperationParameters:
    """Validated optional parameters shared by editor and batch operations."""

    trim_step_ms: int | None = None
    volume_step_db: float | None = None
    speed_step: float | None = None
    pause_aggressiveness: str | None = None
    denoise_algorithm: str | None = None
    dpdfnet_attn_limit_db: float | None = None


def parameters_from_raw(
    *,
    trim_step_ms: Any = None,
    volume_step_db: Any = None,
    speed_step: Any = None,
    pause_aggressiveness: Any = None,
    denoise_algorithm: Any = None,
    dpdfnet_attn_limit_db: Any = None,
) -> AudioOperationParameters:
    """Normalize raw UI values into clamped operation parameters."""
    return AudioOperationParameters(
        trim_step_ms=_clamp_trim_step_ms(_int_or_none(trim_step_ms)),
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
        denoise_algorithm=_denoise_algorithm_or_none(denoise_algorithm),
        dpdfnet_attn_limit_db=_dpdfnet_attn_limit_or_none(dpdfnet_attn_limit_db),
    )


def effective_config_for_operation(
    operation: str,
    config: AudioProcessingConfig,
    parameters: AudioOperationParameters,
) -> AudioProcessingConfig:
    """Return the render config after applying operation-local parameters."""
    if operation == "graph":
        return config
    effective = replace(
        config,
        volume_step_db=parameters.volume_step_db or config.volume_step_db,
        speed_step=parameters.speed_step or config.speed_step,
        denoise_algorithm=parameters.denoise_algorithm or config.denoise_algorithm,
        dpdfnet_attn_limit_db=(
            parameters.dpdfnet_attn_limit_db
            if parameters.dpdfnet_attn_limit_db is not None
            else config.dpdfnet_attn_limit_db
        ),
    )
    if operation == "remove_pauses":
        return config_for_pause_aggressiveness(
            effective,
            parameters.pause_aggressiveness or config.pause_aggressiveness,
        )
    return effective


def config_for_pause_aggressiveness(
    config: AudioProcessingConfig,
    aggressiveness: str,
) -> AudioProcessingConfig:
    """Return pause detection thresholds for one supported aggressiveness level."""
    if aggressiveness == "gentle":
        return replace(
            config,
            internal_pause_silence_threshold_db=-42,
            internal_pause_threshold_ms=450,
            internal_pause_target_gap_ms=180,
            pause_aggressiveness=aggressiveness,
        )
    if aggressiveness == "aggressive":
        return replace(
            config,
            internal_pause_silence_threshold_db=-50,
            internal_pause_threshold_ms=180,
            internal_pause_target_gap_ms=60,
            pause_aggressiveness=aggressiveness,
        )
    return replace(config, pause_aggressiveness="normal")


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


def _clamp_trim_step_ms(value: int | None) -> int | None:
    if value is None:
        return None
    return max(MIN_TRIM_OVERRIDE_MS, min(MAX_TRIM_OVERRIDE_MS, value))


def _clamp_float(value: float | None, minimum: float, maximum: float) -> float | None:
    if value is None:
        return None
    return max(minimum, min(maximum, value))


def _pause_aggressiveness_or_none(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    return value if value in PAUSE_AGGRESSIVENESS else None


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
