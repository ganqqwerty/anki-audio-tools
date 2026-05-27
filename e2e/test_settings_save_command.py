"""E2E tests for settings save command integration."""

from __future__ import annotations

from unittest.mock import patch

from PyQt6.QtWidgets import QApplication

from e2e.conftest import import_runtime_addon_module
from e2e.editor_note_helpers import DEFAULT_VISIBLE_EDITOR_BUTTONS
from e2e.settings_dialog_command_helpers import bridge_command


def test_save_command_writes_config(anki_mw) -> None:
    current_config_version = import_runtime_addon_module(".config_migration").CURRENT_CONFIG_VERSION
    handle_settings_command = import_runtime_addon_module(".settings.commands").handle_settings_command

    config = {
        "_config_version": current_config_version,
        "enabled": False,
        "debug_logging": True,
        "show_ffmpeg_commands": False,
        "repeat_playback_by_default": False,
        "repeat_pause_seconds": 0.0,
        "voice_recording_countdown_seconds": 3,
        "share_target": "litterbox",
        "show_graph_by_default": False,
        "visible_editor_buttons": list(DEFAULT_VISIBLE_EDITOR_BUTTONS),
        "editor_button_modes": {
            "aqe:play": "text",
            "aqe:analyze": "text",
            "aqe:record-voice": "icon",
            "aqe:play-recording": "icon",
            "aqe:show-file": "text",
            "aqe:share": "text",
            "aqe:convert": "text",
            "aqe:remove-pauses": "text",
            "aqe:denoise-standard": "text",
            "aqe:pitch-hum": "text",
            "aqe:slower": "text",
            "aqe:faster": "text",
            "aqe:volume-down": "text",
            "aqe:volume-up": "text",
            "aqe:undo": "text",
            "aqe:redo": "text",
            "aqe:settings": "text",
        },
        "graph_voice_range": "general",
        "graph_recording_condition": "auto",
        "graph_smoothness": "very_smooth",
        "graph_connect_short_dropouts_ms": 240,
        "graph_voice_lock": "balanced",
        "speed_step": 1.5,
        "min_speed": 0.2,
        "max_speed": 5.0,
        "volume_step_db": 15.0,
        "min_volume_db": -40.0,
        "max_volume_db": 40.0,
        "pause_detection_algorithm": "silencedetect",
        "pause_aggressiveness": "normal",
        "pause_silencedetect_threshold_db": -45.0,
        "pause_silencedetect_min_silence_seconds": 0.3,
        "pause_silencedetect_min_speech_seconds": 0.1,
        "pause_silencedetect_preprocess_denoise": True,
        "pause_silero_threshold": 0.5,
        "pause_silero_min_silence_seconds": 0.45,
        "pause_silero_min_speech_seconds": 0.1,
        "pause_silero_preprocess_denoise": False,
        "output_format": "mp3",
        "ffmpeg_path": "",
        "deep_filter_post_filter": True,
        "dpdfnet_attn_limit_db": 12.0,
        "denoise_algorithm": "standard",
        "pitch_hum_mode": "direct",
    }
    eval_calls: list[str] = []
    dialog = type("Dialog", (), {"accept": lambda self: None, "reject": lambda self: None})()

    with patch.object(
        anki_mw.addonManager,
        "writeConfig",
        wraps=anki_mw.addonManager.writeConfig,
    ) as mock_write:
        handle_settings_command(
            bridge_command("settings.save", config),
            lambda js: eval_calls.append(js),
            dialog,
        )
        QApplication.processEvents()

    assert mock_write.called
    assert eval_calls == []
