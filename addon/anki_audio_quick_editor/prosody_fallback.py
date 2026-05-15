"""ffmpeg/PCM fallback prosody analyzer."""

from __future__ import annotations

import math
import subprocess
import sys
from array import array
from pathlib import Path

from .audio_processor import find_ffmpeg, probe_duration_ms
from .audio_state import AudioProcessingConfig
from .errors import AudioProcessingError
from .prosody_types import ProsodyPoint, ProsodyTrack, build_prosody_track

SAMPLE_RATE = 16_000
FRAME_MS = 40
HOP_MS = 10
PITCH_FLOOR_HZ = 75
PITCH_CEILING_HZ = 500
MIN_RMS = 50.0
MIN_CORRELATION = 0.55


def analyze_with_fallback(source_path: Path, config: AudioProcessingConfig) -> ProsodyTrack:
    """Analyze pitch and intensity using ffmpeg-decoded mono PCM."""
    samples = _decode_pcm(source_path, config)
    duration_ms = probe_duration_ms(source_path, config)
    frame_size = SAMPLE_RATE * FRAME_MS // 1000
    hop_size = SAMPLE_RATE * HOP_MS // 1000
    points: list[ProsodyPoint] = []
    if not samples:
        return build_prosody_track(
            duration_ms=duration_ms,
            points=[],
            source_filename=source_path.name,
            analyzer_name="ffmpeg-pcm",
        )
    for start in range(0, len(samples), hop_size):
        frame = samples[start : start + frame_size]
        if len(frame) < frame_size:
            frame = frame + [0.0] * (frame_size - len(frame))
        rms = _rms(frame)
        pitch_hz = _estimate_pitch(frame, rms)
        time_ms = round(start * 1000 / SAMPLE_RATE)
        points.append(
            ProsodyPoint(
                time_ms=time_ms,
                pitch_hz=pitch_hz,
                intensity_db=_rms_to_db(rms),
                intensity_norm=0.0,
                voiced=pitch_hz is not None,
            )
        )
        if time_ms >= duration_ms:
            break
    return build_prosody_track(
        duration_ms=duration_ms,
        points=points,
        source_filename=source_path.name,
        analyzer_name="ffmpeg-pcm",
    )


def _decode_pcm(source_path: Path, config: AudioProcessingConfig) -> list[float]:
    ffmpeg_path = find_ffmpeg(config.ffmpeg_path)
    command = [
        str(ffmpeg_path),
        "-v",
        "error",
        "-i",
        str(source_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(SAMPLE_RATE),
        "-f",
        "s16le",
        "pipe:1",
    ]
    result = subprocess.run(command, capture_output=True, check=False)  # nosec B603
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise AudioProcessingError(message or "Could not decode audio for visualization.")
    pcm = array("h")
    pcm.frombytes(result.stdout)
    if sys.byteorder != "little":
        pcm.byteswap()
    return [float(sample) for sample in pcm]


def _rms(frame: list[float]) -> float:
    if not frame:
        return 0.0
    return math.sqrt(sum(sample * sample for sample in frame) / len(frame))


def _rms_to_db(rms: float) -> float:
    if rms <= 0:
        return -120.0
    return max(-120.0, 20 * math.log10(rms / 32768.0))


def _estimate_pitch(frame: list[float], rms: float) -> float | None:
    if rms < MIN_RMS:
        return None
    centered = _center(frame)
    min_lag = SAMPLE_RATE // PITCH_CEILING_HZ
    max_lag = SAMPLE_RATE // PITCH_FLOOR_HZ
    lag_scores = [
        (lag, _correlation(centered, lag))
        for lag in range(min_lag, min(max_lag, len(centered) - 1) + 1)
    ]
    best_score = max((score for _lag, score in lag_scores), default=0.0)
    if best_score < MIN_CORRELATION:
        return None
    best_lag = _first_confident_peak(lag_scores, best_score)
    return SAMPLE_RATE / best_lag


def _center(frame: list[float]) -> list[float]:
    mean = sum(frame) / len(frame) if frame else 0.0
    return [sample - mean for sample in frame]


def _correlation(frame: list[float], lag: int) -> float:
    count = len(frame) - lag
    if count <= 0:
        return 0.0
    left = frame[:count]
    right = frame[lag : lag + count]
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_energy = sum(a * a for a in left)
    right_energy = sum(b * b for b in right)
    denominator = math.sqrt(left_energy * right_energy)
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def _first_confident_peak(lag_scores: list[tuple[int, float]], best_score: float) -> int:
    minimum = max(MIN_CORRELATION, best_score * 0.9)
    if len(lag_scores) == 1:
        return lag_scores[0][0]
    first_lag, first_score = lag_scores[0]
    if first_score >= minimum and first_score >= lag_scores[1][1]:
        return first_lag
    for index in range(1, len(lag_scores) - 1):
        lag, score = lag_scores[index]
        previous_score = lag_scores[index - 1][1]
        next_score = lag_scores[index + 1][1]
        if score >= minimum and score >= previous_score and score >= next_score:
            return lag
    last_lag, last_score = lag_scores[-1]
    if last_score >= minimum and last_score >= lag_scores[-2][1]:
        return last_lag
    return next(lag for lag, score in lag_scores if score >= minimum)
