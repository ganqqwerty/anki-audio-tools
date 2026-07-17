"""Import-safe voice recording adapter primitives."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable, Literal, Protocol, cast

from .recorder.native_types import (
    AudioRecordingError,
    RecordingCancelReason,
    RecordingCompletedCallback,
    RecordingController,
    RecordingFailedCallback,
    RecordingResult,
    RecordingStartedCallback,
    recording_result_from_path,
)

__all__ = [
    "AudioRecordingError",
    "NativeRecordingController",
    "RecordingCancelReason",
    "RecordingCompletedCallback",
    "RecordingController",
    "RecordingFailedCallback",
    "RecordingResult",
    "RecordingStartedCallback",
    "recording_result_from_path",
]


class NativeRecordingController:
    """Native Anki-style WAV recorder with lazy Qt and Anki helper imports."""

    def __init__(self, output_path: Path, *, mw: Any, parent: Any) -> None:
        self.output_path = output_path
        self._mw = mw
        self._parent = parent
        self._backend: _RecorderBackend | None = None
        self._generation: int | None = None
        self._started_at: float | None = None
        self._operation_token = 0
        self._phase: Literal[
            "idle", "starting", "recording", "stopping", "terminal", "cancelled", "disposed"
        ] = "idle"

    def start(
        self,
        generation: int,
        *,
        on_started: RecordingStartedCallback,
        on_failed: RecordingFailedCallback,
    ) -> None:
        if self._phase == "disposed":
            on_failed(AudioRecordingError("Voice recorder has been disposed."))
            return
        if self._phase in {"starting", "recording", "stopping"}:
            on_failed(AudioRecordingError("A voice recording is already active."))
            return
        self._operation_token += 1
        operation_token = self._operation_token
        self._phase = "starting"
        self._generation = generation
        self._started_at = time.monotonic()
        try:
            self._backend = _create_native_backend(self.output_path, mw=self._mw, parent=self._parent)
        except (ImportError, RuntimeError) as exc:
            self._phase = "terminal"
            on_failed(AudioRecordingError(f"Unable to initialize voice recorder: {exc}"))
            return

        def started() -> None:
            if not self._accepts_callback(operation_token, "starting"):
                return
            self._phase = "recording"
            on_started(generation)

        def failed(error: AudioRecordingError) -> None:
            if not self._accepts_callback(operation_token, "starting", "recording"):
                return
            self._phase = "terminal"
            on_failed(error)

        self._backend.start(on_started=started, on_failed=failed)

    def stop(
        self,
        *,
        on_completed: RecordingCompletedCallback,
        on_failed: RecordingFailedCallback,
    ) -> None:
        if self._backend is None or self._generation is None:
            if self._phase in {"stopping", "terminal", "cancelled", "disposed"}:
                return
            on_failed(AudioRecordingError("No voice recording is active."))
            return
        if self._phase in {"stopping", "terminal", "cancelled", "disposed"}:
            return

        generation = self._generation
        started_at = self._started_at
        operation_token = self._operation_token
        self._phase = "stopping"

        def complete(path: Path) -> None:
            if not self._accepts_callback(operation_token, "stopping"):
                return
            try:
                result = recording_result_from_path(
                    path,
                    generation=generation,
                    started_at=started_at,
                    stopped_at=time.monotonic(),
                )
            except OSError as exc:
                self._finish_with_failure(
                    operation_token,
                    AudioRecordingError(f"Unable to read completed recording: {exc}"),
                    on_failed,
                )
                return
            except AudioRecordingError as exc:
                self._finish_with_failure(operation_token, exc, on_failed)
                return
            self._phase = "terminal"
            self._backend = None
            on_completed(result)

        def failed(error: AudioRecordingError) -> None:
            self._finish_with_failure(operation_token, error, on_failed)

        self._backend.stop(on_completed=complete, on_failed=failed)

    def cancel(self, reason: RecordingCancelReason) -> None:
        if self._phase in {"cancelled", "disposed"}:
            return
        backend = self._backend
        self._operation_token += 1
        self._phase = "cancelled"
        if backend is not None:
            backend.cancel(reason)
        self._generation = None
        self._started_at = None

    def dispose(self) -> None:
        if self._phase == "disposed":
            return
        backend = self._backend
        self.cancel("dispose")
        if backend is not None:
            backend.dispose()
        self._backend = None
        self._phase = "disposed"

    def _accepts_callback(self, operation_token: int, *phases: str) -> bool:
        return operation_token == self._operation_token and self._phase in phases

    def _finish_with_failure(
        self,
        operation_token: int,
        error: AudioRecordingError,
        on_failed: RecordingFailedCallback,
    ) -> None:
        if not self._accepts_callback(operation_token, "stopping"):
            return
        self._phase = "terminal"
        on_failed(error)


class _RecorderBackend(Protocol):
    def start(
        self,
        *,
        on_started: Callable[[], None],
        on_failed: RecordingFailedCallback,
    ) -> None:
        """Start the backend recorder."""

    def stop(
        self,
        *,
        on_completed: Callable[[Path], None],
        on_failed: RecordingFailedCallback,
    ) -> None:
        """Stop the backend recorder."""

    def cancel(self, reason: RecordingCancelReason) -> None:
        """Cancel the backend and suppress completion."""

    def dispose(self) -> None:
        """Release backend resources idempotently."""


def _create_native_backend(output_path: Path, *, mw: Any, parent: Any) -> _RecorderBackend:
    from .recorder.native_backend import create_native_backend

    return cast(_RecorderBackend, create_native_backend(output_path, mw=mw, parent=parent))
