"""Tests for user-facing graph analysis settings."""

from __future__ import annotations

from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.prosody_settings import (
    config_with_graph_settings,
    postprocess_points,
    resolve_analysis_options,
    sanitize_graph_settings,
)
from anki_audio_quick_editor.prosody_types import ProsodyPoint


def test_sanitize_graph_settings_accepts_known_values_and_bounds_numbers() -> None:
    settings = sanitize_graph_settings(
        {
            "voiceRange": "bass",
            "recordingCondition": "noisy",
            "smoothness": "very_smooth",
            "connectShortDropoutsMs": 999,
            "voiceLock": "stable",
            "extra": "ignored",
        }
    )

    assert settings == {
        "graph_voice_range": "bass",
        "graph_recording_condition": "noisy",
        "graph_smoothness": "very_smooth",
        "graph_connect_short_dropouts_ms": 150,
        "graph_voice_lock": "stable",
    }


def test_config_with_graph_settings_ignores_unknown_values() -> None:
    config = config_with_graph_settings(
        AudioProcessingConfig(),
        {
            "voiceRange": "not-a-range",
            "recordingCondition": "studio",
            "connectShortDropoutsMs": -5,
        },
    )

    assert config.graph_voice_range == "general"
    assert config.graph_recording_condition == "studio"
    assert config.graph_connect_short_dropouts_ms == 0


def test_resolve_analysis_options_maps_metaphors_to_praat_controls() -> None:
    options = resolve_analysis_options(
        AudioProcessingConfig(
            graph_voice_range="child",
            graph_recording_condition="studio",
            graph_smoothness="very_smooth",
            graph_voice_lock="stable",
        )
    )

    assert options.pitch_floor_hz == 150.0
    assert options.pitch_ceiling_hz == 1000.0
    assert options.silence_threshold == 0.01
    assert options.voicing_threshold == 0.32
    assert options.smooth_window == 5
    assert options.octave_jump_cost == 0.60


def test_postprocess_points_connects_short_dropouts_and_smooths_pitch() -> None:
    points = [
        ProsodyPoint(0, 100.0, -20.0, 0.5, True),
        ProsodyPoint(30, None, -20.0, 0.5, False),
        ProsodyPoint(60, 160.0, -20.0, 0.5, True),
        ProsodyPoint(90, 220.0, -20.0, 0.5, True),
    ]
    config = AudioProcessingConfig(
        graph_connect_short_dropouts_ms=60,
        graph_smoothness="smooth",
    )

    processed = postprocess_points(points, config)

    assert [point.voiced for point in processed] == [True, True, True, True]
    assert [point.pitch_hz for point in processed] == [115.0, 130.0, 170.0, 190.0]
