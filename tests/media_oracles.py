"""Independent decoded-media assertions for real-binary tests."""

from __future__ import annotations

import json
import math
import subprocess
from array import array
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AudioProbe:
    codec: str
    channels: int
    sample_rate: int
    duration_s: float


def probe_audio(ffprobe: Path, media_path: Path) -> AudioProbe:
    result = subprocess.run(
        [
            str(ffprobe),
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=codec_name,channels,sample_rate:format=duration",
            "-of",
            "json",
            str(media_path),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    payload = json.loads(result.stdout)
    stream = payload["streams"][0]
    return AudioProbe(
        codec=str(stream["codec_name"]),
        channels=int(stream["channels"]),
        sample_rate=int(stream["sample_rate"]),
        duration_s=float(payload["format"]["duration"]),
    )


def decode_mono_f32(
    ffmpeg: Path,
    media_path: Path,
    *,
    sample_rate: int = 48_000,
) -> array[float]:
    result = subprocess.run(
        [
            str(ffmpeg),
            "-v",
            "error",
            "-i",
            str(media_path),
            "-map",
            "0:a:0",
            "-ac",
            "1",
            "-ar",
            str(sample_rate),
            "-f",
            "f32le",
            "pipe:1",
        ],
        check=True,
        capture_output=True,
    )
    samples = array("f")
    samples.frombytes(result.stdout)
    if not samples:
        raise AssertionError(f"decoded audio is empty: {media_path}")
    return samples


def rms(samples: array[float]) -> float:
    if not samples:
        raise AssertionError("cannot measure an empty PCM sequence")
    return math.sqrt(math.fsum(sample * sample for sample in samples) / len(samples))


def window_rms(
    samples: array[float],
    *,
    start_s: float,
    end_s: float,
    sample_rate: int = 48_000,
) -> float:
    start = round(start_s * sample_rate)
    end = round(end_s * sample_rate)
    if start < 0 or end <= start or end > len(samples):
        raise AssertionError(
            f"invalid PCM window {start_s:.3f}-{end_s:.3f}s for {len(samples)} samples"
        )
    return rms(array("f", samples[start:end]))


def db_ratio(reference: float, measured: float) -> float:
    if reference <= 0 or measured <= 0:
        raise AssertionError("dB comparison requires positive RMS values")
    return 20 * math.log10(measured / reference)


def difference_rms(
    reference: array[float],
    measured: array[float],
    *,
    start_s: float,
    end_s: float,
    sample_rate: int = 48_000,
) -> float:
    start = round(start_s * sample_rate)
    end = round(end_s * sample_rate)
    if end > min(len(reference), len(measured)) or end <= start:
        raise AssertionError("PCM difference window is outside one of the signals")
    differences = array(
        "f",
        (measured[index] - reference[index] for index in range(start, end)),
    )
    return rms(differences)
