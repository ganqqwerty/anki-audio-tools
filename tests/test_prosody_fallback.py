"""Tests for the ffmpeg/PCM prosody fallback analyzer."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.prosody_fallback import (
    PITCH_CEILING_HZ,
    PITCH_FLOOR_HZ,
    _decode_pcm,
    analyze_with_fallback,
)

FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
FFMPEG_SKIP_REASON = "ffmpeg and ffprobe are required for fallback prosody tests"


def test_decode_pcm_forwards_window_visibility_kwargs(monkeypatch, tmp_path: Path) -> None:
    run_kwargs: list[dict[str, object]] = []
    monkeypatch.setattr("anki_audio_quick_editor.prosody_fallback.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr(
        "anki_audio_quick_editor.prosody_fallback._external_command_run_kwargs",
        lambda: {"creationflags": 0x08000000},
    )

    def fake_run(
        _cmd: list[str],
        *,
        capture_output: bool,
        check: bool,
        **kwargs: object,
    ) -> SimpleNamespace:
        assert capture_output is True
        assert check is False
        run_kwargs.append(kwargs)
        return SimpleNamespace(returncode=0, stdout=b"\x01\x00\xff\xff", stderr=b"")

    monkeypatch.setattr("anki_audio_quick_editor.prosody_fallback.subprocess.run", fake_run)

    assert _decode_pcm(tmp_path / "clip.wav", AudioProcessingConfig()) == [1.0, -1.0]
    assert run_kwargs == [{"creationflags": 0x08000000}]


@pytest.mark.skipif(not FFMPEG_AVAILABLE, reason=FFMPEG_SKIP_REASON)
def test_fallback_detects_pitch_on_generated_tone(tmp_path: Path) -> None:
    source = tmp_path / "tone.wav"
    _generate_tone(source, frequency_hz=440, duration_s=0.6)

    track = analyze_with_fallback(source, AudioProcessingConfig())

    voiced = [point.pitch_hz for point in track.points if point.pitch_hz is not None]
    assert track.analyzer_name == "ffmpeg-pcm"
    assert voiced
    assert abs(sum(voiced) / len(voiced) - 440) < 20
    assert all(0.0 <= point.intensity_norm <= 1.0 for point in track.points)


@pytest.mark.skipif(not FFMPEG_AVAILABLE, reason=FFMPEG_SKIP_REASON)
def test_fallback_leaves_pitch_blank_for_silence(tmp_path: Path) -> None:
    source = tmp_path / "silence.wav"
    _run_ffmpeg("-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono:d=0.4", str(source))

    track = analyze_with_fallback(source, AudioProcessingConfig())

    assert track.points
    assert all(point.pitch_hz is None and not point.voiced for point in track.points)
    assert all(0.0 <= point.intensity_norm <= 1.0 for point in track.points)


@pytest.mark.skipif(not FFMPEG_AVAILABLE, reason=FFMPEG_SKIP_REASON)
@pytest.mark.parametrize("frequency_hz", [120, 220, 440, 480])
def test_fallback_tracks_flat_tones_without_octave_errors(
    tmp_path: Path,
    frequency_hz: int,
) -> None:
    source = tmp_path / f"flat_{frequency_hz}.wav"
    _generate_tone(source, frequency_hz=frequency_hz, duration_s=0.7)

    track = analyze_with_fallback(source, AudioProcessingConfig())

    voiced = [point.pitch_hz for point in track.points if point.pitch_hz is not None]
    assert voiced
    mean_pitch = sum(voiced) / len(voiced)
    assert abs(mean_pitch - frequency_hz) < max(12, frequency_hz * 0.08)
    assert max(voiced) / min(voiced) < 1.15


@pytest.mark.skipif(not FFMPEG_AVAILABLE, reason=FFMPEG_SKIP_REASON)
@pytest.mark.parametrize("frequency_hz", [75, 500])
def test_fallback_tracks_pitch_near_supported_boundaries(
    tmp_path: Path,
    frequency_hz: int,
) -> None:
    source = tmp_path / f"boundary_{frequency_hz}.wav"
    _generate_tone(source, frequency_hz=frequency_hz, duration_s=0.7)

    track = analyze_with_fallback(source, AudioProcessingConfig())

    voiced = [point.pitch_hz for point in track.points if point.pitch_hz is not None]
    assert voiced
    assert abs(sum(voiced) / len(voiced) - frequency_hz) < 25


@pytest.mark.skipif(not FFMPEG_AVAILABLE, reason=FFMPEG_SKIP_REASON)
@pytest.mark.parametrize("frequency_hz", [74, 501])
def test_fallback_does_not_report_pitch_outside_supported_bounds(
    tmp_path: Path,
    frequency_hz: int,
) -> None:
    source = tmp_path / f"outside_{frequency_hz}.wav"
    _generate_tone(source, frequency_hz=frequency_hz, duration_s=0.7)

    track = analyze_with_fallback(source, AudioProcessingConfig())

    voiced = [point.pitch_hz for point in track.points if point.pitch_hz is not None]
    assert all(PITCH_FLOOR_HZ <= pitch_hz <= PITCH_CEILING_HZ for pitch_hz in voiced)


@pytest.mark.skipif(not FFMPEG_AVAILABLE, reason=FFMPEG_SKIP_REASON)
def test_fallback_preserves_pitch_gaps_for_internal_silence(tmp_path: Path) -> None:
    source = tmp_path / "tone_silence_tone.wav"
    _generate_tone_silence_tone(source)

    track = analyze_with_fallback(source, AudioProcessingConfig())

    assert any(point.voiced for point in track.points if point.time_ms < 300)
    assert all(not point.voiced for point in track.points if 430 <= point.time_ms <= 610)
    assert any(point.voiced for point in track.points if point.time_ms > 760)
    assert _voiced_segment_count(track.points) >= 2


@pytest.mark.skipif(not FFMPEG_AVAILABLE, reason=FFMPEG_SKIP_REASON)
def test_fallback_intensity_changes_without_pitch_drift(tmp_path: Path) -> None:
    source = tmp_path / "amplitude_steps.wav"
    _run_ffmpeg(
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=220:duration=0.4,volume=0.15",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=220:duration=0.4,volume=1.0",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=220:duration=0.4,volume=0.35",
        "-filter_complex",
        "[0:a][1:a][2:a]concat=n=3:v=0:a=1[out]",
        "-map",
        "[out]",
        str(source),
    )

    track = analyze_with_fallback(source, AudioProcessingConfig())

    quiet = _voiced_points_between(track.points, 100, 300)
    loud = _voiced_points_between(track.points, 500, 700)
    assert quiet
    assert loud
    assert abs(_mean_pitch(quiet) - _mean_pitch(loud)) < 12
    assert _mean_intensity(loud) > _mean_intensity(quiet) + 0.25


@pytest.mark.skipif(not FFMPEG_AVAILABLE, reason=FFMPEG_SKIP_REASON)
@pytest.mark.parametrize("duration_s", [0.08, 0.15, 0.3])
def test_fallback_short_clips_produce_finite_bounded_points(
    tmp_path: Path,
    duration_s: float,
) -> None:
    source = tmp_path / f"short_{duration_s}.wav"
    _generate_tone(source, frequency_hz=220, duration_s=duration_s)

    track = analyze_with_fallback(source, AudioProcessingConfig())

    assert track.points
    assert track.duration_ms > 0
    assert [point.time_ms for point in track.points] == sorted(point.time_ms for point in track.points)
    assert all(0 <= point.time_ms <= track.duration_ms for point in track.points)
    assert all(0.0 <= point.intensity_norm <= 1.0 for point in track.points)
    assert all(
        point.pitch_hz is None or PITCH_FLOOR_HZ <= point.pitch_hz <= PITCH_CEILING_HZ
        for point in track.points
    )


def _generate_tone(path: Path, *, frequency_hz: int, duration_s: float) -> None:
    _run_ffmpeg("-f", "lavfi", "-i", f"sine=frequency={frequency_hz}:duration={duration_s}", str(path))


def _generate_tone_silence_tone(path: Path) -> None:
    _run_ffmpeg(
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=220:duration=0.4",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=44100:cl=mono:d=0.45",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=330:duration=0.4",
        "-filter_complex",
        "[0:a][1:a][2:a]concat=n=3:v=0:a=1[out]",
        "-map",
        "[out]",
        str(path),
    )


def _run_ffmpeg(*args: str) -> None:
    assert shutil.which("ffmpeg") is not None
    subprocess.run(
        ["ffmpeg", "-y", *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _voiced_segment_count(points) -> int:
    segments = 0
    in_segment = False
    for point in points:
        if point.voiced and not in_segment:
            segments += 1
            in_segment = True
        elif not point.voiced:
            in_segment = False
    return segments


def _voiced_points_between(points, start_ms: int, end_ms: int):
    return [point for point in points if point.voiced and start_ms <= point.time_ms <= end_ms]


def _mean_pitch(points) -> float:
    pitches = [point.pitch_hz for point in points if point.pitch_hz is not None]
    return sum(pitches) / len(pitches)


def _mean_intensity(points) -> float:
    return sum(point.intensity_norm for point in points) / len(points)
