from __future__ import annotations

import json
from unittest.mock import MagicMock

_NO_PAYLOAD = object()


def _bridge_command(command: str, payload: object = _NO_PAYLOAD) -> str:
    envelope = {"command": command}
    if payload is not _NO_PAYLOAD:
        envelope["payload"] = payload
    return "bridge:" + json.dumps(envelope)


def _make_dialog() -> MagicMock:
    dialog = MagicMock()
    dialog.accepted = False
    dialog.rejected = False
    dialog.accept.side_effect = lambda: setattr(dialog, "accepted", True)
    dialog.reject.side_effect = lambda: setattr(dialog, "rejected", True)
    return dialog


def _capture_eval() -> tuple[list[str], callable]:
    calls: list[str] = []

    def eval_fn(js: str) -> None:
        calls.append(js)

    return calls, eval_fn


def _full_config() -> dict[str, object]:
    return {
        "_config_version": 2,
        "enabled": True,
        "debug_logging": True,
        "show_ffmpeg_commands": False,
        "enable_reviewer_editor": True,
        "repeat_playback_by_default": True,
        "repeat_pause_seconds": 0.0,
        "voice_recording_countdown_seconds": 0,
        "share_target": "litterbox",
        "show_graph_by_default": True,
        "selection_marker_shift_buttons_enabled": False,
        "visible_editor_buttons": [
            "aqe:play",
            "aqe:analyze",
            "aqe:chorusing-practice",
            "aqe:chorusing-previous",
            "aqe:chorusing-next",
            "aqe:show-file",
            "aqe:share",
            "aqe:reduce-size",
            "aqe:remove-pauses",
            "aqe:denoise-standard",
            "aqe:slower",
            "aqe:faster",
            "aqe:delete-selection",
            "aqe:delete-rest",
            "aqe:undo",
            "aqe:redo",
            "aqe:settings",
        ],
        "editor_button_modes": {
            "aqe:play": "icon",
            "aqe:analyze": "icon",
            "aqe:chorusing-practice": "icon",
            "aqe:chorusing-previous": "icon",
            "aqe:chorusing-next": "icon",
            "aqe:record-voice": "icon",
            "aqe:play-recording": "icon",
            "aqe:share-recording": "icon",
            "aqe:show-recording-file": "icon",
            "aqe:show-file": "icon",
            "aqe:share": "icon",
            "aqe:convert": "text",
            "aqe:reduce-size": "text",
            "aqe:remove-pauses": "text",
            "aqe:denoise-standard": "text",
            "aqe:pitch-hum": "text",
            "aqe:slower": "icon",
            "aqe:faster": "icon",
            "aqe:delete-selection": "icon",
            "aqe:delete-rest": "icon",
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
        "size_reduction_mode": "normal",
        "size_reduction_bitrate_kbps": 64,
        "size_reduction_sample_rate_hz": 32000,
        "size_reduction_channels": 1,
        "ffmpeg_path": "/opt/homebrew/bin/ffmpeg",
        "deep_filter_post_filter": True,
        "dpdfnet_attn_limit_db": 12.0,
        "denoise_algorithm": "standard",
        "pitch_hum_mode": "direct",
        "pause_aggressiveness": "normal",
        "pause_detection_algorithm": "silencedetect",
    }

def _parse_callback(js: str, name: str) -> dict:
    prefix = f"window.{name}("
    assert js.startswith(prefix)
    return json.loads(js[len(prefix):-1])
