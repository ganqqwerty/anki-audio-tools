"""Tests for the settings initial state JSON."""

from __future__ import annotations

import json

from anki_audio_quick_editor.settings.initial_state import build_initial_state


def _full_config() -> dict[str, object]:
    return {
        "_config_version": 8,
        "enabled": True,
        "debug_logging": False,
        "show_ffmpeg_commands": False,
        "repeat_playback_by_default": False,
        "manual_trim_small_ms": 100,
        "manual_trim_large_ms": 500,
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
    }


def test_initial_state_has_required_keys() -> None:
    state = json.loads(build_initial_state(_full_config()))

    assert set(state) == {
        "config",
        "version",
        "addon_dir",
        "log_file_path",
        "diagnostics",
    }
    assert state["diagnostics"]["addon_id"] == "anki_audio_quick_editor"
