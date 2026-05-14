"""Optional Parselmouth/Praat prosody analyzer backend."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .audio_processor import probe_duration_ms
from .audio_state import AudioProcessingConfig
from .prosody_types import ProsodyPoint, ProsodyTrack, build_prosody_track

PITCH_FLOOR_HZ = 75
PITCH_CEILING_HZ = 500
TIME_STEP_S = 0.01


def is_praat_available() -> bool:
    """Return True when the optional Parselmouth runtime is importable."""
    try:
        import parselmouth  # noqa: F401
    except ImportError:
        return False
    return True


def analyze_with_praat(source_path: Path, config: AudioProcessingConfig) -> ProsodyTrack:
    """Analyze pitch and intensity with Parselmouth when it is installed."""
    import parselmouth

    sound = parselmouth.Sound(str(source_path))
    pitch = sound.to_pitch(
        time_step=TIME_STEP_S,
        pitch_floor=PITCH_FLOOR_HZ,
        pitch_ceiling=PITCH_CEILING_HZ,
    )
    intensity = sound.to_intensity(
        minimum_pitch=PITCH_FLOOR_HZ,
        time_step=TIME_STEP_S,
    )
    pitch_times = list(pitch.xs())
    frequencies = list(pitch.selected_array["frequency"])
    intensity_times = list(intensity.xs())
    intensity_values = list(intensity.values[0])
    points = [
        _point(time_s, frequency, intensity_times, intensity_values)
        for time_s, frequency in zip(pitch_times, frequencies, strict=False)
    ]
    return build_prosody_track(
        duration_ms=probe_duration_ms(source_path, config),
        points=points,
        source_filename=source_path.name,
        analyzer_name="praat-parselmouth",
    )


def _point(
    time_s: float,
    frequency: float,
    intensity_times: list[float],
    intensity_values: list[Any],
) -> ProsodyPoint:
    pitch_hz = float(frequency) if frequency and frequency > 0 else None
    intensity_db = _nearest_intensity(time_s, intensity_times, intensity_values)
    return ProsodyPoint(
        time_ms=round(time_s * 1000),
        pitch_hz=pitch_hz,
        intensity_db=intensity_db,
        intensity_norm=0.0,
        voiced=pitch_hz is not None,
    )


def _nearest_intensity(
    time_s: float,
    intensity_times: list[float],
    intensity_values: list[Any],
) -> float | None:
    if not intensity_times or not intensity_values:
        return None
    index = min(range(len(intensity_times)), key=lambda idx: abs(intensity_times[idx] - time_s))
    try:
        return float(intensity_values[index])
    except (TypeError, ValueError):
        return None
