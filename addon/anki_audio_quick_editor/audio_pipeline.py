"""Import-safe planning helpers for staged audio render pipelines."""

from __future__ import annotations

import re
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

PAUSE_PIPELINE_MANIFEST_VERSION = 1

_SILENCE_START_RE = re.compile(r"silence_start:\s*(-?\d+(?:\.\d+)?)")
_SILENCE_END_RE = re.compile(
    r"silence_end:\s*(-?\d+(?:\.\d+)?)(?:\s*\|\s*silence_duration:\s*(-?\d+(?:\.\d+)?))?"
)


@dataclass(frozen=True)
class SilenceInterval:
    """A silence interval parsed from ffmpeg silencedetect output."""

    start_ms: int
    end_ms: int
    duration_ms: int


@dataclass(frozen=True)
class TimelineSegment:
    """One segment in the pause speed-up render timeline."""

    kind: str
    start_ms: int
    end_ms: int
    speed_factor: float
    output_duration_ms: int


def make_pause_pipeline_run_id(
    source_filename: str,
    *,
    now: datetime | None = None,
    token: str | None = None,
) -> str:
    """Return a stable, filesystem-safe run id for one retained pipeline run."""
    now = now or datetime.now()
    token = token or uuid.uuid4().hex[:8]
    stem = safe_filename_stem(Path(source_filename).stem or "audio")
    suffix = f"__{now:%Y%m%d_%H%M%S_%f}_{token}"
    max_stem_length = max(1, 160 - len(suffix))
    return f"{stem[:max_stem_length]}{suffix}"


def safe_filename_stem(stem: str) -> str:
    """Return an ASCII-only stem suitable for artifact directories."""
    safe = "".join(ch if ch.isascii() and (ch.isalnum() or ch in {"-", "_"}) else "_" for ch in stem)
    safe = "_".join(part for part in safe.split("_") if part)
    return safe or "audio"


def parse_silencedetect_intervals(stderr: str, duration_ms: int) -> tuple[SilenceInterval, ...]:
    """Parse ffmpeg silencedetect stderr into clamped silence intervals."""
    intervals: list[SilenceInterval] = []
    open_start_ms: int | None = None
    for line in stderr.splitlines():
        start_match = _SILENCE_START_RE.search(line)
        if start_match:
            open_start_ms = _seconds_to_ms(float(start_match.group(1)))
            continue

        end_match = _SILENCE_END_RE.search(line)
        if not end_match:
            continue
        end_ms = _seconds_to_ms(float(end_match.group(1)))
        duration_value = end_match.group(2)
        duration_from_line_ms = (
            _seconds_to_ms(float(duration_value)) if duration_value is not None else None
        )
        if open_start_ms is None:
            open_start_ms = end_ms - (duration_from_line_ms or 0)
        intervals.append(_clamped_interval(open_start_ms, end_ms, duration_ms))
        open_start_ms = None

    if open_start_ms is not None:
        intervals.append(_clamped_interval(open_start_ms, duration_ms, duration_ms))

    return tuple(_merge_intervals(intervals))


def plan_pause_timeline(
    duration_ms: int,
    silence_intervals: tuple[SilenceInterval, ...],
    *,
    min_pause_ms: int,
    target_gap_ms: int,
) -> tuple[TimelineSegment, ...]:
    """Return normal and pause segments for speeding qualifying pauses."""
    duration_ms = max(0, int(duration_ms))
    min_pause_ms = max(1, int(min_pause_ms))
    target_gap_ms = max(1, int(target_gap_ms))
    if duration_ms <= 0:
        return ()

    segments: list[TimelineSegment] = []
    cursor_ms = 0
    for interval in silence_intervals:
        start_ms = max(0, min(interval.start_ms, duration_ms))
        end_ms = max(start_ms, min(interval.end_ms, duration_ms))
        pause_duration_ms = end_ms - start_ms
        if pause_duration_ms < min_pause_ms:
            continue
        if start_ms > cursor_ms:
            segments.append(_normal_segment(cursor_ms, start_ms))
        speed_factor = max(1.0, pause_duration_ms / target_gap_ms)
        segments.append(
            TimelineSegment(
                kind="pause",
                start_ms=start_ms,
                end_ms=end_ms,
                speed_factor=round(speed_factor, 6),
                output_duration_ms=max(1, round(pause_duration_ms / speed_factor)),
            )
        )
        cursor_ms = end_ms

    if cursor_ms < duration_ms:
        segments.append(_normal_segment(cursor_ms, duration_ms))

    if not segments:
        return (_normal_segment(0, duration_ms),)
    return tuple(segment for segment in segments if segment.end_ms > segment.start_ms)


