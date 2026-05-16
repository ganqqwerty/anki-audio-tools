"""Tests for ffmpeg command construction helpers."""

from __future__ import annotations

import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import pytest

from anki_audio_quick_editor.audio_processor import (
    build_audio_filters,
    build_playback_segment_filters,
    format_ffmpeg_command,
    make_output_filename,
    make_playback_segment_filename,
    probe_duration_ms,
    render_audio,
    render_playback_segment,
    temp_final_path,
)
from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.errors import AudioProcessingError


def test_build_audio_filters_includes_crop_speed_and_silence_steps() -> None:
    config = AudioProcessingConfig()
    state = AudioEditState(
        "clip.mp3",
        left_trim_ms=200,
        right_trim_ms=100,
        speed=1.15,
        volume_db=3.0,
        edge_trim_enabled=True,
        remove_internal_pauses_enabled=True,
    )

    filters = build_audio_filters(3000, state, config)
    threshold = f"{config.edge_silence_threshold_db}dB"

    assert "atrim=start=0.200:end=2.900" in filters
    assert "silenceremove=start_periods=1" in filters
    assert "stop_periods=-1" in filters
    assert f"start_threshold={threshold}" in filters
    assert f"stop_threshold={threshold}" in filters
    assert "stop_silence=0.100" in filters
    assert "volume=3.00dB" in filters
    assert "atempo=1.150" in filters
    assert filters.index("stop_silence=0.100") < filters.index("volume=3.00dB")
    assert filters.index("volume=3.00dB") < filters.index("atempo=1.150")


def test_build_audio_filters_omits_volume_filter_when_unchanged() -> None:
    filters = build_audio_filters(3000, AudioEditState("clip.mp3"), AudioProcessingConfig())

    assert "volume=" not in filters


def test_build_playback_segment_filters_starts_at_cursor_and_resets_timestamps() -> None:
    filters = build_playback_segment_filters(700)

    assert filters == "atrim=start=0.700,asetpts=PTS-STARTPTS"


def test_build_playback_segment_filters_clamps_negative_cursor_to_zero() -> None:
    filters = build_playback_segment_filters(-200)

    assert filters == "atrim=start=0.000,asetpts=PTS-STARTPTS"


def test_make_output_filename_is_mp3_and_timestamped() -> None:
    filename = make_output_filename("my sentence.wav", datetime(2026, 5, 14, 9, 8, 7), "abc12345")

    assert filename == "my_sentence__aqe_20260514_090807_000000_abc12345.mp3"


def test_make_output_filename_sanitizes_and_bounds_problematic_names() -> None:
    filename = make_output_filename(
        "../??? " + ("very long " * 30) + ".wav",
        datetime(2026, 5, 14, 9, 8, 7, 123456),
        "deadbeef",
    )

    assert filename.endswith("__aqe_20260514_090807_123456_deadbeef.mp3")
    assert "/" not in filename
    assert "?" not in filename
    assert len(filename) <= 120


def test_make_output_filename_uses_audio_for_empty_sanitized_stem() -> None:
    filename = make_output_filename("短い.wav", datetime(2026, 5, 14), "12345678")

    assert filename == "audio__aqe_20260514_000000_000000_12345678.mp3"


def test_make_playback_segment_filename_is_debuggable_and_sanitized() -> None:
    filename = make_playback_segment_filename("../短い test.wav", 700, "abc12345")

    assert filename == "aqe_playback_test__from_700ms_abc12345.mp3"


def test_temp_final_path_preserves_basename_only() -> None:
    path = temp_final_path("../nested/clip.mp3")

    assert path.name == "clip.mp3"
    assert path.parent.name.startswith("aqe_final_")


def test_render_playback_segment_rejects_cursor_at_end(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda *_args: Path("/tmp/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: 1000)

    with pytest.raises(AudioProcessingError, match="Cursor is at the end of the audio."):
        render_playback_segment(
            tmp_path / "source.wav",
            1000,
            AudioProcessingConfig(),
        )


@pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="ffmpeg and ffprobe are required for audio rendering smoke tests",
)
def test_render_audio_smoke_with_path_spaces_and_non_ascii(tmp_path: Path) -> None:
    source_dir = tmp_path / "media with spaces"
    source_dir.mkdir()
    source = source_dir / "短い clip.wav"
    output = tmp_path / "edited preview.mp3"

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=1",
            str(source),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    result = render_audio(
        source,
        AudioEditState("短い clip.wav", left_trim_ms=100, speed=1.05),
        AudioProcessingConfig(),
        output_path=output,
    )

    assert result.output_path == output
    assert " -y -i " in format_ffmpeg_command(result.command)
    assert output.is_file()
    assert 700 <= probe_duration_ms(output, AudioProcessingConfig()) <= 1000


@pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="ffmpeg and ffprobe are required for audio rendering smoke tests",
)
def test_render_playback_segment_from_70_percent_is_shorter(tmp_path: Path) -> None:
    source = tmp_path / "cursor source.wav"
    output = tmp_path / "cursor segment.mp3"

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=1",
            str(source),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    result = render_playback_segment(
        source,
        700,
        AudioProcessingConfig(),
        output_path=output,
    )

    assert result.output_path == output
    assert "atrim=start=0.700" in format_ffmpeg_command(result.command)
    assert output.is_file()
    assert 220 <= probe_duration_ms(output, AudioProcessingConfig()) <= 380
