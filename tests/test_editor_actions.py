"""Tests for import-safe editor action transitions."""

from __future__ import annotations

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
    operation_for_command,
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
