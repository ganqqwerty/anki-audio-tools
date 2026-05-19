"""Import-safe prosody data types and normalization helpers."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class ProsodyPoint:
    """One pitch/intensity analysis frame."""

    time_ms: int
    pitch_hz: float | None
    intensity_db: float | None
    intensity_norm: float
    voiced: bool


@dataclass(frozen=True)
class ProsodyTrack:
    """Serializable pitch and intensity analysis for one audio clip."""

    duration_ms: int
    points: tuple[ProsodyPoint, ...]
    pitch_min_hz: float | None
    pitch_max_hz: float | None
    source_filename: str
    analyzer_name: str

    def to_payload(self) -> dict[str, object]:
        """Return a compact JSON-serializable payload for the editor webview."""
        return {
            "durationMs": self.duration_ms,
            "pitchMinHz": _rounded_or_none(self.pitch_min_hz),
            "pitchMaxHz": _rounded_or_none(self.pitch_max_hz),
            "sourceFilename": self.source_filename,
            "analyzerName": self.analyzer_name,
            "points": [
                [
                    point.time_ms,
                    _rounded_or_none(point.pitch_hz),
                    round(point.intensity_norm, 3),
                    point.voiced,
                ]
                for point in self.points
            ],
        }


def build_prosody_track(
    *,
    duration_ms: int,
    points: list[ProsodyPoint],
    source_filename: str,
    analyzer_name: str,
) -> ProsodyTrack:
    """Normalize intensity and derive pitch bounds for a track."""
    normalized = normalize_intensity(points)
    voiced = [point.pitch_hz for point in normalized if point.pitch_hz is not None]
    return ProsodyTrack(
        duration_ms=max(0, int(duration_ms)),
        points=tuple(normalized),
        pitch_min_hz=min(voiced) if voiced else None,
        pitch_max_hz=max(voiced) if voiced else None,
        source_filename=source_filename,
        analyzer_name=analyzer_name,
    )


def normalize_intensity(points: list[ProsodyPoint]) -> list[ProsodyPoint]:
    """Return points with robustly bounded ``intensity_norm`` values."""
    values = sorted(
        point.intensity_db
        for point in points
        if point.intensity_db is not None and math.isfinite(point.intensity_db)
    )
    if not values:
        return [replace(point, intensity_norm=0.0) for point in points]
    low = _percentile(values, 5)
    high = _percentile(values, 95)
    if high <= low:
        return [
            replace(point, intensity_norm=0.5 if point.intensity_db is not None else 0.0)
            for point in points
        ]
    return [
        replace(point, intensity_norm=_normalized(point.intensity_db, low, high))
        for point in points
    ]


def clamp_cursor_ms(cursor_ms: int | float | None, duration_ms: int | None) -> int:
    """Clamp a playback cursor to the known duration range."""
    try:
        value = int(round(float(cursor_ms if cursor_ms is not None else 0)))
    except (TypeError, ValueError):
        value = 0
    upper = max(0, int(duration_ms or 0))
    return min(max(0, value), upper)


def _normalized(value: float | None, low: float, high: float) -> float:
    if value is None or not math.isfinite(value):
        return 0.0
    return min(1.0, max(0.0, (value - low) / (high - low)))


def _percentile(values: list[float], percentile: float) -> float:
    if len(values) == 1:
        return values[0]
    position = (len(values) - 1) * percentile / 100
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return values[int(position)]
    weight = position - lower
    return values[lower] * (1 - weight) + values[upper] * weight


def _rounded_or_none(value: float | None) -> float | None:
    return None if value is None else round(float(value), 2)
