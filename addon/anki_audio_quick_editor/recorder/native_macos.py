"""Cancelable adapter for Anki's native macOS WAV recorder."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .native_types import (
    AudioRecordingError,
    RecordingCancelReason,
    RecordingFailedCallback,
)


class MacWavRecorderBackend:
    """Translate Anki's macOS helper into the shared recorder backend protocol."""

    def __init__(self, output_path: Path, *, macos_helper: Any) -> None:
        self.output_path = output_path
        self._macos_helper = macos_helper
        self._error: str | None = None
        self._active = False
        self._ended = False
        self._cancelled = False
        self._disposed = False
        self._output_existed_before_start = False

    def start(
        self,
        *,
        on_started: Callable[[], None],
        on_failed: RecordingFailedCallback,
    ) -> None:
        if self._disposed:
            on_failed(AudioRecordingError("Voice recorder has been disposed."))
            return
        self._error = None
        self._active = False
        self._ended = False
        self._cancelled = False
        self._output_existed_before_start = self.output_path.exists()
        try:
            self._macos_helper.start_wav_record(str(self.output_path), self._on_error)
        except (OSError, RuntimeError) as exc:
            on_failed(AudioRecordingError(f"Unable to start voice recorder: {exc}"))
            return
        self._active = True
        error = self._current_error()
        if error is not None:
            on_failed(AudioRecordingError(error))
            return
        on_started()

    def stop(
        self,
        *,
        on_completed: Callable[[Path], None],
        on_failed: RecordingFailedCallback,
    ) -> None:
        if self._cancelled or self._disposed or self._ended:
            return
        try:
            self._end_once()
        except (OSError, RuntimeError) as exc:
            on_failed(AudioRecordingError(f"Unable to stop voice recorder: {exc}"))
            return
        if self._error is not None:
            on_failed(AudioRecordingError(self._error))
            return
        on_completed(self.output_path)

    def cancel(self, _reason: RecordingCancelReason) -> None:
        if self._cancelled or self._disposed:
            return
        self._cancelled = True
        try:
            self._end_once()
        except (OSError, RuntimeError):
            pass
        self._remove_attempt_owned_output()

    def dispose(self) -> None:
        if self._disposed:
            return
        self.cancel("dispose")
        self._disposed = True

    def _end_once(self) -> None:
        if self._ended or not self._active:
            return
        self._ended = True
        self._active = False
        self._macos_helper.end_wav_record()

    def _remove_attempt_owned_output(self) -> None:
        if self._output_existed_before_start:
            return
        try:
            self.output_path.unlink(missing_ok=True)
        except OSError:
            pass

    def _on_error(self, message: str) -> None:
        self._error = message

    def _current_error(self) -> str | None:
        return self._error


__all__ = ["MacWavRecorderBackend"]
