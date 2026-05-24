"""Shared playback helpers for editor E2E tests."""

from __future__ import annotations

import re
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import patch

from e2e.conftest import import_runtime_addon_module

PLAYBACK_INTERVAL_TOLERANCE_MS = 75


@dataclass
class PlaybackAttempt:
    filename: str
    path: Path
    duration_ms: int
    start_ms: int = 0
    end_ms: int = 0
    audible_start_ms: int = 0
    audible_end_ms: int = 0
    started_at: float = 0.0
    seek_calls: list[float] | None = None

    def __post_init__(self) -> None:
        self.end_ms = self.duration_ms
        self.audible_end_ms = self.duration_ms
        if self.seek_calls is None:
            self.seek_calls = []


class FakePlaybackRecorder:
    def __init__(
        self,
        media_dir: Path,
        durations_ms: dict[str, int],
        *,
        apply_immediate_seek: bool = True,
        ffmpeg_config: Any | None = None,
    ) -> None:
        self.media_dir = media_dir
        self.durations_ms = durations_ms
        self.apply_immediate_seek = apply_immediate_seek
        self.ffmpeg_config = ffmpeg_config
        self.attempts: list[PlaybackAttempt] = []
        self.unknown_filenames: list[str] = []
        self.stop_count = 0
        self.toggle_count = 0

    @property
    def current(self) -> PlaybackAttempt | None:
        return self.attempts[-1] if self.attempts else None

    def play_tags(self, tags) -> None:
        tag = tags[0]
        filename = str(tag.filename)
        path = Path(filename)
        if not path.is_absolute():
            path = self.media_dir / filename
        duration_ms = self._duration_ms(path)
        attempt = PlaybackAttempt(
            filename=path.name,
            path=path,
            duration_ms=duration_ms,
            started_at=time.monotonic(),
        )
        segment_start_ms = _playback_segment_start_ms(path.name)
        if segment_start_ms is not None:
            attempt.start_ms = segment_start_ms
            attempt.end_ms = segment_start_ms + duration_ms
            attempt.audible_start_ms = segment_start_ms
            attempt.audible_end_ms = attempt.end_ms
        self.attempts.append(attempt)

    def _duration_ms(self, path: Path) -> int:
        duration_ms = self.durations_ms.get(path.name)
        if duration_ms is not None:
            return duration_ms
        if self.ffmpeg_config is not None and path.is_file():
            probe_duration_ms = import_runtime_addon_module(".audio_processor").probe_duration_ms

            return probe_duration_ms(path, self.ffmpeg_config)
        self.unknown_filenames.append(path.name)
        return next(iter(self.durations_ms.values()))

    def seek_relative(self, seconds: float) -> None:
        current = self.current
        if current is None:
            return
        current.seek_calls = current.seek_calls or []
        current.seek_calls.append(seconds)
        current.start_ms = max(
            0,
            min(current.duration_ms, current.start_ms + round(seconds * 1000)),
        )
        if self.apply_immediate_seek:
            current.audible_start_ms = current.start_ms

    def stop_and_clear_queue(self) -> None:
        self.stop_count += 1
        current = self.current
        if current is None or current.started_at <= 0:
            return
        elapsed_ms = round((time.monotonic() - current.started_at) * 1000)
        current.audible_end_ms = max(
            current.audible_start_ms,
            min(current.duration_ms, current.audible_start_ms + elapsed_ms),
        )

    def toggle_pause(self) -> None:
        self.toggle_count += 1


@contextmanager
def _record_fake_playback(
    media_dir: Path,
    durations_ms: dict[str, int],
    *,
    apply_immediate_seek: bool = True,
    ffmpeg_config: Any | None = None,
):
    from aqt.sound import av_player

    recorder = FakePlaybackRecorder(
        media_dir,
        durations_ms,
        apply_immediate_seek=apply_immediate_seek,
        ffmpeg_config=ffmpeg_config,
    )
    with (
        patch.object(av_player, "stop_and_clear_queue", recorder.stop_and_clear_queue),
        patch.object(av_player, "play_tags", recorder.play_tags),
        patch.object(av_player, "seek_relative", recorder.seek_relative),
        patch.object(av_player, "toggle_pause", recorder.toggle_pause),
    ):
        yield recorder


def _assert_interval(
    attempt: PlaybackAttempt,
    expected_start_ms: int,
    *,
    expected_end_ms: int | None = None,
    tolerance_ms: int = PLAYBACK_INTERVAL_TOLERANCE_MS,
) -> None:
    assert abs(attempt.start_ms - expected_start_ms) <= tolerance_ms
    if expected_end_ms is not None:
        assert abs(attempt.end_ms - expected_end_ms) <= tolerance_ms
    else:
        assert attempt.end_ms >= attempt.start_ms


def _playback_segment_start_ms(filename: str) -> int | None:
    match = re.search(r"__from_(\d+)ms_", filename)
    return int(match.group(1)) if match else None


def _shift_click_region(editor, ratio: float, ord_: int = 0) -> None:
    from e2e.editor_region_loop_helpers import (
        _shift_click_region as _region_shift_click,
    )

    _region_shift_click(editor, ratio, ord_)
