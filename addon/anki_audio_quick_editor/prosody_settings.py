"""Graph analysis settings and post-processing helpers."""

from __future__ import annotations

from collections.abc import Container
from dataclasses import dataclass, replace
from typing import Any

from .audio_state import AudioProcessingConfig
from .prosody_types import ProsodyPoint

VOICE_RANGES: dict[str, tuple[float, float]] = {
    "bass": (50.0, 300.0),
    "low": (60.0, 400.0),
    "general": (75.0, 500.0),
    "high": (100.0, 700.0),
    "child": (150.0, 1000.0),
}

RECORDING_CONDITIONS = frozenset({"auto", "very_noisy", "noisy", "normal", "clean", "studio"})
SMOOTHNESSES = frozenset({"raw", "balanced", "smooth", "very_smooth"})
VOICE_LOCKS = frozenset({"loose", "balanced", "stable"})


@dataclass(frozen=True)
class ProsodyAnalysisOptions:
    """Resolved low-level analysis options derived from user-facing graph settings."""

    frame_ms: int
    max_number_of_candidates: int
    min_correlation: float
    min_rms: float
    octave_cost: float
    octave_jump_cost: float
    pitch_ceiling_hz: float
    pitch_floor_hz: float
    silence_threshold: float
    smooth_window: int
    time_step_s: float
    voiced_unvoiced_cost: float
    voicing_threshold: float


def sanitize_graph_settings(raw: Any) -> dict[str, object]:
    """Return graph settings containing only known values and bounded numbers."""
    if not isinstance(raw, dict):
        return {}
    settings: dict[str, object] = {}
    voice_range = _enum_or_none(raw.get("voiceRange"), VOICE_RANGES)
    if voice_range is not None:
        settings["graph_voice_range"] = voice_range
    recording_condition = _enum_or_none(raw.get("recordingCondition"), RECORDING_CONDITIONS)
    if recording_condition is not None:
        settings["graph_recording_condition"] = recording_condition
    smoothness = _enum_or_none(raw.get("smoothness"), SMOOTHNESSES)
    if smoothness is not None:
        settings["graph_smoothness"] = smoothness
    voice_lock = _enum_or_none(raw.get("voiceLock"), VOICE_LOCKS)
    if voice_lock is not None:
        settings["graph_voice_lock"] = voice_lock
    dropout_ms = _int_or_none(raw.get("connectShortDropoutsMs"))
    if dropout_ms is not None:
        settings["graph_connect_short_dropouts_ms"] = min(150, max(0, dropout_ms))
    return settings


def config_with_graph_settings(
    config: AudioProcessingConfig,
    settings: dict[str, object] | None,
) -> AudioProcessingConfig:
    """Return ``config`` with sanitized graph analysis overrides applied."""
    if not settings:
        return config
    overrides = _config_key_settings(settings) or sanitize_graph_settings(settings)
    if not overrides:
        return config
    dropout_ms = _int_or_none(overrides.get("graph_connect_short_dropouts_ms"))
    return replace(
        config,
        graph_voice_range=str(overrides.get("graph_voice_range", config.graph_voice_range)),
        graph_recording_condition=str(
            overrides.get("graph_recording_condition", config.graph_recording_condition)
        ),
        graph_smoothness=str(overrides.get("graph_smoothness", config.graph_smoothness)),
        graph_connect_short_dropouts_ms=(
            config.graph_connect_short_dropouts_ms if dropout_ms is None else dropout_ms
        ),
        graph_voice_lock=str(overrides.get("graph_voice_lock", config.graph_voice_lock)),
    )


def prosody_cache_fingerprint(config: AudioProcessingConfig) -> tuple[object, ...]:
    """Return the config parts that materially affect graph analysis output."""
    return (
        graph_voice_range(config),
        graph_recording_condition(config),
        graph_smoothness(config),
        graph_connect_short_dropouts_ms(config),
        graph_voice_lock(config),
    )


