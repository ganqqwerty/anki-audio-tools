"""Tests for import-safe editor action transitions."""

from __future__ import annotations

from unittest.mock import patch

from anki_audio_quick_editor.audio_operations import (
    OP_CONVERT,
    OP_FASTER,
    OP_REMOVE_PAUSES,
    OP_SLOWER,
    OP_VOLUME_DOWN,
    OP_VOLUME_UP,
)
from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.editor_actions import (
    BRIDGE_COMMAND_TO_OPERATION,
    BRIDGE_COMMANDS,
    PROCESSING_COMMANDS,
    apply_processing_command,
    decode_editor_command_payload,
    processing_config_for_command,
)


def test_processing_commands_are_registered_bridge_commands() -> None:
    assert set(PROCESSING_COMMANDS) < set(BRIDGE_COMMANDS)


def test_batchable_processing_commands_map_to_shared_operations() -> None:
    assert BRIDGE_COMMAND_TO_OPERATION == {
        "aqe:slower": OP_SLOWER,
        "aqe:faster": OP_FASTER,
        "aqe:volume-down": OP_VOLUME_DOWN,
        "aqe:volume-up": OP_VOLUME_UP,
        "aqe:remove-pauses": OP_REMOVE_PAUSES,
        "aqe:convert": OP_CONVERT,
    }


def test_decode_processing_command_accepts_json_payload() -> None:
    decoded = decode_editor_command_payload(
        '{"command":"aqe:volume-up","fieldOrd":0,"overrides":{"volumeStepDb":6}}'
    )

    assert decoded.command == "aqe:volume-up"
    assert decoded.field_ord == 0
    assert decoded.overrides.volume_step_db == 6


def test_decode_graph_command_accepts_graph_settings() -> None:
    decoded = decode_editor_command_payload(
        '{"command":"aqe:analyze","fieldOrd":1,'
        '"graphSettings":{"voiceRange":"bass","smoothness":"very_smooth"}}'
    )

    assert decoded.command == "aqe:analyze"
    assert decoded.field_ord == 1
    assert decoded.graph_settings == {"voiceRange": "bass", "smoothness": "very_smooth"}


def test_decode_command_accepts_share_target_payload() -> None:
    decoded = decode_editor_command_payload(
        '{"command":"aqe:share","fieldOrd":0,"shareTarget":"litterbox"}'
    )

    assert decoded.command == "aqe:share"
    assert decoded.field_ord == 0
    assert decoded.share_target == "litterbox"


def test_apply_processing_command_handles_speed_and_feature_toggles() -> None:
    config = AudioProcessingConfig(speed_step=1.5)
    state = AudioEditState("clip.mp3")

    faster = apply_processing_command("aqe:faster", state, config)
    pauses_shortened = apply_processing_command("aqe:remove-pauses", state, config)

    assert faster == AudioEditState("clip.mp3", speed=1.5)
    assert pauses_shortened == AudioEditState("clip.mp3", remove_internal_pauses_enabled=True)


def test_apply_processing_command_handles_volume_steps() -> None:
    config = AudioProcessingConfig(volume_step_db=2.5)
    state = AudioEditState("clip.mp3")

    louder = apply_processing_command("aqe:volume-up", state, config)
    quieter = apply_processing_command("aqe:volume-down", state, config)

    assert louder == AudioEditState("clip.mp3", volume_db=2.5)
    assert quieter == AudioEditState("clip.mp3", volume_db=-2.5)


def test_apply_processing_command_uses_volume_override_without_mutating_config() -> None:
    config = AudioProcessingConfig(volume_step_db=2.5)
    state = AudioEditState("clip.mp3")
    decoded = decode_editor_command_payload(
        '{"command":"aqe:volume-up","fieldOrd":0,"overrides":{"volumeStepDb":6}}'
    )

    updated = apply_processing_command(decoded, state, config)

    assert decoded.overrides.volume_step_db == 6
    assert updated == AudioEditState("clip.mp3", volume_db=6)
    assert config.volume_step_db == 2.5


def test_apply_processing_command_uses_speed_override_without_mutating_config() -> None:
    config = AudioProcessingConfig(speed_step=1.5)
    state = AudioEditState("clip.mp3")
    decoded = decode_editor_command_payload(
        '{"command":"aqe:faster","fieldOrd":0,"overrides":{"speedStep":2}}'
    )

    updated = apply_processing_command(decoded, state, config)

    assert decoded.overrides.speed_step == 2
    assert updated == AudioEditState("clip.mp3", speed=2.0)
    assert config.speed_step == 1.5


def test_decode_processing_command_accepts_pause_aggressiveness_override() -> None:
    decoded = decode_editor_command_payload(
        '{"command":"aqe:remove-pauses","fieldOrd":0,"overrides":{"pauseAggressiveness":"aggressive"}}'
    )

    assert decoded.overrides.pause_aggressiveness == "aggressive"


def test_decode_command_accepts_dpdfnet_aggressiveness_override() -> None:
    decoded = decode_editor_command_payload(
        '{"command":"aqe:dpdfnet","fieldOrd":0,'
        '"overrides":{"denoiseAlgorithm":"dpdfnet","dpdfnetAttnLimitDb":18}}'
    )

    assert decoded.overrides.denoise_algorithm == "dpdfnet"
    assert decoded.overrides.dpdfnet_attn_limit_db == 18.0


