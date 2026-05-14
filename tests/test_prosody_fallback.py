"""Tests for the ffmpeg/PCM prosody fallback analyzer."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.prosody_fallback import analyze_with_fallback


@pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="ffmpeg and ffprobe are required for fallback prosody tests",
)
def test_fallback_detects_pitch_on_generated_tone(tmp_path: Path) -> None:
    source = tmp_path / "tone.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=0.6", str(source)],
        check=True,
        capture_output=True,
        text=True,
    )

    track = analyze_with_fallback(source, AudioProcessingConfig())

    voiced = [point.pitch_hz for point in track.points if point.pitch_hz is not None]
    assert track.analyzer_name == "ffmpeg-pcm"
    assert voiced
    assert abs(sum(voiced) / len(voiced) - 440) < 20
    assert all(0.0 <= point.intensity_norm <= 1.0 for point in track.points)


@pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="ffmpeg and ffprobe are required for fallback prosody tests",
)
def test_fallback_leaves_pitch_blank_for_silence(tmp_path: Path) -> None:
    source = tmp_path / "silence.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono:d=0.4", str(source)],
        check=True,
        capture_output=True,
        text=True,
    )

    track = analyze_with_fallback(source, AudioProcessingConfig())

    assert track.points
    assert all(point.pitch_hz is None and not point.voiced for point in track.points)
    assert all(0.0 <= point.intensity_norm <= 1.0 for point in track.points)