def resolve_analysis_options(config: AudioProcessingConfig) -> ProsodyAnalysisOptions:
    """Resolve user-facing graph settings into low-level analysis options."""
    floor, ceiling = VOICE_RANGES[graph_voice_range(config)]
    condition = graph_recording_condition(config)
    smoothness = graph_smoothness(config)
    voice_lock = graph_voice_lock(config)
    silence_threshold, voicing_threshold, min_rms, min_correlation = _condition_profile(condition)
    octave_cost, octave_jump_cost, voiced_unvoiced_cost = _voice_lock_profile(voice_lock)
    time_step_s, smooth_window = _smoothness_profile(smoothness)
    return ProsodyAnalysisOptions(
        frame_ms=max(40, round(time_step_s * 4000)),
        max_number_of_candidates=15,
        min_correlation=min_correlation,
        min_rms=min_rms,
        octave_cost=octave_cost,
        octave_jump_cost=octave_jump_cost,
        pitch_ceiling_hz=ceiling,
        pitch_floor_hz=floor,
        silence_threshold=silence_threshold,
        smooth_window=smooth_window,
        time_step_s=time_step_s,
        voiced_unvoiced_cost=voiced_unvoiced_cost,
        voicing_threshold=voicing_threshold,
    )


def graph_voice_range(config: AudioProcessingConfig) -> str:
    """Return a known graph voice range setting."""
    return str(config.graph_voice_range) if config.graph_voice_range in VOICE_RANGES else "general"


def graph_recording_condition(config: AudioProcessingConfig) -> str:
    """Return a known graph recording condition setting."""
    value = str(config.graph_recording_condition)
    return value if value in RECORDING_CONDITIONS else "auto"


def graph_smoothness(config: AudioProcessingConfig) -> str:
    """Return a known graph smoothness setting."""
    value = str(config.graph_smoothness)
    return value if value in SMOOTHNESSES else "balanced"


def graph_voice_lock(config: AudioProcessingConfig) -> str:
    """Return a known graph voice-lock setting."""
    value = str(config.graph_voice_lock)
    return value if value in VOICE_LOCKS else "balanced"


def graph_connect_short_dropouts_ms(config: AudioProcessingConfig) -> int:
    """Return bounded graph dropout-connection window in milliseconds."""
    return min(150, max(0, int(config.graph_connect_short_dropouts_ms)))


def postprocess_points(points: list[ProsodyPoint], config: AudioProcessingConfig) -> list[ProsodyPoint]:
    """Apply graph smoothing and short-dropout connection to analysis points."""
    connected = _connect_short_dropouts(points, graph_connect_short_dropouts_ms(config))
    return _smooth_pitch(connected, resolve_analysis_options(config).smooth_window)


def _enum_or_none(value: object, allowed: Container[str]) -> str | None:
    text = str(value)
    return text if text in allowed else None


