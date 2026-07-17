"""Import-safe native recording port and result types."""

from __future__ import annotations

import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal, Protocol, runtime_checkable

from ..errors import AudioQuickEditorError

RecordingStartedCallback = Callable[[int], None]
RecordingCompletedCallback = Callable[["RecordingResult"], None]
RecordingFailedCallback = Callable[["AudioRecordingError"], None]
RecordingCancelReason = Literal[
    "application_shutdown",
    "collection_closed",
    "dispose",
    "editor_closed",
    "note_changed",
    "replaced",
    "source_replaced",
    "user",
]


class AudioRecordingError(AudioQuickEditorError):
    """Raised when native voice recording cannot start or complete."""


@dataclass(frozen=True)
class RecordingResult:
    """Completed learner recording metadata."""

    path: Path
    generation: int
    duration_ms: int | None = None


@runtime_checkable
class RecordingController(Protocol):
    """Small callback-based interface implemented by native and fake recorders."""

    def start(
        self,
        generation: int,
        *,
        on_started: RecordingStartedCallback,
        on_failed: RecordingFailedCallback,
    ) -> None:
        """Start recording for a session generation."""

    def stop(
        self,
        *,
        on_completed: RecordingCompletedCallback,
        on_failed: RecordingFailedCallback,
    ) -> None:
        """Stop recording and return the produced WAV path."""

    def cancel(self, reason: RecordingCancelReason) -> None:
        """Cancel active capture and suppress all pending publication callbacks."""

    def dispose(self) -> None:
        """Release recorder resources idempotently."""


def recording_result_from_path(
    path: Path,
    *,
    generation: int,
    started_at: float | None = None,
    stopped_at: float | None = None,
) -> RecordingResult:
    """Validate a completed recording path and build a result object."""
    if not path.is_file():
        raise AudioRecordingError("Recording did not produce an audio file.")
    if path.stat().st_size <= 0:
        raise AudioRecordingError("Recording produced an empty audio file.")

    duration_ms: int | None = None
    if started_at is not None and stopped_at is not None:
        duration_ms = max(0, round((stopped_at - started_at) * 1000))
    else:
        try:
            with wave.open(str(path), "rb") as wav_file:
                frame_rate = wav_file.getframerate()
                if frame_rate > 0:
                    duration_ms = round(wav_file.getnframes() * 1000 / frame_rate)
        except (EOFError, wave.Error):
            duration_ms = None

    return RecordingResult(path=path, generation=generation, duration_ms=duration_ms)


__all__ = [
    "AudioRecordingError",
    "RecordingCancelReason",
    "RecordingCompletedCallback",
    "RecordingController",
    "RecordingFailedCallback",
    "RecordingResult",
    "RecordingStartedCallback",
    "recording_result_from_path",
]