def test_decode_command_accepts_convert_target_format_override() -> None:
    decoded = decode_editor_command_payload(
        '{"command":"aqe:convert","fieldOrd":0,"overrides":{"targetFormat":"flac"}}'
    )

    assert decoded.overrides.target_format == "flac"


def test_decode_command_accepts_pitch_hum_mode_override() -> None:
    decoded = decode_editor_command_payload(
        '{"command":"aqe:pitch-hum","fieldOrd":0,"overrides":{"pitchHumMode":"pitch_tier"}}'
    )

    assert decoded.overrides.pitch_hum_mode == "pitch_tier"


def test_apply_processing_command_uses_pause_aggressiveness_without_mutating_config() -> None:
    config = AudioProcessingConfig(
        pause_aggressiveness="normal",
        pause_detection_algorithm="silencedetect",
        pause_silencedetect_threshold_db=-45,
        pause_silencedetect_min_silence_seconds=0.30,
        pause_silencedetect_min_speech_seconds=0.10,
    )
    state = AudioEditState("clip.mp3")
    decoded = decode_editor_command_payload(
        '{"command":"aqe:remove-pauses","fieldOrd":0,"overrides":{"pauseAggressiveness":"aggressive"}}'
    )
    captured: dict[str, AudioProcessingConfig] = {}

    def fake_apply(operation: str, current_state: AudioEditState, effective_config: AudioProcessingConfig) -> AudioEditState:
        captured["config"] = effective_config
        return current_state.toggle_internal_pauses()

    with patch("anki_audio_quick_editor.editor_actions.apply_audio_operation", fake_apply):
        updated = apply_processing_command(decoded, state, config)

    assert updated == AudioEditState("clip.mp3", remove_internal_pauses_enabled=True)
    assert captured["config"].pause_aggressiveness == "aggressive"
    assert captured["config"].pause_silencedetect_threshold_db == -52
    assert captured["config"].pause_silencedetect_min_silence_seconds == 0.14
    assert captured["config"].pause_silencedetect_min_speech_seconds == 0.04
    assert config.pause_aggressiveness == "normal"
    assert config.pause_silencedetect_min_silence_seconds == 0.30


def test_processing_config_for_command_returns_render_config_with_local_overrides() -> None:
    config = AudioProcessingConfig(
        volume_step_db=15,
        speed_step=1.5,
        pause_aggressiveness="normal",
        pause_detection_algorithm="silencedetect",
        pause_silencedetect_threshold_db=-45,
        pause_silencedetect_min_silence_seconds=0.30,
        pause_silencedetect_min_speech_seconds=0.10,
    )
    decoded = decode_editor_command_payload(
        '{"command":"aqe:remove-pauses","fieldOrd":0,'
        '"overrides":{"pauseAggressiveness":"aggressive","volumeStepDb":6,"speedStep":2}}'
    )

    effective = processing_config_for_command(decoded, config)

    assert effective.volume_step_db == 6
    assert effective.speed_step == 2
    assert effective.pause_aggressiveness == "aggressive"
    assert effective.pause_silencedetect_threshold_db == -52
    assert effective.pause_silencedetect_min_silence_seconds == 0.14
    assert effective.pause_silencedetect_min_speech_seconds == 0.04
    assert config.pause_aggressiveness == "normal"


def test_apply_processing_command_returns_none_for_non_processing_command() -> None:
    config = AudioProcessingConfig()
    state = AudioEditState("clip.mp3")

    assert apply_processing_command("aqe:play", state, config) is None


def test_apply_processing_command_returns_none_for_convert_command() -> None:
    config = AudioProcessingConfig()
    state = AudioEditState("clip.mp3")

    assert apply_processing_command("aqe:convert", state, config) is None


def test_play_graph_cursor_and_play_ended_are_not_processing_commands() -> None:
    assert {
        "aqe:play",
        "aqe:play-ended",
        "aqe:stop-playback",
        "aqe:show-file",
        "aqe:share",
        "aqe:analyze",
        "aqe:analyze-field",
        "aqe:set-cursor",
        "aqe:denoise-standard",
        "aqe:rnnoise",
        "aqe:dpdfnet",
        "aqe:voice-only",
        "aqe:pitch-hum",
        "aqe:settings",
        "aqe:redo",
        "aqe:trim-silence",
    }.isdisjoint(PROCESSING_COMMANDS)

    assert "aqe:denoise-standard" in BRIDGE_COMMANDS
    assert "aqe:rnnoise" in BRIDGE_COMMANDS
    assert "aqe:dpdfnet" in BRIDGE_COMMANDS
    assert "aqe:voice-only" in BRIDGE_COMMANDS
    assert "aqe:pitch-hum" in BRIDGE_COMMANDS
    assert "aqe:settings" in BRIDGE_COMMANDS
    assert "aqe:redo" in BRIDGE_COMMANDS
    assert "aqe:analyze-field" in BRIDGE_COMMANDS
    assert ("aqe:" + "si" + "don") not in BRIDGE_COMMANDS


def test_share_command_is_registered_but_not_processing() -> None:
    assert "aqe:share" in BRIDGE_COMMANDS
    assert "aqe:share" not in PROCESSING_COMMANDS