def _int_or_none(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if not isinstance(value, str):
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _config_key_settings(settings: dict[str, object]) -> dict[str, object]:
    sanitized: dict[str, object] = {}
    voice_range = _enum_or_none(settings.get("graph_voice_range"), VOICE_RANGES)
    if voice_range is not None:
        sanitized["graph_voice_range"] = voice_range
    recording_condition = _enum_or_none(settings.get("graph_recording_condition"), RECORDING_CONDITIONS)
    if recording_condition is not None:
        sanitized["graph_recording_condition"] = recording_condition
    smoothness = _enum_or_none(settings.get("graph_smoothness"), SMOOTHNESSES)
    if smoothness is not None:
        sanitized["graph_smoothness"] = smoothness
    voice_lock = _enum_or_none(settings.get("graph_voice_lock"), VOICE_LOCKS)
    if voice_lock is not None:
        sanitized["graph_voice_lock"] = voice_lock
    dropout_ms = _int_or_none(settings.get("graph_connect_short_dropouts_ms"))
    if dropout_ms is not None:
        sanitized["graph_connect_short_dropouts_ms"] = min(150, max(0, dropout_ms))
    return sanitized


def _condition_profile(condition: str) -> tuple[float, float, float, float]:
    profiles = {
        "very_noisy": (0.08, 0.65, 100.0, 0.70),
        "noisy": (0.05, 0.55, 75.0, 0.62),
        "normal": (0.03, 0.45, 50.0, 0.55),
        "clean": (0.02, 0.38, 35.0, 0.48),
        "studio": (0.01, 0.32, 25.0, 0.42),
    }
    return profiles.get(condition, profiles["normal"])


def _voice_lock_profile(lock: str) -> tuple[float, float, float]:
    profiles = {
        "loose": (0.005, 0.20, 0.08),
        "balanced": (0.01, 0.35, 0.14),
        "stable": (0.02, 0.60, 0.25),
    }
    return profiles.get(lock, profiles["balanced"])


def _smoothness_profile(smoothness: str) -> tuple[float, int]:
    profiles = {
        "raw": (0.005, 1),
        "balanced": (0.01, 1),
        "smooth": (0.01, 3),
        "very_smooth": (0.02, 5),
    }
    return profiles.get(smoothness, profiles["balanced"])


def _connect_short_dropouts(points: list[ProsodyPoint], max_gap_ms: int) -> list[ProsodyPoint]:
    if max_gap_ms <= 0 or len(points) < 3:
        return list(points)
    result = list(points)
    index = 1
    while index < len(result) - 1:
        if _has_voiced_pitch(result[index]):
            index += 1
            continue
        gap_start = index
        index = _next_voiced_pitch_index(result, index)
        bounds = _dropout_bounds(result, gap_start, index, max_gap_ms)
        if bounds is None:
            continue
        _fill_dropout(result, gap_start, index, *bounds)
    return result


def _has_voiced_pitch(point: ProsodyPoint) -> bool:
    return point.voiced and point.pitch_hz is not None


def _next_voiced_pitch_index(points: list[ProsodyPoint], start: int) -> int:
    index = start
    while index < len(points) and not _has_voiced_pitch(points[index]):
        index += 1
    return index


def _dropout_bounds(
    points: list[ProsodyPoint],
    gap_start: int,
    gap_end: int,
    max_gap_ms: int,
) -> tuple[ProsodyPoint, ProsodyPoint] | None:
    if gap_start <= 0 or gap_end >= len(points):
        return None
    before = points[gap_start - 1]
    after = points[gap_end]
    if not _has_voiced_pitch(before) or not _has_voiced_pitch(after):
        return None
    return (before, after) if after.time_ms - before.time_ms <= max_gap_ms else None


def _fill_dropout(
    points: list[ProsodyPoint],
    gap_start: int,
    gap_end: int,
    before: ProsodyPoint,
    after: ProsodyPoint,
) -> None:
    if before.pitch_hz is None or after.pitch_hz is None:
        return
    span = max(1, after.time_ms - before.time_ms)
    for gap_index in range(gap_start, gap_end):
        point = points[gap_index]
        ratio = (point.time_ms - before.time_ms) / span
        pitch = before.pitch_hz + (after.pitch_hz - before.pitch_hz) * ratio
        points[gap_index] = replace(point, pitch_hz=pitch, voiced=True)


def _smooth_pitch(points: list[ProsodyPoint], window: int) -> list[ProsodyPoint]:
    if window <= 1:
        return list(points)
    radius = window // 2
    result = list(points)
    for index, point in enumerate(points):
        if not point.voiced or point.pitch_hz is None:
            continue
        values = [
            nearby.pitch_hz
            for nearby in points[max(0, index - radius) : index + radius + 1]
            if nearby.voiced and nearby.pitch_hz is not None
        ]
        if values:
            result[index] = replace(point, pitch_hz=sum(values) / len(values))
    return result
