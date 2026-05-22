"""Tests for the settings initial state JSON."""

from __future__ import annotations

import json

from anki_audio_quick_editor.settings.initial_state import build_initial_state


def _full_config() -> dict[str, object]:
    return {
        "_config_version": 17,
        "enabled": True,
        "debug_logging": False,
        "show_ffmpeg_commands": False,
        "repeat_playback_by_default": False,
        "repeat_pause_seconds": 0.0,
        "show_graph_by_default": False,
        "graph_voice_range": "general",
        "graph_recording_condition": "auto",
        "graph_smoothness": "very_smooth",
        "graph_connect_short_dropouts_ms": 240,
        "graph_voice_lock": "balanced",
        "speed_step": 0.05,
        "min_speed": 0.75,
        "max_speed": 1.5,
        "volume_step_db": 3.0,
        "min_volume_db": -24.0,
        "max_volume_db": 24.0,
        "internal_pause_silence_threshold_db": -45,
        "internal_pause_threshold_ms": 300,
        "internal_pause_target_gap_ms": 100,
        "output_format": "mp3",
        "ffmpeg_path": "",
        "deep_filter_path": "",
        "deep_filter_post_filter": True,
        "dpdfnet_attn_limit_db": 12.0,
        "denoise_algorithm": "standard",
        "pitch_hum_mode": "direct",
        "pause_aggressiveness": "normal",
    }


def test_initial_state_has_required_keys() -> None:
    state = json.loads(build_initial_state(_full_config()))

    assert set(state) == {
        "config",
        "version",
        "addon_dir",
        "log_file_path",
        "locale",
        "direction",
        "messages",
        "diagnostics",
    }
    assert state["diagnostics"]["addon_id"] == "anki_audio_quick_editor"
    assert state["locale"] == "en"
    assert state["direction"] == "ltr"
    assert "settings.title" in state["messages"]
