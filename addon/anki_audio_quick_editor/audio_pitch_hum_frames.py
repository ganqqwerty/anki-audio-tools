"""Pitch hum frame cleanup and lookup helpers."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace

F0_SPIKE_RATIO = 1.8
MIN_VOICED_ISLAND_MS = 30


@dataclass(frozen=True)
class PitchHumFrame:
    """One Praat pitch frame used for neutral hum synthesis."""

    time_s: float
    pitch_hz: float | None
    intensity_db: float | None


def sanitize_pitch_hum_frames(
    frames: Sequence[PitchHumFrame],
    *,
    pitch_floor_hz: float,
    pitch_ceiling_hz: float,
) -> list[PitchHumFrame]:
    """Return frames with obvious F0 tracking artifacts removed."""
    clamped = [
        _clamp_frame_pitch(frame, pitch_floor_hz, pitch_ceiling_hz)
        for frame in sorted_pitch_frames(frames)
    ]
    without_spikes = _drop_octave_spikes(clamped)
    smoothed = _median_smooth_voiced_pitch(without_spikes)
    return _drop_short_voiced_islands(smoothed)


def sorted_pitch_frames(frames: Sequence[PitchHumFrame]) -> list[PitchHumFrame]:
    return sorted(frames, key=lambda pitch_frame: pitch_frame.time_s)


def max_voiced_intensity_db(frames: Sequence[PitchHumFrame]) -> float | None:
    voiced_levels = [
        pitch_frame.intensity_db
        for pitch_frame in frames
        if pitch_frame.pitch_hz is not None and pitch_frame.intensity_db is not None
    ]
    return max(voiced_levels) if voiced_levels else None


def sample_frame_pair(
    sorted_frames: Sequence[PitchHumFrame],
    frame_index: int,
    time_s: float,
) -> tuple[int, PitchHumFrame | None, PitchHumFrame | None]:
    while (
        frame_index + 1 < len(sorted_frames)
        and sorted_frames[frame_index + 1].time_s <= time_s
    ):
        frame_index += 1
    frame = sorted_frames[frame_index] if sorted_frames else None
    next_frame = (
        sorted_frames[frame_index + 1]
        if frame_index + 1 < len(sorted_frames)
        else None
    )
    return frame_index, frame, next_frame


def frame_pitch_at(
    time_s: float,
    frame: PitchHumFrame | None,
    next_frame: PitchHumFrame | None,
) -> float | None:
    if frame is None or frame.pitch_hz is None:
        return None
    if next_frame is None or next_frame.pitch_hz is None or next_frame.time_s <= frame.time_s:
        return frame.pitch_hz
    progress = max(0.0, min(1.0, (time_s - frame.time_s) / (next_frame.time_s - frame.time_s)))
    return frame.pitch_hz + ((next_frame.pitch_hz - frame.pitch_hz) * progress)


def _clamp_frame_pitch(
    frame: PitchHumFrame,
    pitch_floor_hz: float,
    pitch_ceiling_hz: float,
) -> PitchHumFrame:
    if frame.pitch_hz is None:
        return frame
    floor = min(pitch_floor_hz, pitch_ceiling_hz)
    ceiling = max(pitch_floor_hz, pitch_ceiling_hz)
    return replace(frame, pitch_hz=max(floor, min(ceiling, frame.pitch_hz)))


def _drop_octave_spikes(frames: Sequence[PitchHumFrame]) -> list[PitchHumFrame]:
    result = list(frames)
    for index in range(1, len(frames) - 1):
        before = frames[index - 1].pitch_hz
        current = frames[index].pitch_hz
        after = frames[index + 1].pitch_hz
        if current is None or before is None or after is None:
            continue
        if _pitch_ratio(before, after) > F0_SPIKE_RATIO:
            continue
        if (
            _pitch_ratio(current, before) > F0_SPIKE_RATIO
            and _pitch_ratio(current, after) > F0_SPIKE_RATIO
        ):
            result[index] = replace(frames[index], pitch_hz=None)
    return result


def _median_smooth_voiced_pitch(frames: Sequence[PitchHumFrame]) -> list[PitchHumFrame]:
    result = list(frames)
    for index, frame in enumerate(frames):
        if frame.pitch_hz is None:
            continue
        values = [
            nearby.pitch_hz
            for nearby in frames[max(0, index - 1) : index + 2]
            if nearby.pitch_hz is not None
        ]
        if len(values) == 3:
            result[index] = replace(frame, pitch_hz=sorted(values)[1])
    return result


def _drop_short_voiced_islands(frames: Sequence[PitchHumFrame]) -> list[PitchHumFrame]:
    result = list(frames)
    index = 0
    while index < len(frames):
        if frames[index].pitch_hz is None:
            index += 1
            continue
        start = index
        while index < len(frames) and frames[index].pitch_hz is not None:
            index += 1
        if _is_short_voiced_island(frames, start, index):
            for drop_index in range(start, index):
                result[drop_index] = replace(frames[drop_index], pitch_hz=None)
    return result


def _is_short_voiced_island(
    frames: Sequence[PitchHumFrame],
    start: int,
    end: int,
) -> bool:
    has_unvoiced_before = start > 0 and frames[start - 1].pitch_hz is None
    has_unvoiced_after = end < len(frames) and frames[end].pitch_hz is None
    if not has_unvoiced_before or not has_unvoiced_after:
        return False
    island_end_s = frames[end].time_s
    duration_ms = max(0.0, (island_end_s - frames[start].time_s) * 1000)
    return duration_ms < MIN_VOICED_ISLAND_MS


def _pitch_ratio(first_hz: float, second_hz: float) -> float:
    lower = max(0.000_001, min(abs(first_hz), abs(second_hz)))
    upper = max(abs(first_hz), abs(second_hz))
    return upper / lower
