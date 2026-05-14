"""Tests for import-safe editor action transitions."""

from __future__ import annotations

from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.editor_actions import (
    BRIDGE_COMMANDS,
    PROCESSING_COMMANDS,
    apply_processing_command,
)


def test_processing_commands_are_registered_bridge_commands() -> None:
    assert set(PROCESSING_COMMANDS) < set(BRIDGE_COMMANDS)


def test_apply_processing_command_uses_configured_trim_step() -> None:
    config = AudioProcessingConfig(manual_trim_small_ms=250)
    state = AudioEditState("clip.mp3")

    updated = apply_processing_command("aqe:trim-left", state, config)

    assert updated == AudioEditState("clip.mp3", left_trim_ms=250)


def test_apply_processing_command_handles_speed_and_feature_toggles() -> None:
    config = AudioProcessingConfig(speed_step=0.1)
    state = AudioEditState("clip.mp3")

    faster = apply_processing_command("aqe:faster", state, config)
    edge_trimmed = apply_processing_command("aqe:trim-silence", state, config)

    assert faster == AudioEditState("clip.mp3", speed=1.1)
    assert edge_trimmed == AudioEditState("clip.mp3", edge_trim_enabled=True)


def test_apply_processing_command_returns_none_for_non_processing_command() -> None:
    config = AudioProcessingConfig()
    state = AudioEditState("clip.mp3")

    assert apply_processing_command("aqe:play", state, config) is None
