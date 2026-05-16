"""Tests for audio edit state transitions."""

from __future__ import annotations

import pytest

from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.errors import InvalidEditStateError


def test_trim_and_untrim_are_bounded_at_zero() -> None:
    state = AudioEditState("clip.mp3").trim_left(100).trim_right(200)

    assert state.left_trim_ms == 100
    assert state.right_trim_ms == 200
    assert state.untrim_left(500).left_trim_ms == 0
    assert state.untrim_right(500).right_trim_ms == 0


def test_speed_changes_are_clamped_to_configured_range() -> None:
    config = AudioProcessingConfig(speed_step=0.05, min_speed=0.75, max_speed=1.5)

    fast = AudioEditState("clip.mp3", speed=1.48).faster(config)
    slow = AudioEditState("clip.mp3", speed=0.77).slower(config)

    assert fast.speed == 1.5
    assert slow.speed == 0.75


def test_speed_changes_are_noops_once_at_clamp() -> None:
    config = AudioProcessingConfig(speed_step=0.05, min_speed=0.75, max_speed=1.5)

    assert AudioEditState("clip.mp3", speed=1.5).faster(config).speed == 1.5
    assert AudioEditState("clip.mp3", speed=0.75).slower(config).speed == 0.75


def test_volume_changes_are_clamped_to_configured_range() -> None:
    config = AudioProcessingConfig(volume_step_db=3.0, min_volume_db=-6.0, max_volume_db=6.0)

    louder = AudioEditState("clip.mp3", volume_db=4.5).volume_up(config)
    quieter = AudioEditState("clip.mp3", volume_db=-4.5).volume_down(config)

    assert louder.volume_db == 6.0
    assert quieter.volume_db == -6.0


def test_volume_changes_are_noops_once_at_clamp() -> None:
    config = AudioProcessingConfig(volume_step_db=3.0, min_volume_db=-6.0, max_volume_db=6.0)

    assert AudioEditState("clip.mp3", volume_db=6.0).volume_up(config).volume_db == 6.0
    assert AudioEditState("clip.mp3", volume_db=-6.0).volume_down(config).volume_db == -6.0


def test_validate_rejects_zero_length_crop() -> None:
    state = AudioEditState("clip.mp3", left_trim_ms=700, right_trim_ms=280)

    with pytest.raises(InvalidEditStateError):
        state.validate(duration_ms=1000, config=AudioProcessingConfig())


def test_validate_allows_trim_just_below_no_audio_boundary() -> None:
    state = AudioEditState("clip.mp3", left_trim_ms=700, right_trim_ms=249)

    state.validate(duration_ms=1000, config=AudioProcessingConfig())


def test_validate_rejects_trim_exactly_at_no_audio_boundary() -> None:
    state = AudioEditState("clip.mp3", left_trim_ms=700, right_trim_ms=250)

    with pytest.raises(InvalidEditStateError):
        state.validate(duration_ms=1000, config=AudioProcessingConfig())


def test_validate_rejects_invalid_speed() -> None:
    state = AudioEditState("clip.mp3", speed=2.0)

    with pytest.raises(InvalidEditStateError):
        state.validate(duration_ms=1000, config=AudioProcessingConfig())


def test_validate_rejects_invalid_volume() -> None:
    state = AudioEditState("clip.mp3", volume_db=30.0)

    with pytest.raises(InvalidEditStateError):
        state.validate(duration_ms=1000, config=AudioProcessingConfig())


def test_feature_toggles_only_enable_processing_steps() -> None:
    state = AudioEditState("clip.mp3").toggle_edge_trim().toggle_internal_pauses()

    assert state.edge_trim_enabled is True
    assert state.remove_internal_pauses_enabled is True


def test_processing_config_from_partial_config_uses_defaults() -> None:
    config = AudioProcessingConfig.from_config({"ffmpeg_path": "/opt/bin/ffmpeg"})

    assert config.manual_trim_small_ms == 100
    assert config.volume_step_db == 3.0
    assert config.min_volume_db == -24.0
    assert config.max_volume_db == 24.0
    assert config.edge_silence_threshold_db == -35
    assert config.internal_pause_silence_threshold_db == -45
    assert config.output_format == "mp3"
    assert config.ffmpeg_path == "/opt/bin/ffmpeg"
    assert config.deep_filter_path == ""
    assert config.deep_filter_post_filter is True
    assert config.show_ffmpeg_commands is False


def test_processing_config_reads_volume_settings() -> None:
    config = AudioProcessingConfig.from_config(
        {"volume_step_db": 1.5, "min_volume_db": -12, "max_volume_db": 9}
    )

    assert config.volume_step_db == 1.5
    assert config.min_volume_db == -12.0
    assert config.max_volume_db == 9.0


def test_processing_config_reads_show_ffmpeg_commands_flag() -> None:
    config = AudioProcessingConfig.from_config({"show_ffmpeg_commands": True})

    assert config.show_ffmpeg_commands is True


def test_processing_config_reads_internal_pause_silence_threshold() -> None:
    config = AudioProcessingConfig.from_config({"internal_pause_silence_threshold_db": -42})

    assert config.internal_pause_silence_threshold_db == -42


def test_processing_config_reads_deep_filter_settings() -> None:
    config = AudioProcessingConfig.from_config(
        {
            "deep_filter_path": "/opt/bin/deep-filter",
            "deep_filter_post_filter": False,
        }
    )

    assert config.deep_filter_path == "/opt/bin/deep-filter"
    assert config.deep_filter_post_filter is False
