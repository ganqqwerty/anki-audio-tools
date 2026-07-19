"""Import-safe trigger rule model, validation, and matching helpers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Literal, cast

from .audio_operation_params import AudioOperationParameters, parameters_from_raw
from .audio_operations import BATCH_OPERATIONS, OP_GRAPH, is_transform_operation
from .audio_processing_presets import AudioProcessingPreset, preset_by_id
from .errors import UnsupportedAudioError
from .sound_refs import select_first_sound_reference

TriggerEvent = Literal["add", "edit"]
TriggerActionType = Literal["operation", "preset"]

GRAPH_VOICE_RANGES = frozenset({"bass", "low", "general", "high", "child"})
GRAPH_RECORDING_CONDITIONS = frozenset(
    {"auto", "very_noisy", "noisy", "normal", "clean", "studio"}
)
GRAPH_SMOOTHNESS_VALUES = frozenset({"raw", "balanced", "smooth", "very_smooth"})
GRAPH_VOICE_LOCKS = frozenset({"loose", "balanced", "stable"})


@dataclass(frozen=True)
class TriggerNoteTypeRef:
    """Stored note type identity used to match trigger rules."""

    id: int | None
    name: str


@dataclass(frozen=True)
class AudioTriggerGraphParameters:
    """Graph parameters saved directly on a trigger rule."""

    graph_voice_range: str | None = None
    graph_recording_condition: str | None = None
    graph_smoothness: str | None = None
    graph_connect_short_dropouts_ms: int | None = None
    graph_voice_lock: str | None = None


@dataclass(frozen=True)
class AudioTriggerRule:
    """One config-backed automatic audio processing rule."""

    id: str
    name: str
    enabled: bool
    event: TriggerEvent
    note_type: TriggerNoteTypeRef
    source_field: str
    action_type: TriggerActionType
    operation: str | None
    preset_id: str | None
    target_field: str | None
    parameters: AudioOperationParameters
    graph_parameters: AudioTriggerGraphParameters


def trigger_rules_from_raw(
    raw: Any,
    *,
    presets: tuple[AudioProcessingPreset, ...] = (),
    allow_missing_presets: bool = False,
) -> tuple[AudioTriggerRule, ...]:
    """Parse and validate a raw config ``audio_trigger_rules`` value."""
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ValueError("audio_trigger_rules must be a list")
    rules = tuple(
        _rule_from_raw(
            item,
            presets=presets,
            allow_missing_presets=allow_missing_presets,
        )
        for item in raw
    )
    _validate_unique_rule_ids(rules)
    return rules


def note_type_matches(
    rule: AudioTriggerRule,
    note_type_id: int | None,
    note_type_name: str,
) -> bool:
    """Return whether ``rule`` applies to the given note type identity."""
    if rule.note_type.id is not None and note_type_id is not None:
        return rule.note_type.id == note_type_id
    return rule.note_type.name == note_type_name


def rule_applies_to_event(rule: AudioTriggerRule, event: str) -> bool:
    """Return whether ``rule`` is enabled and configured for ``event``."""
    return rule.enabled and rule.event == event


def first_supported_sound_filename(field_html: str) -> str | None:
    """Return the first supported sound filename in ``field_html``."""
    try:
        selection = select_first_sound_reference(field_html)
    except UnsupportedAudioError:
        return None
    return selection.selected.filename if selection.selected is not None else None


def action_fingerprint(
    rule: AudioTriggerRule,
    presets: tuple[AudioProcessingPreset, ...],
) -> str:
    """Return a stable fingerprint for the action selected by ``rule``."""
    if rule.action_type == "preset":
        assert rule.preset_id is not None
        preset = preset_by_id(presets, rule.preset_id)
        payload: dict[str, Any] = {
            "action_type": rule.action_type,
            "preset": asdict(preset),
            "target_field": rule.target_field,
        }
    else:
        payload = {
            "action_type": rule.action_type,
            "operation": rule.operation,
            "parameters": asdict(rule.parameters),
            "graph_parameters": asdict(rule.graph_parameters),
            "target_field": rule.target_field,
        }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _rule_from_raw(
    raw: Any,
    *,
    presets: tuple[AudioProcessingPreset, ...],
    allow_missing_presets: bool,
) -> AudioTriggerRule:
    if not isinstance(raw, dict):
        raise ValueError("Trigger rule must be an object")
    rule_id = _required_text(raw.get("id"), "Trigger rule ID")
    name = _required_text(raw.get("name"), "Trigger rule name")
    enabled = _required_bool(raw.get("enabled"), "Trigger rule enabled")
    event = _event(raw.get("event"))
    note_type = _note_type_from_raw(raw.get("note_type"))
    source_field = _required_text(raw.get("source_field"), "Trigger source field")
    action_type = _action_type(raw.get("action_type"))
    parameters = _parameters_from_raw(raw.get("parameters"))
    graph_parameters = _graph_parameters_from_raw(raw.get("parameters"))
    operation = raw.get("operation")
    preset_id = raw.get("preset_id")
    target_field = _optional_text(raw.get("target_field"), "Trigger target field")

    if action_type == "operation":
        operation = _operation(operation)
        _none_value(preset_id, "Trigger preset ID")
        preset_id = None
        _validate_operation_target(operation, target_field)
    else:
        _none_value(operation, "Trigger operation")
        operation = None
        preset_id = _required_text(preset_id, "Trigger preset ID")
        _validate_preset_target(
            preset_id,
            target_field,
            presets,
            allow_missing_presets=allow_missing_presets,
        )

    return AudioTriggerRule(
        id=rule_id,
        name=name,
        enabled=enabled,
        event=event,
        note_type=note_type,
        source_field=source_field,
        action_type=action_type,
        operation=operation,
        preset_id=preset_id,
        target_field=target_field,
        parameters=parameters,
        graph_parameters=graph_parameters,
    )


def _note_type_from_raw(raw: Any) -> TriggerNoteTypeRef:
    if not isinstance(raw, dict):
        raise ValueError("Trigger note type must be an object")
    note_type_id = raw.get("id")
    if note_type_id is not None and (
        isinstance(note_type_id, bool) or not isinstance(note_type_id, int)
    ):
        raise ValueError("Trigger note type ID must be an integer or null")
    return TriggerNoteTypeRef(
        id=note_type_id,
        name=_required_text(raw.get("name"), "Trigger note type name"),
    )


def _parameters_from_raw(raw: Any) -> AudioOperationParameters:
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError("Trigger parameters must be an object")
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


def _graph_parameters_from_raw(raw: Any) -> AudioTriggerGraphParameters:
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError("Trigger parameters must be an object")
    return AudioTriggerGraphParameters(
        graph_voice_range=_optional_enum(
            raw.get("graph_voice_range"),
            GRAPH_VOICE_RANGES,
            "graph_voice_range",
        ),
        graph_recording_condition=_optional_enum(
            raw.get("graph_recording_condition"),
            GRAPH_RECORDING_CONDITIONS,
            "graph_recording_condition",
        ),
        graph_smoothness=_optional_enum(
            raw.get("graph_smoothness"),
            GRAPH_SMOOTHNESS_VALUES,
            "graph_smoothness",
        ),
        graph_connect_short_dropouts_ms=_optional_int_in_range(
            raw.get("graph_connect_short_dropouts_ms"),
            0,
            500,
            "graph_connect_short_dropouts_ms",
        ),
        graph_voice_lock=_optional_enum(
            raw.get("graph_voice_lock"),
            GRAPH_VOICE_LOCKS,
            "graph_voice_lock",
        ),
    )


def _validate_operation_target(operation: str, target_field: str | None) -> None:
    if operation == OP_GRAPH:
        if target_field is None:
            raise ValueError("Graph trigger rules require a target field")
        return
    if is_transform_operation(operation) and target_field is not None:
        raise ValueError("Transform trigger rules must not set a target field")


def _validate_preset_target(
    preset_id: str,
    target_field: str | None,
    presets: tuple[AudioProcessingPreset, ...],
    *,
    allow_missing_presets: bool,
) -> None:
    try:
        preset = preset_by_id(presets, preset_id)
    except ValueError:
        if allow_missing_presets:
            return
        raise
    if preset.graph.enabled and target_field is None:
        raise ValueError("Preset trigger rules with Graph output require a target field")
    if not preset.graph.enabled and target_field is not None:
        raise ValueError("Preset trigger rules without Graph output must not set a target field")


def _operation(value: Any) -> str:
    operation = _required_text(value, "Trigger operation")
    if operation not in BATCH_OPERATIONS:
        raise ValueError(f"Unsupported trigger operation: {operation}")
    return operation


def _event(value: Any) -> TriggerEvent:
    if value not in {"add", "edit"}:
        raise ValueError(f"Invalid trigger event: {value}")
    return cast(TriggerEvent, value)


def _action_type(value: Any) -> TriggerActionType:
    if value not in {"operation", "preset"}:
        raise ValueError(f"Invalid trigger action type: {value}")
    return cast(TriggerActionType, value)


def _required_text(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string")
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{label} must not be empty")
    return stripped


def _optional_text(value: Any, label: str) -> str | None:
    if value is None:
        return None
    return _required_text(value, label)


def _required_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{label} must be boolean")
    return value


def _none_value(value: Any, label: str) -> None:
    if value is not None:
        raise ValueError(f"{label} must be null")


def _optional_enum(value: Any, allowed: frozenset[str], label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or value not in allowed:
        raise ValueError(f"Invalid {label}: {value}")
    return value


def _optional_int_in_range(value: Any, minimum: int, maximum: int, label: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Invalid {label}: {value}")
    if value < minimum or value > maximum:
        raise ValueError(f"Invalid {label}: {value}")
    return value


def _validate_unique_rule_ids(rules: tuple[AudioTriggerRule, ...]) -> None:
    seen: set[str] = set()
    for rule in rules:
        if rule.id in seen:
            raise ValueError(f"Duplicate trigger rule ID: {rule.id}")
        seen.add(rule.id)