def build_filter_complex_script(
    segments: tuple[TimelineSegment, ...],
    *,
    volume_db: float,
    speed: float,
) -> str:
    """Build an ffmpeg filter_complex script for a planned timeline."""
    usable_segments = tuple(segment for segment in segments if segment.end_ms > segment.start_ms)
    if not usable_segments:
        usable_segments = (_normal_segment(0, 1),)

    lines: list[str] = []
    source_labels: list[str] = []
    if len(usable_segments) > 1:
        source_labels = [f"src{index}" for index in range(len(usable_segments))]
        split_outputs = "".join(f"[{label}]" for label in source_labels)
        lines.append(f"[0:a]asplit={len(usable_segments)}{split_outputs}")
    else:
        source_labels = ["0:a"]

    segment_labels: list[str] = []
    for index, segment in enumerate(usable_segments):
        label = f"a{index}"
        segment_labels.append(label)
        source = source_labels[index]
        start_s = segment.start_ms / 1000
        end_s = segment.end_ms / 1000
        filters = [
            f"[{source}]atrim=start={start_s:.3f}:end={end_s:.3f}",
            "asetpts=PTS-STARTPTS",
        ]
        if segment.kind == "pause" and not _is_close(segment.speed_factor, 1.0):
            filters.extend(atempo_filters(segment.speed_factor))
        lines.append(f"{','.join(filters)}[{label}]")

    concat_inputs = "".join(f"[{label}]" for label in segment_labels)
    lines.append(f"{concat_inputs}concat=n={len(segment_labels)}:v=0:a=1[cat]")

    output_filters: list[str] = []
    if not _is_close(volume_db, 0.0):
        output_filters.append(f"volume={volume_db:.2f}dB")
    if not _is_close(speed, 1.0):
        output_filters.extend(atempo_filters(speed))
    if not output_filters:
        output_filters.append("anull")
    lines.append(f"[cat]{','.join(output_filters)}[out]")
    return ";\n".join(lines) + "\n"


def atempo_filters(speed: float) -> list[str]:
    """Return ffmpeg atempo filters that represent ``speed``."""
    remaining = float(speed)
    filters: list[str] = []
    while remaining > 2.0:
        filters.append("atempo=2.000")
        remaining /= 2.0
    while remaining < 0.5:
        filters.append("atempo=0.500")
        remaining /= 0.5
    filters.append(f"atempo={remaining:.3f}")
    return filters


def intervals_to_json(intervals: tuple[SilenceInterval, ...]) -> list[dict[str, int]]:
    """Return JSON-serializable silence interval dictionaries."""
    return [asdict(interval) for interval in intervals]


def timeline_to_json(segments: tuple[TimelineSegment, ...]) -> list[dict[str, object]]:
    """Return JSON-serializable timeline segment dictionaries."""
    return [asdict(segment) for segment in segments]


def _normal_segment(start_ms: int, end_ms: int) -> TimelineSegment:
    return TimelineSegment(
        kind="normal",
        start_ms=start_ms,
        end_ms=end_ms,
        speed_factor=1.0,
        output_duration_ms=max(0, end_ms - start_ms),
    )


def _clamped_interval(start_ms: int, end_ms: int, duration_ms: int) -> SilenceInterval:
    clamped_start = max(0, min(start_ms, max(0, duration_ms)))
    clamped_end = max(clamped_start, min(end_ms, max(0, duration_ms)))
    return SilenceInterval(
        start_ms=clamped_start,
        end_ms=clamped_end,
        duration_ms=max(0, clamped_end - clamped_start),
    )


def _merge_intervals(intervals: list[SilenceInterval]) -> list[SilenceInterval]:
    merged: list[SilenceInterval] = []
    for interval in sorted(intervals, key=lambda item: (item.start_ms, item.end_ms)):
        if interval.end_ms <= interval.start_ms:
            continue
        if not merged or interval.start_ms > merged[-1].end_ms:
            merged.append(interval)
            continue
        previous = merged[-1]
        end_ms = max(previous.end_ms, interval.end_ms)
        merged[-1] = SilenceInterval(
            start_ms=previous.start_ms,
            end_ms=end_ms,
            duration_ms=end_ms - previous.start_ms,
        )
    return merged


def _seconds_to_ms(seconds: float) -> int:
    return max(0, round(seconds * 1000))


def _is_close(left: float, right: float) -> bool:
    return abs(left - right) < 0.000_001
