"""Import-safe planning helpers for staged audio render pipelines."""

from __future__ import annotations

import re
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

PAUSE_PIPELINE_MANIFEST_VERSION = 1

_SILENCE_START_RE = re.compile(r"silence_start:\s*(-?\d+(?:\.\d+)?)")
_SILENCE_END_RE = re.compile(r"silence_end:\s*(-?\d+(?:\.\d+)?)")
_SILENCE_DURATION_RE = re.compile(r"silence_duration:\s*(-?\d+(?:\.\d+)?)")
_SILERO_SPEECH_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s+--\s*(-?\d+(?:\.\d+)?)\s*$")


@dataclass(frozen=True)
class SilenceInterval:
    """A silence interval parsed from ffmpeg silencedetect output."""

    start_ms: int
    end_ms: int
    duration_ms: int


@dataclass(frozen=True)
class TimelineSegment:
    """One keep segment in a staged audio render timeline."""

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
        duration_match = _SILENCE_DURATION_RE.search(line)
        duration_value = duration_match.group(1) if duration_match else None
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


def parse_silero_vad_speech_intervals(stderr: str, duration_ms: int) -> tuple[SilenceInterval, ...]:
    """Parse Sherpa ONNX Silero VAD stderr into clamped speech intervals."""
    intervals: list[SilenceInterval] = []
    for line in stderr.splitlines():
        match = _SILERO_SPEECH_RE.match(line)
        if not match:
            continue
        start_ms = _seconds_to_ms(float(match.group(1)))
        end_ms = _seconds_to_ms(float(match.group(2)))
        intervals.append(_clamped_interval(start_ms, end_ms, duration_ms))
    return tuple(_merge_intervals(intervals))


def speech_intervals_to_silence_intervals(
    speech_intervals: tuple[SilenceInterval, ...],
    duration_ms: int,
) -> tuple[SilenceInterval, ...]:
    """Return non-speech gaps for a set of speech intervals."""
    duration_ms = max(0, int(duration_ms))
    intervals: list[SilenceInterval] = []
    cursor_ms = 0
    for speech in _merge_intervals(list(speech_intervals)):
        start_ms = max(0, min(speech.start_ms, duration_ms))
        end_ms = max(start_ms, min(speech.end_ms, duration_ms))
        if start_ms > cursor_ms:
            intervals.append(_clamped_interval(cursor_ms, start_ms, duration_ms))
        cursor_ms = max(cursor_ms, end_ms)
    if cursor_ms < duration_ms:
        intervals.append(_clamped_interval(cursor_ms, duration_ms, duration_ms))
    return tuple(_merge_intervals(intervals))


def merge_short_speech_gaps(
    silence_intervals: tuple[SilenceInterval, ...],
    duration_ms: int,
    *,
    min_speech_ms: int,
) -> tuple[SilenceInterval, ...]:
    """Merge silence intervals separated by speech shorter than ``min_speech_ms``."""
    duration_ms = max(0, int(duration_ms))
    min_speech_ms = max(1, int(min_speech_ms))
    merged_source = _merge_intervals(list(silence_intervals))
    if not merged_source:
        return ()

    merged: list[SilenceInterval] = [merged_source[0]]
    for interval in merged_source[1:]:
        previous = merged[-1]
        speech_gap_ms = max(0, interval.start_ms - previous.end_ms)
        if speech_gap_ms < min_speech_ms:
            merged[-1] = _clamped_interval(previous.start_ms, interval.end_ms, duration_ms)
        else:
            merged.append(interval)
    return tuple(merged)


def filter_silence_intervals_by_duration(
    silence_intervals: tuple[SilenceInterval, ...],
    *,
    min_silence_ms: int,
) -> tuple[SilenceInterval, ...]:
    """Return only silence intervals long enough to remove."""
    min_silence_ms = max(1, int(min_silence_ms))
    return tuple(interval for interval in silence_intervals if interval.duration_ms >= min_silence_ms)


def plan_pause_removal_timeline(
    duration_ms: int,
    silence_intervals: tuple[SilenceInterval, ...],
) -> tuple[TimelineSegment, ...]:
    """Return keep-only segments for cutting detected pause intervals."""
    duration_ms = max(0, int(duration_ms))
    if duration_ms <= 0:
        return ()

    segments: list[TimelineSegment] = []
    cursor_ms = 0
    for interval in _merge_intervals(list(silence_intervals)):
        start_ms = max(0, min(interval.start_ms, duration_ms))
        end_ms = max(start_ms, min(interval.end_ms, duration_ms))
        if start_ms > cursor_ms:
            segments.append(_normal_segment(cursor_ms, start_ms))
        cursor_ms = max(cursor_ms, end_ms)
    if cursor_ms < duration_ms:
        segments.append(_normal_segment(cursor_ms, duration_ms))
    if not segments:
        return (_normal_segment(0, min(duration_ms, 1)),)
    return tuple(segment for segment in segments if segment.end_ms > segment.start_ms)


def build_filter_complex_script(
    segments: tuple[TimelineSegment, ...],
    *,
    volume_db: float,
    speed: float,
) -> str:
    """Build an ffmpeg filter_complex script for a planned timeline."""
    usable_segments = _usable_timeline_segments(segments)
    source_labels, lines = _source_labels_and_split_lines(len(usable_segments))
    segment_labels = [f"a{index}" for index in range(len(usable_segments))]
    lines.extend(
        _segment_filter_line(source, label, segment)
        for source, label, segment in zip(source_labels, segment_labels, usable_segments, strict=True)
    )

    concat_inputs = "".join(f"[{label}]" for label in segment_labels)
    lines.append(f"{concat_inputs}concat=n={len(segment_labels)}:v=0:a=1[cat]")
    lines.append(f"[cat]{','.join(_output_filters(volume_db, speed))}[out]")
    return ";\n".join(lines) + "\n"


def _usable_timeline_segments(segments: tuple[TimelineSegment, ...]) -> tuple[TimelineSegment, ...]:
    usable_segments = tuple(segment for segment in segments if segment.end_ms > segment.start_ms)
    return usable_segments or (_normal_segment(0, 1),)


def _source_labels_and_split_lines(segment_count: int) -> tuple[list[str], list[str]]:
    if segment_count <= 1:
        return ["0:a"], []
    source_labels = [f"src{index}" for index in range(segment_count)]
    split_outputs = "".join(f"[{label}]" for label in source_labels)
    return source_labels, [f"[0:a]asplit={segment_count}{split_outputs}"]


def _segment_filter_line(source: str, label: str, segment: TimelineSegment) -> str:
    filters = [
        f"[{source}]atrim=start={segment.start_ms / 1000:.3f}:end={segment.end_ms / 1000:.3f}",
        "asetpts=PTS-STARTPTS",
    ]
    return f"{','.join(filters)}[{label}]"


def _output_filters(volume_db: float, speed: float) -> list[str]:
    filters: list[str] = []
    if not _is_close(volume_db, 0.0):
        filters.append(f"volume={volume_db:.2f}dB")
    if not _is_close(speed, 1.0):
        filters.extend(atempo_filters(speed))
    return filters or ["anull"]


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
