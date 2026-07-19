"""Tests for import-safe trigger rule validation and matching."""

from __future__ import annotations

import pytest

from anki_audio_quick_editor.audio_processing_presets import presets_from_raw
from anki_audio_quick_editor.trigger_rules import (
    AudioTriggerRule,
    action_fingerprint,
    first_supported_sound_filename,
    note_type_matches,
    rule_applies_to_event,
    trigger_rules_from_raw,
)


def _note_type() -> dict[str, object]:
    return {"id": 123, "name": "Basic"}


def _graph(enabled: bool = False) -> dict[str, object]:
    return {
        "enabled": enabled,
        "parameters": {
            "graph_voice_range": "general",
            "graph_recording_condition": "auto",
            "graph_smoothness": "very_smooth",
            "graph_connect_short_dropouts_ms": 240,
            "graph_voice_lock": "balanced",
        },
    }


def _operation_rule(
    *,
    operation: str = "remove_pauses",
    target_field: str | None = None,
    parameters: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "id": "trigger_clean_basic_audio",
        "name": "Clean Basic audio on add",
        "enabled": True,
        "event": "add",
        "note_type": _note_type(),
        "source_field": "Audio",
        "action_type": "operation",
        "operation": operation,
        "preset_id": None,
        "target_field": target_field,
        "parameters": parameters or {},
    }


def _preset_rule(preset_id: str = "preset_clean") -> dict[str, object]:
    return {
        "id": "trigger_preset_basic_audio",
        "name": "Clean preset on add",
        "enabled": True,
        "event": "add",
        "note_type": _note_type(),
        "source_field": "Audio",
        "action_type": "preset",
        "operation": None,
        "preset_id": preset_id,
        "target_field": None,
        "parameters": {},
    }


def _preset(step_speed: float = 1.5) -> tuple:
    return presets_from_raw(
        [
            {
                "id": "preset_clean",
                "name": "Clean",
                "steps": [
                    {
                        "id": "faster",
                        "operation": "faster",
                        "parameters": {"speed_step": step_speed},
                    }
                ],
                "graph": _graph(False),
            }
        ]
    )


def test_trigger_rules_parse_transform_rule() -> None:
    rules = trigger_rules_from_raw(
        [
            _operation_rule(
                parameters={
                    "pause_aggressiveness": "aggressive",
                    "pause_detection_algorithm": "silencedetect",
                    "pause_threshold": -40,
                }
            )
        ]
    )

    rule = rules[0]
    assert isinstance(rule, AudioTriggerRule)
    assert rule.id == "trigger_clean_basic_audio"
    assert rule.enabled is True
    assert rule.event == "add"
    assert rule.note_type.id == 123
    assert rule.note_type.name == "Basic"
    assert rule.operation == "remove_pauses"
    assert rule.parameters.pause_aggressiveness == "aggressive"
    assert rule.parameters.pause_threshold == -40.0


def test_trigger_rules_parse_graph_rule_requires_target_field() -> None:
    with pytest.raises(ValueError, match="target field"):
        trigger_rules_from_raw([_operation_rule(operation="graph", target_field=None)])

    rule = trigger_rules_from_raw(
        [
            _operation_rule(
                operation="graph",
                target_field="Graph",
                parameters={
                    "graph_voice_range": "general",
                    "graph_recording_condition": "auto",
                    "graph_smoothness": "very_smooth",
                    "graph_connect_short_dropouts_ms": 240,
                    "graph_voice_lock": "balanced",
                },
            )
        ]
    )[0]

    assert rule.target_field == "Graph"
    assert rule.graph_parameters.graph_smoothness == "very_smooth"


def test_trigger_rules_parse_reduce_size_parameters() -> None:
    rule = trigger_rules_from_raw(
        [
            _operation_rule(
                operation="reduce_size",
                parameters={
                    "size_reduction_mode": "normal",
                    "size_reduction_bitrate_kbps": 64,
                    "size_reduction_sample_rate_hz": 32000,
                    "size_reduction_channels": 1,
                },
            )
        ]
    )[0]

    assert rule.operation == "reduce_size"
    assert rule.parameters.size_reduction_mode == "normal"
    assert rule.parameters.size_reduction_bitrate_kbps == 64
    assert rule.parameters.size_reduction_sample_rate_hz == 32000
    assert rule.parameters.size_reduction_channels == 1


def test_trigger_rules_parse_preset_rule() -> None:
    rules = trigger_rules_from_raw([_preset_rule()], presets=_preset())

    rule = rules[0]
    assert rule.action_type == "preset"
    assert rule.operation is None
    assert rule.preset_id == "preset_clean"
    assert rule.parameters.speed_step is None


def test_trigger_rules_require_existing_preset_by_default() -> None:
    with pytest.raises(ValueError, match="Unknown processing preset"):
        trigger_rules_from_raw([_preset_rule()])


def test_trigger_rules_reject_duplicate_ids() -> None:
    duplicate = _operation_rule()

    with pytest.raises(ValueError, match="Duplicate trigger rule ID"):
        trigger_rules_from_raw([duplicate, duplicate])


def test_trigger_rules_match_event_note_type_and_field() -> None:
    rule = trigger_rules_from_raw([_operation_rule()])[0]

    assert rule_applies_to_event(rule, "add") is True
    assert rule_applies_to_event(rule, "edit") is False
    assert note_type_matches(rule, 123, "Other") is True
    assert note_type_matches(rule, 456, "Basic") is False

    fallback_rule = trigger_rules_from_raw(
        [{**_operation_rule(), "note_type": {"id": None, "name": "Basic"}}]
    )[0]
    assert note_type_matches(fallback_rule, 456, "Basic") is True


def test_trigger_rules_action_fingerprint_changes_with_parameters() -> None:
    first = trigger_rules_from_raw([_operation_rule(parameters={"speed_step": 1.2})])[0]
    second = trigger_rules_from_raw([_operation_rule(parameters={"speed_step": 1.8})])[0]

    assert action_fingerprint(first, ()) != action_fingerprint(second, ())


def test_trigger_rules_action_fingerprint_changes_with_preset_content() -> None:
    rule = trigger_rules_from_raw([_preset_rule()], presets=_preset())[0]

    assert action_fingerprint(rule, _preset(1.5)) != action_fingerprint(rule, _preset(2.0))


def test_first_supported_sound_filename_returns_first_supported_reference() -> None:
    assert first_supported_sound_filename("before [sound:voice.mp3] after") == "voice.mp3"
    assert first_supported_sound_filename("before [sound:notes.txt] after") is None
