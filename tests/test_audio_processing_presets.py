"""Tests for import-safe processing preset validation."""

from __future__ import annotations

import pytest

from anki_audio_quick_editor.audio_processing_presets import (
    AudioProcessingPreset,
    presets_from_raw,
)


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


def test_presets_from_raw_normalizes_steps_and_parameters() -> None:
    presets = presets_from_raw(
        [
            {
                "id": " clean ",
                "name": " Clean + graph ",
                "steps": [
                    {
                        "id": "denoise",
                        "operation": "denoise",
                        "parameters": {
                            "denoise_algorithm": "dpdfnet",
                            "dpdfnet_attn_limit_db": 17.4,
                        },
                    },
                    {
                        "id": "faster",
                        "operation": "faster",
                        "parameters": {"speed_step": 99},
                    },
                ],
                "graph": _graph(True),
            }
        ]
    )

    assert len(presets) == 1
    preset = presets[0]
    assert isinstance(preset, AudioProcessingPreset)
    assert preset.id == "clean"
    assert preset.name == "Clean + graph"
    assert preset.graph.enabled is True
    assert [step.operation for step in preset.steps] == ["denoise", "faster"]
    assert preset.steps[0].parameters.denoise_algorithm == "dpdfnet"
    assert preset.steps[0].parameters.dpdfnet_attn_limit_db == 18.0
    assert preset.steps[1].parameters.speed_step == 5.0


def test_presets_from_raw_accepts_graph_only_preset() -> None:
    presets = presets_from_raw(
        [
            {
                "id": "graph",
                "name": "Graph only",
                "steps": [],
                "graph": _graph(True),
            }
        ]
    )

    assert presets[0].has_transforms is False
    assert presets[0].graph.enabled is True


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        ({"id": "", "name": "Name", "steps": [], "graph": _graph(True)}, "Preset ID"),
        ({"id": "one", "name": " ", "steps": [], "graph": _graph(True)}, "Preset name"),
        ({"id": "one", "name": "Name", "steps": [], "graph": _graph(False)}, "at least one"),
        (
            {
                "id": "one",
                "name": "Name",
                "steps": [{"id": "step", "operation": "graph", "parameters": {}}],
                "graph": _graph(False),
            },
            "Unsupported preset operation",
        ),
        (
            {
                "id": "one",
                "name": "Name",
                "steps": [
                    {"id": "same", "operation": "faster", "parameters": {}},
                    {"id": "same", "operation": "slower", "parameters": {}},
                ],
                "graph": _graph(False),
            },
            "Duplicate preset step ID",
        ),
        (
            {
                "id": "one",
                "name": "Name",
                "steps": [],
                "graph": {
                    "enabled": True,
                    "parameters": {
                        "graph_voice_range": "invalid",
                        "graph_recording_condition": "auto",
                        "graph_smoothness": "very_smooth",
                        "graph_connect_short_dropouts_ms": 240,
                        "graph_voice_lock": "balanced",
                    },
                },
            },
            "graph_voice_range",
        ),
    ],
)
def test_presets_from_raw_rejects_invalid_presets(
    raw: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        presets_from_raw([raw])


def test_presets_from_raw_rejects_duplicate_preset_ids_and_names() -> None:
    with pytest.raises(ValueError, match="Duplicate preset ID"):
        presets_from_raw(
            [
                {"id": "same", "name": "One", "steps": [], "graph": _graph(True)},
                {"id": "same", "name": "Two", "steps": [], "graph": _graph(True)},
            ]
        )

    with pytest.raises(ValueError, match="Duplicate preset name"):
        presets_from_raw(
            [
                {"id": "one", "name": "Same", "steps": [], "graph": _graph(True)},
                {"id": "two", "name": " same ", "steps": [], "graph": _graph(True)},
            ]
        )
