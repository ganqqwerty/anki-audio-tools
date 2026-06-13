"""Shared test fixtures for pitch hum synthesis tests."""

from __future__ import annotations

import math
import wave
from array import array
from pathlib import Path

from anki_audio_quick_editor.audio_output_policy import AudioSourceMetadata
from anki_audio_quick_editor.audio_pitch_hum import HUM_SAMPLE_RATE


def wav_source_metadata(
    source_path: Path,
    *,
    visible_format: str = "wav",
    codec_name: str = "pcm_s16le",
    sample_rate: int = HUM_SAMPLE_RATE,
    channels: int = 1,
    bit_rate: int | None = HUM_SAMPLE_RATE * 16,
    bits_per_raw_sample: int | None = 16,
    sample_fmt: str | None = "s16",
) -> AudioSourceMetadata:
    return AudioSourceMetadata(
        path=source_path,
        visible_format=visible_format,
        codec_name=codec_name,
        sample_rate=sample_rate,
        channels=channels,
        bit_rate=bit_rate,
        bits_per_raw_sample=bits_per_raw_sample,
        sample_fmt=sample_fmt,
    )


def write_voiced_silence_voiced_wav(path: Path) -> None:
    samples = array("h")
    for duration_s, pitch_hz in ((0.35, 220.0), (0.35, None), (0.35, 330.0)):
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


def read_wav_pcm(path: Path) -> tuple[int, array[int]]:
    with wave.open(str(path), "rb") as wav_file:
        sample_rate = wav_file.getframerate()
        samples = array("h")
        samples.frombytes(wav_file.readframes(wav_file.getnframes()))
    return sample_rate, samples


def region_rms(samples: array[int], sample_rate: int, start_s: float, end_s: float) -> float:
    start = round(start_s * sample_rate)
    end = round(end_s * sample_rate)
    region = samples[start:end]
    if not region:
        return 0.0
    return math.sqrt(sum(sample * sample for sample in region) / len(region))
