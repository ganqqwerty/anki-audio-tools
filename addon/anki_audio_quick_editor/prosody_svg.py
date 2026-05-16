"""Render prosody tracks as standalone SVG media assets."""

from __future__ import annotations

import html
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .prosody_types import ProsodyPoint, ProsodyTrack


@dataclass(frozen=True)
class SvgPlot:
    """Fixed visualization geometry shared with the editor graph."""

    width: int = 620
    height: int = 150
    left: int = 44
    right: int = 10
    top: int = 10
    bottom: int = 34

    @property
    def plot_width(self) -> int:
        """Return drawable plot width."""
        return self.width - self.left - self.right

    @property
    def plot_height(self) -> int:
        """Return drawable plot height."""
        return self.height - self.top - self.bottom


PLOT = SvgPlot()


def make_visualization_filename(source_filename: str, now: datetime | None = None) -> str:
    """Return a preferred SVG filename tied to the source media and current time."""
    now = now or datetime.now()
    stem = _safe_filename_stem(Path(source_filename).stem or "audio")
    suffix = f"__aqe_viz_{now:%Y%m%d_%H%M%S_%f}.svg"
    max_stem_length = max(1, 120 - len(suffix))  # pragma: no mutate
    return f"{stem[:max_stem_length]}{suffix}"


