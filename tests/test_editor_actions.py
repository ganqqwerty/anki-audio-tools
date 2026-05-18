"""Tests for import-safe editor action transitions."""

from __future__ import annotations

from unittest.mock import patch

from anki_audio_quick_editor.audio_operations import (
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
    operation_for_command,
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
    }
    assert operation_for_command("aqe:trim-left") is None
    assert operation_for_command("aqe:trim-right") is None


def test_apply_processing_command_uses_configured_trim_step() -> None:
    config = AudioProcessingConfig(manual_trim_small_ms=250)
    state = AudioEditState("clip.mp3")

    updated = apply_processing_command("aqe:trim-left", state, config)

    assert updated == AudioEditState("clip.mp3", left_trim_ms=250)


def test_decode_processing_command_accepts_json_payload() -> None:
    decoded = decode_editor_command_payload(
        '{"command":"aqe:trim-left","fieldOrd":0,"overrides":{"trimStepMs":200}}'
    )

    assert decoded.command == "aqe:trim-left"
    assert decoded.field_ord == 0
    assert decoded.overrides.trim_step_ms == 200


def test_apply_processing_command_uses_trim_override_without_mutating_config() -> None:
    config = AudioProcessingConfig(manual_trim_small_ms=500)
    state = AudioEditState("clip.mp3")
    decoded = decode_editor_command_payload(
        '{"command":"aqe:trim-left","fieldOrd":0,"overrides":{"trimStepMs":200}}'
    )

    updated = apply_processing_command(decoded, state, config)

    assert updated == AudioEditState("clip.mp3", left_trim_ms=200)
    assert config.manual_trim_small_ms == 500


def test_apply_processing_command_clamps_trim_override() -> None:
    config = AudioProcessingConfig(manual_trim_small_ms=500)
    state = AudioEditState("clip.mp3")
    low = decode_editor_command_payload(
        '{"command":"aqe:trim-left","fieldOrd":0,"overrides":{"trimStepMs":10}}'
    )
    high = decode_editor_command_payload(
        '{"command":"aqe:trim-right","fieldOrd":0,"overrides":{"trimStepMs":20000}}'
    )

    assert apply_processing_command(low, state, config) == AudioEditState(
        "clip.mp3", left_trim_ms=50
    )
    assert apply_processing_command(high, state, config) == AudioEditState(
        "clip.mp3", right_trim_ms=10000
    )


def test_apply_processing_command_handles_speed_and_feature_toggles() -> None:
    config = AudioProcessingConfig(speed_step=0.1)
    state = AudioEditState("clip.mp3")

    faster = apply_processing_command("aqe:faster", state, config)
    pauses_shortened = apply_processing_command("aqe:remove-pauses", state, config)

    assert faster == AudioEditState("clip.mp3", speed=1.1)
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
    config = AudioProcessingConfig(speed_step=0.05)
    state = AudioEditState("clip.mp3")
    decoded = decode_editor_command_payload(
        '{"command":"aqe:faster","fieldOrd":0,"overrides":{"speedStep":0.1}}'
    )

    updated = apply_processing_command(decoded, state, config)

    assert decoded.overrides.speed_step == 0.1
    assert updated == AudioEditState("clip.mp3", speed=1.1)
    assert config.speed_step == 0.05


def test_decode_processing_command_accepts_pause_aggressiveness_override() -> None:
    decoded = decode_editor_command_payload(
        '{"command":"aqe:remove-pauses","fieldOrd":0,"overrides":{"pauseAggressiveness":"aggressive"}}'
    )

    assert decoded.overrides.pause_aggressiveness == "aggressive"


def test_apply_processing_command_uses_pause_aggressiveness_without_mutating_config() -> None:
    config = AudioProcessingConfig(
        internal_pause_silence_threshold_db=-45,
        internal_pause_threshold_ms=300,
        internal_pause_target_gap_ms=100,
        pause_aggressiveness="normal",
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
    assert captured["config"].internal_pause_silence_threshold_db == -50
    assert captured["config"].internal_pause_threshold_ms == 180
    assert captured["config"].internal_pause_target_gap_ms == 60
    assert config.pause_aggressiveness == "normal"
    assert config.internal_pause_threshold_ms == 300


def test_processing_config_for_command_returns_render_config_with_local_overrides() -> None:
    config = AudioProcessingConfig(
        volume_step_db=3,
        speed_step=0.05,
        pause_aggressiveness="normal",
        internal_pause_silence_threshold_db=-45,
        internal_pause_threshold_ms=300,
        internal_pause_target_gap_ms=100,
    )
    decoded = decode_editor_command_payload(
        '{"command":"aqe:remove-pauses","fieldOrd":0,'
        '"overrides":{"pauseAggressiveness":"aggressive","volumeStepDb":6,"speedStep":0.1}}'
    )

    effective = processing_config_for_command(decoded, config)

    assert effective.volume_step_db == 6
    assert effective.speed_step == 0.1
    assert effective.pause_aggressiveness == "aggressive"
    assert effective.internal_pause_silence_threshold_db == -50
    assert effective.internal_pause_threshold_ms == 180
    assert effective.internal_pause_target_gap_ms == 60
    assert config.pause_aggressiveness == "normal"


def test_apply_processing_command_returns_none_for_non_processing_command() -> None:
    config = AudioProcessingConfig()
    state = AudioEditState("clip.mp3")

    assert apply_processing_command("aqe:play", state, config) is None


def test_play_graph_cursor_and_play_ended_are_not_processing_commands() -> None:
    assert {
        "aqe:play",
        "aqe:play-ended",
        "aqe:show-file",
        "aqe:analyze",
        "aqe:analyze-field",
        "aqe:set-cursor",
        "aqe:denoise-standard",
        "aqe:rnnoise",
        "aqe:settings",
        "aqe:redo",
        "aqe:trim-silence",
    }.isdisjoint(PROCESSING_COMMANDS)

    assert "aqe:denoise-standard" in BRIDGE_COMMANDS
    assert "aqe:rnnoise" in BRIDGE_COMMANDS
    assert "aqe:settings" in BRIDGE_COMMANDS
    assert "aqe:redo" in BRIDGE_COMMANDS
    assert "aqe:analyze-field" in BRIDGE_COMMANDS
    assert ("aqe:" + "si" + "don") not in BRIDGE_COMMANDS


def test_untrim_commands_are_not_registered() -> None:
    assert "aqe:untrim-left" not in BRIDGE_COMMANDS
    assert "aqe:untrim-right" not in BRIDGE_COMMANDS
    assert "aqe:untrim-left" not in PROCESSING_COMMANDS
    assert "aqe:untrim-right" not in PROCESSING_COMMANDS
