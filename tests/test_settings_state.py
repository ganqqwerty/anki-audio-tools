"""Tests for import-safe settings initial state construction."""

from __future__ import annotations

import json

from anki_audio_quick_editor.settings_state import (
    build_initial_state_payload,
    encode_initial_state,
)


def _full_config() -> dict[str, object]:
    return {
        "_config_version": 1,
        "enabled": True,
        "debug_logging": False,
        "show_ffmpeg_commands": False,
        "repeat_playback_by_default": True,
        "repeat_pause_seconds": 0.0,
        "voice_recording_countdown_seconds": 3,
        "share_target": "litterbox",
        "show_graph_by_default": True,
        "visible_editor_buttons": [
            "aqe:play",
            "aqe:analyze",
            "aqe:show-file",
            "aqe:share",
            "aqe:remove-pauses",
            "aqe:denoise-standard",
            "aqe:slower",
            "aqe:faster",
            "aqe:undo",
            "aqe:redo",
            "aqe:settings",
        ],
        "editor_button_modes": {
            "aqe:play": "icon",
            "aqe:analyze": "icon",
            "aqe:record-voice": "icon",
            "aqe:play-recording": "icon",
            "aqe:show-file": "icon",
            "aqe:share": "icon",
            "aqe:convert": "text",
            "aqe:remove-pauses": "text",
            "aqe:denoise-standard": "text",
            "aqe:pitch-hum": "text",
            "aqe:slower": "icon",
            "aqe:faster": "icon",
            "aqe:volume-down": "icon",
            "aqe:volume-up": "icon",
            "aqe:undo": "icon",
            "aqe:redo": "icon",
            "aqe:settings": "icon",
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
        "pause_silencedetect_threshold_db": -45.0,
        "pause_silencedetect_min_silence_seconds": 0.3,
        "pause_silencedetect_min_speech_seconds": 0.1,
        "pause_silencedetect_preprocess_denoise": True,
        "pause_silero_threshold": 0.5,
        "pause_silero_min_silence_seconds": 0.45,
        "pause_silero_min_speech_seconds": 0.1,
        "pause_silero_preprocess_denoise": False,
        "output_format": "mp3",
        "ffmpeg_path": "/opt/homebrew/bin/ffmpeg",
        "deep_filter_post_filter": True,
        "dpdfnet_attn_limit_db": 12.0,
        "denoise_algorithm": "standard",
        "pitch_hum_mode": "direct",
        "pause_aggressiveness": "normal",
        "pause_detection_algorithm": "silencedetect",
    }


def _payload_args() -> dict[str, object]:
    return {
        "version": "0.1.0",
        "addon_id": "anki_audio_quick_editor",
        "addon_dir": "/tmp/addon",
        "collection_available": True,
        "locale": "de",
        "direction": "ltr",
        "messages": {"settings.title": "Einstellungen"},
    }


def _missing_runtime_status() -> dict[str, object]:
    return {
        "phase": "missing",
        "runtime_manifest_id": "",
        "platform": "",
        "runtime_root": "",
        "progress": 0,
        "message": "",
        "error": "",
    }


def test_build_initial_state_payload_has_settings_webview_shape() -> None:
    config = _full_config()
    payload = build_initial_state_payload(
        config,
        **_payload_args(),
    )

    assert payload == {
        "config": config,
        "version": "0.1.0",
        "addon_dir": "/tmp/addon",
        "log_file_path": "/tmp/addon/anki_audio_quick_editor.log",
        "locale": "de",
        "direction": "ltr",
        "messages": {"settings.title": "Einstellungen"},
        "diagnostics": {
            "addon_id": "anki_audio_quick_editor",
            "collection_available": True,
            "release_info": {
                "commit_hash": "",
                "commit_message": "",
            },
            "runtime": _missing_runtime_status(),
        },
    }


def test_encode_initial_state_returns_json() -> None:
    payload = build_initial_state_payload(
        _full_config(),
        **{**_payload_args(), "addon_id": "addon", "collection_available": False},
    )

    assert json.loads(encode_initial_state(payload)) == payload


def test_build_initial_state_payload_preserves_false_diagnostics_and_log_path() -> None:
    payload = build_initial_state_payload(
        {**_full_config(), "enabled": False},
        **{
            **_payload_args(),
            "addon_id": "addon",
            "addon_dir": "/tmp/custom-addon",
            "collection_available": False,
        },
    )

    assert payload["diagnostics"]["collection_available"] is False
    assert payload["log_file_path"] == "/tmp/custom-addon/anki_audio_quick_editor.log"
