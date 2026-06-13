from __future__ import annotations

from types import SimpleNamespace

import pytest

from anki_audio_quick_editor.audio_size_reduction import (
    normalize_size_reduction_mode,
    size_reduction_plan_from_metadata,
)
from anki_audio_quick_editor.errors import AudioAlreadyCompactError


def test_size_reduction_plan_uses_normal_mode_source_aware_caps() -> None:
    metadata = SimpleNamespace(sample_rate=44100, channels=2, bit_rate=128_000)

    plan = size_reduction_plan_from_metadata(metadata, "normal")

    assert plan.target_bitrate_kbps == 64
    assert plan.target_sample_rate_hz == 32000
    assert plan.target_channels == 1
    assert plan.codec_args == (
        "-codec:a",
        "libmp3lame",
        "-b:a",
        "64k",
        "-ar",
        "32000",
        "-ac",
        "1",
    )


def test_size_reduction_plan_caps_unknown_bitrate_but_does_not_increase_known_params() -> None:
    metadata = SimpleNamespace(sample_rate=44100, channels=2, bit_rate=None)

    plan = size_reduction_plan_from_metadata(metadata, "aggressive")

    assert plan.target_bitrate_kbps == 40
    assert plan.target_sample_rate_hz == 22050
    assert plan.target_channels == 1
    assert plan.codec_args == (
        "-codec:a",
        "libmp3lame",
        "-b:a",
        "40k",
        "-ar",
        "22050",
        "-ac",
        "1",
    )


def test_size_reduction_plan_skips_when_known_params_are_already_compact() -> None:
    metadata = SimpleNamespace(sample_rate=16000, channels=1, bit_rate=24_000)

    with pytest.raises(AudioAlreadyCompactError, match="already compact"):
        size_reduction_plan_from_metadata(metadata, "aggressive")


def test_size_reduction_plan_uses_explicit_advanced_caps() -> None:
    metadata = SimpleNamespace(sample_rate=48000, channels=2, bit_rate=128_000)

    plan = size_reduction_plan_from_metadata(
        metadata,
        "normal",
        bitrate_kbps=80,
        sample_rate_hz=44100,
        channels=2,
    )

    assert plan.target_bitrate_kbps == 80
    assert plan.target_sample_rate_hz == 44100
    assert plan.target_channels == 2
    assert plan.codec_args == (
        "-codec:a",
        "libmp3lame",
        "-b:a",
        "80k",
        "-ar",
        "44100",
        "-ac",
        "2",
    )


def test_size_reduction_plan_never_increases_known_params_from_advanced_caps() -> None:
    metadata = SimpleNamespace(sample_rate=16000, channels=1, bit_rate=64_000)

    with pytest.raises(AudioAlreadyCompactError, match="already compact"):
        size_reduction_plan_from_metadata(
            metadata,
            "normal",
            bitrate_kbps=96,
            sample_rate_hz=44100,
            channels=2,
        )


def test_normalize_size_reduction_mode_defaults_invalid_values_to_normal() -> None:
    assert normalize_size_reduction_mode(" gentle ") == "gentle"
    assert normalize_size_reduction_mode("unknown") == "normal"
