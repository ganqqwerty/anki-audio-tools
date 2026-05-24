"""Shared generated language-contour fixtures for prosody tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest


@dataclass(frozen=True)
class ContourWindow:
    name: str
    start_ms: int
    end_ms: int
    expected_hz: float | None = None


@dataclass(frozen=True)
class VoicelessGap:
    start_ms: int
    end_ms: int


@dataclass(frozen=True)
class ContourSpec:
    name: str
    duration_ms: int
    f0_points: tuple[tuple[int, float], ...]
    windows: tuple[ContourWindow, ...]
    gaps: tuple[VoicelessGap, ...] = ()
    weak_windows: tuple[str, ...] = ()


PRAAT_SKIP_REASON = "praat-parselmouth is required for generated speech contour fixtures"
FFMPEG_SKIP_REASON = "ffmpeg and ffprobe are required for Praat analyzer duration probing"

LANGUAGE_CONTOUR_SPECS: dict[str, ContourSpec] = {
    "ja_heiban_4mora_particle_1_6s": ContourSpec(
        name="ja_heiban_4mora_particle_1_6s",
        duration_ms=1600,
        f0_points=((0, 150), (320, 225), (1280, 225), (1600, 220)),
        windows=(
            ContourWindow("early_low", 80, 240, 160),
            ContourWindow("mid_high", 520, 760, 225),
            ContourWindow("particle_high", 1340, 1540, 220),
        ),
    ),
    "ja_atamadaka_3mora_particle_1_4s": ContourSpec(
        name="ja_atamadaka_3mora_particle_1_4s",
        duration_ms=1400,
        f0_points=((0, 230), (260, 230), (470, 150), (1400, 145)),
        windows=(
            ContourWindow("initial_high", 80, 240, 230),
            ContourWindow("post_drop_low", 620, 920, 150),
            ContourWindow("particle_low", 1120, 1340, 145),
        ),
    ),
    "ja_nakadaka_4mora_1_5s": ContourSpec(
        name="ja_nakadaka_4mora_1_5s",
        duration_ms=1500,
        f0_points=((0, 150), (320, 225), (820, 225), (1040, 145), (1500, 145)),
        windows=(
            ContourWindow("early_low", 80, 250, 160),
            ContourWindow("pre_drop_high", 520, 820, 225),
            ContourWindow("post_drop_low", 1120, 1420, 145),
        ),
    ),
    "ja_odaka_3mora_particle_1_6s": ContourSpec(
        name="ja_odaka_3mora_particle_1_6s",
        duration_ms=1600,
        f0_points=((0, 150), (360, 225), (1160, 225), (1360, 145), (1600, 145)),
        windows=(
            ContourWindow("early_low", 80, 260, 155),
            ContourWindow("word_high", 680, 1080, 225),
            ContourWindow("particle_low", 1400, 1560, 145),
        ),
    ),
    "zh_tone1_high_level_0_9s": ContourSpec(
        name="zh_tone1_high_level_0_9s",
        duration_ms=900,
        f0_points=((0, 235), (900, 235)),
        windows=(
            ContourWindow("early", 120, 280, 235),
            ContourWindow("mid", 360, 540, 235),
            ContourWindow("late", 640, 820, 235),
        ),
    ),
    "zh_tone2_rising_0_9s": ContourSpec(
        name="zh_tone2_rising_0_9s",
        duration_ms=900,
        f0_points=((0, 155), (260, 170), (900, 250)),
        windows=(
            ContourWindow("early", 100, 280, 165),
            ContourWindow("late", 620, 840, 240),
        ),
    ),
    "zh_tone3_dipping_1_1s": ContourSpec(
        name="zh_tone3_dipping_1_1s",
        duration_ms=1100,
        f0_points=((0, 205), (500, 120), (1100, 210)),
        windows=(
            ContourWindow("early", 100, 280, 185),
            ContourWindow("trough", 430, 620, 125),
            ContourWindow("late", 820, 1040, 200),
        ),
    ),
    "zh_tone4_falling_0_8s": ContourSpec(
        name="zh_tone4_falling_0_8s",
        duration_ms=800,
        f0_points=((0, 255), (220, 230), (800, 125)),
        windows=(
            ContourWindow("early", 80, 220, 240),
            ContourWindow("late", 580, 760, 135),
        ),
    ),
    "zh_neutral_after_tone4_1_2s": ContourSpec(
        name="zh_neutral_after_tone4_1_2s",
        duration_ms=1200,
        f0_points=((0, 255), (420, 135), (560, 135), (1200, 145)),
        windows=(
            ContourWindow("tone4_early", 80, 220, 240),
            ContourWindow("tone4_late", 340, 500, 145),
            ContourWindow("neutral", 780, 1080, 145),
        ),
        gaps=(VoicelessGap(560, 650),),
        weak_windows=("neutral",),
    ),
    "zh_1_4": ContourSpec(
        name="zh_1_4",
        duration_ms=1500,
        f0_points=((0, 235), (600, 235), (720, 255), (1500, 125)),
        windows=(ContourWindow("first", 160, 520, 235), ContourWindow("second_late", 1180, 1440, 135)),
        gaps=(VoicelessGap(650, 730),),
    ),
    "zh_2_3": ContourSpec(
        name="zh_2_3",
        duration_ms=1600,
        f0_points=((0, 155), (600, 245), (760, 205), (1180, 120), (1600, 205)),
        windows=(
            ContourWindow("first_early", 120, 300, 170),
            ContourWindow("first_late", 440, 620, 230),
            ContourWindow("second_trough", 1060, 1240, 125),
            ContourWindow("second_late", 1380, 1560, 195),
        ),
        gaps=(VoicelessGap(660, 760),),
    ),
    "zh_3_3": ContourSpec(
        name="zh_3_3",
        duration_ms=1700,
        f0_points=((0, 170), (620, 240), (780, 200), (1220, 120), (1700, 205)),
        windows=(
            ContourWindow("first_early", 120, 300, 180),
            ContourWindow("first_late", 500, 660, 230),
            ContourWindow("second_trough", 1120, 1300, 125),
            ContourWindow("second_late", 1480, 1660, 195),
        ),
        gaps=(VoicelessGap(700, 800),),
    ),
    "zh_4_1": ContourSpec(
        name="zh_4_1",
        duration_ms=1500,
        f0_points=((0, 255), (600, 125), (730, 235), (1500, 235)),
        windows=(
            ContourWindow("first_early", 100, 260, 235),
            ContourWindow("first_late", 460, 620, 145),
            ContourWindow("second", 920, 1380, 235),
        ),
        gaps=(VoicelessGap(640, 730),),
    ),
    "vi_ngang_mid_level_0_9s": ContourSpec(
        name="vi_ngang_mid_level_0_9s",
        duration_ms=900,
        f0_points=((0, 190), (900, 190)),
        windows=(
            ContourWindow("early", 120, 280, 190),
            ContourWindow("mid", 360, 540, 190),
            ContourWindow("late", 640, 820, 190),
        ),
    ),
    "vi_sac_high_rising_0_9s": ContourSpec(
        name="vi_sac_high_rising_0_9s",
        duration_ms=900,
        f0_points=((0, 165), (260, 175), (900, 245)),
        windows=(
            ContourWindow("early", 100, 280, 170),
            ContourWindow("late", 620, 840, 235),
        ),
    ),
    "vi_huyen_low_falling_0_9s": ContourSpec(
        name="vi_huyen_low_falling_0_9s",
        duration_ms=900,
        f0_points=((0, 195), (900, 130)),
        windows=(
            ContourWindow("early", 100, 280, 185),
            ContourWindow("late", 620, 840, 140),
        ),
    ),
    "vi_hoi_dipping_1_0s": ContourSpec(
        name="vi_hoi_dipping_1_0s",
        duration_ms=1000,
        f0_points=((0, 180), (500, 115), (1000, 175)),
        windows=(
            ContourWindow("early", 100, 280, 165),
            ContourWindow("trough", 420, 580, 120),
            ContourWindow("late", 760, 940, 165),
        ),
    ),
    "vi_nga_broken_rising_1_0s": ContourSpec(
        name="vi_nga_broken_rising_1_0s",
        duration_ms=1000,
        f0_points=((0, 170), (360, 155), (560, 200), (1000, 245)),
        windows=(
            ContourWindow("pre_break", 180, 360, 160),
            ContourWindow("post_break", 580, 760, 215),
            ContourWindow("late", 800, 960, 240),
        ),
        gaps=(VoicelessGap(430, 520),),
    ),
    "vi_nang_low_checked_0_8s": ContourSpec(
        name="vi_nang_low_checked_0_8s",
        duration_ms=800,
        f0_points=((0, 180), (460, 115), (800, 105)),
        windows=(
            ContourWindow("early", 80, 220, 165),
            ContourWindow("late_low", 440, 620, 110),
        ),
        weak_windows=("late_low",),
    ),
}


def require_praat_and_ffmpeg() -> None:
    pytest.importorskip("parselmouth", reason=PRAAT_SKIP_REASON)
    pytest.importorskip("numpy", reason=PRAAT_SKIP_REASON)
    try:
        from anki_audio_quick_editor.audio_processor import find_ffmpeg, find_ffprobe
        from anki_audio_quick_editor.audio_state import AudioProcessingConfig

        ffmpeg_path = find_ffmpeg(AudioProcessingConfig().ffmpeg_path)
        find_ffprobe(ffmpeg_path)
    except ModuleNotFoundError:
        import shutil

        if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
            pytest.skip(FFMPEG_SKIP_REASON)
    except Exception:
        pytest.skip(FFMPEG_SKIP_REASON)


def generate_praat_vowel_fixture(path: Path, spec: ContourSpec) -> Path:
    """Generate a vowel-like WAV through Parselmouth from a known F0 schedule."""
    parselmouth = pytest.importorskip("parselmouth", reason=PRAAT_SKIP_REASON)
    np = pytest.importorskip("numpy", reason=PRAAT_SKIP_REASON)

    sample_rate = 22_050
    duration_s = spec.duration_ms / 1000
    times = np.arange(round(sample_rate * duration_s)) / sample_rate
    f0_times = np.array([time_ms / 1000 for time_ms, _hz in spec.f0_points])
    f0_values = np.array([hz for _time_ms, hz in spec.f0_points])
    f0 = np.interp(times, f0_times, f0_values)
    amplitude = _amplitude_envelope(np, times, duration_s, spec)
    phase = 2 * np.pi * np.cumsum(f0) / sample_rate
    waveform = (
        0.58 * np.sin(phase)
        + 0.26 * np.sin(phase * 2)
        + 0.11 * np.sin(phase * 3)
        + 0.05 * np.sin(phase * 4)
    )
    waveform = 0.30 * amplitude * waveform
    sound = parselmouth.Sound(waveform, sampling_frequency=sample_rate)
    sound.save(str(path), "WAV")
    return path


def expected_hz(spec: ContourSpec, time_ms: float) -> float:
    for (left_time, left_hz), (right_time, right_hz) in zip(
        spec.f0_points,
        spec.f0_points[1:],
        strict=False,
    ):
        if left_time <= time_ms <= right_time:
            span = right_time - left_time
            if span <= 0:
                return right_hz
            ratio = (time_ms - left_time) / span
            return left_hz + (right_hz - left_hz) * ratio
    return spec.f0_points[-1][1]


def window_named(spec: ContourSpec, name: str) -> ContourWindow:
    for window in spec.windows:
        if window.name == name:
            return window
    raise AssertionError(f"No window named {name!r} in {spec.name}")


def points_in_window(points, window: ContourWindow):
    return [point for point in points if window.start_ms <= point.time_ms <= window.end_ms]


def median(values: list[float]) -> float:
    ordered = sorted(values)
    if not ordered:
        raise AssertionError("Cannot compute median of an empty sequence")
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def median_pitch(points) -> float:
    return median([point.pitch_hz for point in points if point.pitch_hz is not None])


def median_intensity(points) -> float:
    return median([point.intensity_norm for point in points])


def _amplitude_envelope(np, times, duration_s: float, spec: ContourSpec):
    fade_s = min(0.035, duration_s / 8)
    envelope = np.minimum(1.0, times / fade_s) * np.minimum(1.0, (duration_s - times) / fade_s)
    envelope = np.clip(envelope, 0.0, 1.0)
    for gap in spec.gaps:
        mask = (times >= gap.start_ms / 1000) & (times <= gap.end_ms / 1000)
        envelope[mask] = 0.0
    for window_name in spec.weak_windows:
        window = window_named(spec, window_name)
        mask = (times >= window.start_ms / 1000) & (times <= window.end_ms / 1000)
        envelope[mask] *= 0.35
    return envelope
