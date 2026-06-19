from __future__ import annotations

import math
import subprocess
import wave
from array import array
from pathlib import Path

import pytest

from anki_audio_quick_editor.audio_pitch_hum import (
    HUM_SAMPLE_RATE,
    render_pitch_hum_audio,
    render_pitch_tier_hum_audio,
)
from anki_audio_quick_editor.audio_processor import find_ffmpeg, probe_duration_ms
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from tests.audio_fixtures import FFMPEG_AVAILABLE, FFMPEG_SKIP_REASON


def _region(samples: list[int], start_s: float, end_s: float, sample_rate: int) -> list[int]:
    start = round(start_s * sample_rate)
    end = round(end_s * sample_rate)
    return samples[start:end]


def _region_rms(samples: list[int], start_s: float, end_s: float, sample_rate: int) -> float:
    region = _region(samples, start_s, end_s, sample_rate)
    if not region:
        return 0.0
    return math.sqrt(sum(sample * sample for sample in region) / len(region))


def _decode_mono_pcm(path: Path) -> list[int]:
    ffmpeg_config = AudioProcessingConfig(ffmpeg_path=find_ffmpeg(AudioProcessingConfig().ffmpeg_path))
    result = subprocess.run(
        [
            str(ffmpeg_config.ffmpeg_path),
            "-i",
            str(path),
            "-f",
            "s16le",
            "-acodec",
            "pcm_s16le",
            "-ac",
            "1",
            "-ar",
            str(HUM_SAMPLE_RATE),
            "-",
        ],
        check=True,
        capture_output=True,
    )
    samples = array("h")
    samples.frombytes(result.stdout)
    return list(samples)


def _write_voiced_silence_voiced_wav(path: Path) -> None:
    samples = array("h")
    segments = ((0.35, 220.0), (0.35, None), (0.35, 330.0))
    for duration_s, pitch_hz in segments:
        segment_samples = round(duration_s * HUM_SAMPLE_RATE)
        for sample_index in range(segment_samples):
            if pitch_hz is None:
                samples.append(0)
                continue
            phase = 2 * math.pi * pitch_hz * sample_index / HUM_SAMPLE_RATE
            samples.append(round(math.sin(phase) * 0.35 * 32767))

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(HUM_SAMPLE_RATE)
        wav_file.writeframes(samples.tobytes())


def _write_rich_pitch_wav(path: Path) -> None:
    samples = array("h")
    weights = ((1, 0.38), (2, 0.33), (3, 0.28), (4, 0.24), (5, 0.18))
    weight_sum = sum(weight for _harmonic, weight in weights)
    duration_s = 0.9
    for sample_index in range(round(duration_s * HUM_SAMPLE_RATE)):
        sample = sum(
            weight
            * math.sin(2 * math.pi * 220.0 * harmonic * sample_index / HUM_SAMPLE_RATE)
            for harmonic, weight in weights
        )
        samples.append(round(sample / weight_sum * 0.65 * 32767))

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(HUM_SAMPLE_RATE)
        wav_file.writeframes(samples.tobytes())


def _upper_harmonic_ratio(samples: list[int], start_s: float, end_s: float) -> float:
    region = _region(samples, start_s, end_s, HUM_SAMPLE_RATE)

    def goertzel_power(signal: list[int], frequency_hz: float) -> float:
        if not signal:
            return 0.0
        coefficient = 2 * math.cos(2 * math.pi * frequency_hz / HUM_SAMPLE_RATE)
        previous = 0.0
        previous2 = 0.0
        for value in signal:
            current = float(value) + coefficient * previous - previous2
            previous2 = previous
            previous = current
        return previous2 * previous2 + previous * previous - coefficient * previous * previous2

    fundamental = max(goertzel_power(region, 220.0), 1.0)
    upper = sum(goertzel_power(region, frequency) for frequency in (440.0, 660.0, 880.0))
    return upper / fundamental


@pytest.mark.allow_managed_runtime
def test_pitch_hum_algorithms_keep_unvoiced_regions_silent(tmp_path: Path) -> None:
    assert FFMPEG_AVAILABLE, FFMPEG_SKIP_REASON
    __import__("parselmouth")

    source = tmp_path / "voiced-silence-voiced.wav"
    direct = tmp_path / "direct-hum.mp3"
    pitch_tier = tmp_path / "pitch-tier-hum.mp3"
    _write_voiced_silence_voiced_wav(source)

    render_pitch_hum_audio(source, AudioProcessingConfig(output_format="mp3"), output_path=direct)
    render_pitch_tier_hum_audio(source, AudioProcessingConfig(output_format="mp3"), output_path=pitch_tier)

    for output in (direct, pitch_tier):
        samples = _decode_mono_pcm(output)
        voiced_rms = min(
            _region_rms(samples, 0.12, 0.28, HUM_SAMPLE_RATE),
            _region_rms(samples, 0.82, 0.98, HUM_SAMPLE_RATE),
        )
        gap_rms = _region_rms(samples, 0.47, 0.63, HUM_SAMPLE_RATE)

        assert 900 <= probe_duration_ms(output, AudioProcessingConfig()) <= 1250
        assert voiced_rms > 200
        assert gap_rms < voiced_rms * 0.25


@pytest.mark.allow_managed_runtime
def test_pitch_tier_hum_removes_original_harmonic_timbre(tmp_path: Path) -> None:
    assert FFMPEG_AVAILABLE, FFMPEG_SKIP_REASON
    __import__("parselmouth")

    source = tmp_path / "rich-harmonic-source.wav"
    pitch_tier = tmp_path / "pitch-tier-hum.mp3"
    _write_rich_pitch_wav(source)

    render_pitch_tier_hum_audio(source, AudioProcessingConfig(output_format="mp3"), output_path=pitch_tier)

    source_ratio = _upper_harmonic_ratio(_decode_mono_pcm(source), 0.12, 0.72)
    pitch_tier_ratio = _upper_harmonic_ratio(_decode_mono_pcm(pitch_tier), 0.12, 0.72)

    assert source_ratio > 0.9
    assert pitch_tier_ratio < source_ratio * 0.35
