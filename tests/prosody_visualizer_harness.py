"""Helpers for exercising visualizer pitch coordinate semantics."""

from __future__ import annotations

from typing import Any

PLOT = {"width": 620, "height": 150, "left": 44, "right": 10, "top": 10, "bottom": 34}


def render_pitch_points(track_payload: dict[str, Any]) -> dict[str, Any]:
    points = [_normalize_point(point) for point in track_payload["points"]]
    duration_ms = int(track_payload["durationMs"])
    min_hz = track_payload["pitchMinHz"]
    max_hz = track_payload["pitchMaxHz"]
    paths = [
        _path_for_segment(segment)
        for segment in _pitch_segments(points, duration_ms, min_hz, max_hz)
        if len(segment) >= 2
    ]
    rendered = [
        {
            "timeMs": point[0],
            "pitchHz": point[1],
            "x": _x_for_ms(point[0], duration_ms),
            "y": _y_for_pitch(point[1], min_hz, max_hz),
        }
        for point in points
        if point[3] and point[1] is not None
    ]
    return {"paths": paths, "rendered": rendered}


def _normalize_point(point: list[bool | float | int | None]) -> tuple[int, float | None, float, bool]:
    time_ms = int(point[0]) if isinstance(point[0], (float, int)) else 0
    pitch_hz = float(point[1]) if isinstance(point[1], (float, int)) else None
    intensity = float(point[2]) if isinstance(point[2], (float, int)) else 0.0
    voiced = bool(point[3]) if isinstance(point[3], bool) else False
    return time_ms, pitch_hz, intensity, voiced


def _plot_width() -> int:
    return PLOT["width"] - PLOT["left"] - PLOT["right"]


def _plot_height() -> int:
    return PLOT["height"] - PLOT["top"] - PLOT["bottom"]


def _x_for_ms(ms: int, duration_ms: int) -> float:
    if not duration_ms:
        return float(PLOT["left"])
    ratio = max(0.0, min(1.0, ms / duration_ms))
    return PLOT["left"] + ratio * _plot_width()


def _y_for_pitch(pitch_hz: float | None, min_hz: float | None, max_hz: float | None) -> float:
    if not pitch_hz or not min_hz or not max_hz or max_hz <= min_hz:
        return float(PLOT["height"] - PLOT["bottom"])
    ratio = max(0.0, min(1.0, (pitch_hz - min_hz) / (max_hz - min_hz)))
    return PLOT["top"] + (1 - ratio) * _plot_height()


def _pitch_segments(
    points: list[tuple[int, float | None, float, bool]],
    duration_ms: int,
    min_hz: float | None,
    max_hz: float | None,
) -> list[list[tuple[float, float]]]:
    segments: list[list[tuple[float, float]]] = []
    current: list[tuple[float, float]] = []
    for point in points:
        pitch_hz = point[1]
        if not point[3] or pitch_hz is None:
            if current:
                segments.append(current)
            current = []
            continue
        current.append((_x_for_ms(point[0], duration_ms), _y_for_pitch(pitch_hz, min_hz, max_hz)))
    if current:
        segments.append(current)
    return segments


def _path_for_segment(segment: list[tuple[float, float]]) -> str:
    return " ".join(
        f"{'L' if index else 'M'} {point[0]:.2f} {point[1]:.2f}"
        for index, point in enumerate(segment)
    )
