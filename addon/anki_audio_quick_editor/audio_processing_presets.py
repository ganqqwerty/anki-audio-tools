"""Import-safe processing preset model and validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .audio_operation_params import AudioOperationParameters, parameters_from_raw
from .audio_operations import TRANSFORM_OPERATIONS

GRAPH_VOICE_RANGES = frozenset({"bass", "low", "general", "high", "child"})
GRAPH_RECORDING_CONDITIONS = frozenset(
    {"auto", "very_noisy", "noisy", "normal", "clean", "studio"}
)
GRAPH_SMOOTHNESS_VALUES = frozenset({"raw", "balanced", "smooth", "very_smooth"})
GRAPH_VOICE_LOCKS = frozenset({"loose", "balanced", "stable"})
MIN_GRAPH_CONNECT_DROPOUTS_MS = 0
MAX_GRAPH_CONNECT_DROPOUTS_MS = 500


@dataclass(frozen=True)
class AudioProcessingPresetGraphParameters:
    """Graph parameters saved with a processing preset."""

    graph_voice_range: str
    graph_recording_condition: str
    graph_smoothness: str
    graph_connect_short_dropouts_ms: int
    graph_voice_lock: str


@dataclass(frozen=True)
class AudioProcessingPresetGraph:
    """Terminal graph output settings for a processing preset."""

    enabled: bool
    parameters: AudioProcessingPresetGraphParameters


@dataclass(frozen=True)
class AudioProcessingPresetStep:
    """One transform operation inside a processing preset."""

    id: str
    operation: str
    parameters: AudioOperationParameters


@dataclass(frozen=True)
class AudioProcessingPreset:
    """A user-saved ordered audio processing recipe."""

    id: str
    name: str
    steps: tuple[AudioProcessingPresetStep, ...]
    graph: AudioProcessingPresetGraph

    @property
    def has_transforms(self) -> bool:
        """Return true when this preset renders a final audio file."""
        return len(self.steps) > 0


def presets_from_raw(raw: Any) -> tuple[AudioProcessingPreset, ...]:
    """Parse and validate a raw config ``audio_processing_presets`` value."""
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ValueError("audio_processing_presets must be a list")
    presets = tuple(_preset_from_raw(item) for item in raw)
    _validate_unique_presets(presets)
    return presets


def preset_by_id(
    presets: tuple[AudioProcessingPreset, ...],
    preset_id: str,
) -> AudioProcessingPreset:
    """Return the preset with ``preset_id`` or raise ``ValueError``."""
    for preset in presets:
        if preset.id == preset_id:
            return preset
    raise ValueError(f"Unknown processing preset: {preset_id}")


def _preset_from_raw(raw: Any) -> AudioProcessingPreset:
    if not isinstance(raw, dict):
        raise ValueError("Processing preset must be an object")
    preset_id = _required_text(raw.get("id"), "Preset ID")
    name = _required_text(raw.get("name"), "Preset name")
    steps = _steps_from_raw(raw.get("steps"))
    graph = _graph_from_raw(raw.get("graph"))
    if not steps and not graph.enabled:
        raise ValueError("Processing preset must contain at least one transform step or Graph output")
    return AudioProcessingPreset(id=preset_id, name=name, steps=steps, graph=graph)


def _steps_from_raw(raw: Any) -> tuple[AudioProcessingPresetStep, ...]:
    if not isinstance(raw, list):
        raise ValueError("Preset steps must be a list")
    steps = tuple(_step_from_raw(item) for item in raw)
    seen: set[str] = set()
    for step in steps:
        if step.id in seen:
            raise ValueError(f"Duplicate preset step ID: {step.id}")
        seen.add(step.id)
    return steps


def _step_from_raw(raw: Any) -> AudioProcessingPresetStep:
    if not isinstance(raw, dict):
        raise ValueError("Preset step must be an object")
    step_id = _required_text(raw.get("id"), "Preset step ID")
    operation = _required_text(raw.get("operation"), "Preset step operation")
    if operation not in TRANSFORM_OPERATIONS:
        raise ValueError(f"Unsupported preset operation: {operation}")
    parameters = _parameters_from_raw(raw.get("parameters"))
    return AudioProcessingPresetStep(id=step_id, operation=operation, parameters=parameters)


def _parameters_from_raw(raw: Any) -> AudioOperationParameters:
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError("Preset step parameters must be an object")
    return parameters_from_raw(
        speed_step=raw.get("speed_step"),
        volume_step_db=raw.get("volume_step_db"),
        pause_aggressiveness=raw.get("pause_aggressiveness"),
        pause_detection_algorithm=raw.get("pause_detection_algorithm"),
        pause_threshold=raw.get("pause_threshold"),
        pause_min_silence_seconds=raw.get("pause_min_silence_seconds"),
        pause_min_speech_seconds=raw.get("pause_min_speech_seconds"),
        pause_preprocess_denoise=raw.get("pause_preprocess_denoise"),
        denoise_algorithm=raw.get("denoise_algorithm"),
        dpdfnet_attn_limit_db=raw.get("dpdfnet_attn_limit_db"),
        target_format=raw.get("target_format"),
        size_reduction_mode=raw.get("size_reduction_mode"),
        size_reduction_bitrate_kbps=raw.get("size_reduction_bitrate_kbps"),
        size_reduction_sample_rate_hz=raw.get("size_reduction_sample_rate_hz"),
        size_reduction_channels=raw.get("size_reduction_channels"),
    )


def _graph_from_raw(raw: Any) -> AudioProcessingPresetGraph:
    if not isinstance(raw, dict):
        raise ValueError("Preset graph must be an object")
    enabled = raw.get("enabled")
    if not isinstance(enabled, bool):
        raise ValueError("Preset graph enabled must be boolean")
    parameters = _graph_parameters_from_raw(raw.get("parameters"))
    return AudioProcessingPresetGraph(enabled=enabled, parameters=parameters)


def _graph_parameters_from_raw(raw: Any) -> AudioProcessingPresetGraphParameters:
    if not isinstance(raw, dict):
        raise ValueError("Preset graph parameters must be an object")
    voice_range = _enum_value(raw.get("graph_voice_range"), GRAPH_VOICE_RANGES, "graph_voice_range")
    recording_condition = _enum_value(
        raw.get("graph_recording_condition"),
        GRAPH_RECORDING_CONDITIONS,
        "graph_recording_condition",
    )
    smoothness = _enum_value(raw.get("graph_smoothness"), GRAPH_SMOOTHNESS_VALUES, "graph_smoothness")
    voice_lock = _enum_value(raw.get("graph_voice_lock"), GRAPH_VOICE_LOCKS, "graph_voice_lock")
    connect_ms = _int_in_range(
        raw.get("graph_connect_short_dropouts_ms"),
        MIN_GRAPH_CONNECT_DROPOUTS_MS,
        MAX_GRAPH_CONNECT_DROPOUTS_MS,
        "graph_connect_short_dropouts_ms",
    )
    return AudioProcessingPresetGraphParameters(
        graph_voice_range=voice_range,
        graph_recording_condition=recording_condition,
        graph_smoothness=smoothness,
        graph_connect_short_dropouts_ms=connect_ms,
        graph_voice_lock=voice_lock,
    )


def _required_text(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string")
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{label} must not be empty")
    return stripped


def _enum_value(value: Any, allowed: frozenset[str], label: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise ValueError(f"Invalid {label}: {value}")
    return value


def _int_in_range(value: Any, minimum: int, maximum: int, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Invalid {label}: {value}")
    if value < minimum or value > maximum:
        raise ValueError(f"Invalid {label}: {value}")
    return value


def _validate_unique_presets(presets: tuple[AudioProcessingPreset, ...]) -> None:
    seen_ids: set[str] = set()
    seen_names: set[str] = set()
    for preset in presets:
        if preset.id in seen_ids:
            raise ValueError(f"Duplicate preset ID: {preset.id}")
        seen_ids.add(preset.id)
        normalized_name = preset.name.casefold()
        if normalized_name in seen_names:
            raise ValueError(f"Duplicate preset name: {preset.name}")
        seen_names.add(normalized_name)