def render_prosody_svg(track: ProsodyTrack) -> bytes:
    """Render ``track`` as UTF-8 SVG bytes suitable for Anki media."""
    duration_ms = max(0, int(track.duration_ms))
    intensity_path = _path_for_intensity(track.points, duration_ms)
    escaped_intensity_path = html.escape(intensity_path, quote=True)  # pragma: no mutate
    pitch_paths = "\n".join(
        f'    <path class="aqe-pitch-path" d="{html.escape(path, quote=True)}" />'  # pragma: no mutate
        for path in _pitch_paths(track)
    )
    labels = _label_svg(track)
    x_axis = _x_axis_svg(duration_ms)
    title = html.escape(f"Audio visualization for {track.source_filename}")
    analyzer = html.escape(track.analyzer_name)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{PLOT.width}" height="{PLOT.height}" viewBox="0 0 {PLOT.width} {PLOT.height}" role="img" aria-label="{title}">
  <title>{title}</title>
  <style>
    .aqe-intensity {{ fill: #4f6f8f; opacity: 0.18; stroke: none; }}
    .aqe-pitch-path {{ fill: none; stroke: #1f7a5c; stroke-linecap: round; stroke-linejoin: round; stroke-width: 2; }}
    .aqe-axis, .aqe-cursor {{ stroke: #4b5563; stroke-width: 1; opacity: 0.65; }}
    .aqe-label {{ fill: #374151; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-size: 11px; }}
    .aqe-meta {{ fill: #6b7280; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-size: 10px; }}
  </style>
  <rect x="0" y="0" width="{PLOT.width}" height="{PLOT.height}" fill="#ffffff" />
  <path class="aqe-intensity" d="{escaped_intensity_path}" />
  <g class="aqe-pitch">
{pitch_paths}
  </g>
  <g class="aqe-labels">
{labels}
  </g>
  <g class="aqe-x-axis">
{x_axis}
  </g>
  <line class="aqe-cursor" x1="{PLOT.left}" x2="{PLOT.left}" y1="{PLOT.top}" y2="{PLOT.height - PLOT.bottom}" />
  <text class="aqe-meta" x="{PLOT.left}" y="{PLOT.height - 2}">{analyzer}</text>
</svg>
"""
    return svg.encode("utf-8")  # pragma: no mutate


def _safe_filename_stem(stem: str) -> str:
    safe = "".join(ch if ch.isascii() and (ch.isalnum() or ch in {"-", "_"}) else "_" for ch in stem)  # pragma: no mutate
    safe = "_".join(part for part in safe.split("_") if part)
    return safe or "audio"


def _x_for_ms(ms: int | float, duration_ms: int) -> float:
    if duration_ms <= 0:  # pragma: no mutate
        return float(PLOT.left)
    ratio = max(0.0, min(1.0, float(ms) / duration_ms))
    return PLOT.left + ratio * PLOT.plot_width


def _y_for_pitch(pitch_hz: float | None, min_hz: float | None, max_hz: float | None) -> float:
    if not pitch_hz or not min_hz or not max_hz or max_hz <= min_hz:
        return float(PLOT.height - PLOT.bottom)
    ratio = max(0.0, min(1.0, (pitch_hz - min_hz) / (max_hz - min_hz)))
    return PLOT.top + (1.0 - ratio) * PLOT.plot_height


def _path_for_intensity(points: tuple[ProsodyPoint, ...], duration_ms: int) -> str:
    if not points or duration_ms <= 0:
        return ""
    base = float(PLOT.height - PLOT.bottom)
    head = f"M {_x_for_ms(points[0].time_ms, duration_ms):.2f} {base:.2f}"
    body = " ".join(
        f"L {_x_for_ms(point.time_ms, duration_ms):.2f} "
        f"{base - _bounded(point.intensity_norm) * PLOT.plot_height:.2f}"
        for point in points
    )
    tail = f"L {_x_for_ms(points[-1].time_ms, duration_ms):.2f} {base:.2f} Z"
    return f"{head} {body} {tail}"


def _pitch_paths(track: ProsodyTrack) -> list[str]:
    paths: list[str] = []
    current: list[tuple[float, float]] = []
    for point in track.points:
        if not point.voiced or point.pitch_hz is None:
            if current:
                _append_pitch_path(paths, current)
                current = []
            continue
        current.append(
            (
                _x_for_ms(point.time_ms, track.duration_ms),
                _y_for_pitch(point.pitch_hz, track.pitch_min_hz, track.pitch_max_hz),
            )
        )
    if current:
        _append_pitch_path(paths, current)
    return paths


def _append_pitch_path(paths: list[str], points: list[tuple[float, float]]) -> None:
    if len(points) < 2:
        return
    paths.append(
        " ".join(
            f"{'L' if index else 'M'} {x:.2f} {y:.2f}"
            for index, (x, y) in enumerate(points)
            if math.isfinite(x) and math.isfinite(y)
        )
    )


def _label_svg(track: ProsodyTrack) -> str:
    max_hz = track.pitch_max_hz or 500
    min_hz = track.pitch_min_hz or 75
    labels = (
        (max_hz, PLOT.top + 10),
        (min_hz, PLOT.height - PLOT.bottom),
    )
    return "\n".join(
        f'    <text class="aqe-label" x="2" y="{y}">{round(hz)} Hz</text>'
        for hz, y in labels
    )


def _x_axis_svg(duration_ms: int) -> str:
    ticks = _axis_ticks(duration_ms)
    rows: list[str] = []
    for tick in ticks:
        x = _x_for_ms(tick, duration_ms)
        rows.append(
            f'    <line class="aqe-axis" x1="{x:.2f}" x2="{x:.2f}" '
            f'y1="{PLOT.height - PLOT.bottom}" y2="{PLOT.height - PLOT.bottom + 4}" />'
        )
        rows.append(
            f'    <text class="aqe-label" text-anchor="middle" x="{x:.2f}" '
            f'y="{PLOT.height - 8}">{html.escape(_format_time(tick, duration_ms))}</text>'
        )
    return "\n".join(rows)


def _axis_ticks(duration_ms: int) -> list[float]:
    if duration_ms <= 0:  # pragma: no mutate
        return [0.0]
    ticks = [0.0, duration_ms / 2, float(duration_ms)]
    deduped: list[float] = []
    for tick in ticks:
        if not deduped or tick != deduped[-1]:
            deduped.append(tick)
    return deduped


def _format_time(ms: float, duration_ms: int) -> str:
    if duration_ms and duration_ms < 2000:
        return f"{round(ms)} ms"
    return f"{ms / 1000:.2f}s"


def _bounded(value: float | None) -> float:
    if value is None or not math.isfinite(value):
        return 0.0
    return min(1.0, max(0.0, float(value)))
