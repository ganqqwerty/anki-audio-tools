"""Import-safe voice recording adapter primitives."""

from __future__ import annotations

import platform
import struct
import time
import wave
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, Protocol, runtime_checkable

from .errors import AudioQuickEditorError

RecordingStartedCallback = Callable[[int], None]
RecordingCompletedCallback = Callable[["RecordingResult"], None]
RecordingFailedCallback = Callable[["AudioRecordingError"], None]


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

    return RecordingResult(path=path, generation=generation, duration_ms=duration_ms)


class NativeRecordingController:
    """Native Anki-style WAV recorder with lazy Qt and Anki helper imports."""

    def __init__(self, output_path: Path, *, mw: Any, parent: Any) -> None:
        self.output_path = output_path
        self._mw = mw
        self._parent = parent
        self._backend: _RecorderBackend | None = None
        self._generation: int | None = None
        self._started_at: float | None = None

    def start(
        self,
        generation: int,
        *,
        on_started: RecordingStartedCallback,
        on_failed: RecordingFailedCallback,
    ) -> None:
        self._generation = generation
        self._started_at = time.monotonic()
        try:
            self._backend = _create_native_backend(self.output_path, mw=self._mw, parent=self._parent)
        except (ImportError, RuntimeError) as exc:
            on_failed(AudioRecordingError(f"Unable to initialize voice recorder: {exc}"))
            return

        self._backend.start(on_started=lambda: on_started(generation), on_failed=on_failed)

    def stop(
        self,
        *,
        on_completed: RecordingCompletedCallback,
        on_failed: RecordingFailedCallback,
    ) -> None:
        if self._backend is None or self._generation is None:
            on_failed(AudioRecordingError("No voice recording is active."))
            return

        generation = self._generation
        started_at = self._started_at

        def complete(path: Path) -> None:
            try:
                result = recording_result_from_path(
                    path,
                    generation=generation,
                    started_at=started_at,
                    stopped_at=time.monotonic(),
                )
            except OSError as exc:
                on_failed(AudioRecordingError(f"Unable to read completed recording: {exc}"))
                return
            except AudioRecordingError as exc:
                on_failed(exc)
                return
            on_completed(result)

        self._backend.stop(on_completed=complete, on_failed=on_failed)


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


def _create_native_backend(output_path: Path, *, mw: Any, parent: Any) -> _RecorderBackend:
    macos_helper = _load_macos_helper()
    if macos_helper is not None and platform.machine() == "arm64":
        return _MacWavRecorderBackend(output_path, macos_helper=macos_helper)
    return _QtAudioSourceRecorderBackend(output_path, mw=mw, parent=parent)


def _load_macos_helper() -> Any | None:
    try:
        module = import_module("aqt._macos_helper")
    except (ImportError, ModuleNotFoundError):
        return None
    return getattr(module, "macos_helper", None)


class _MacWavRecorderBackend:
    def __init__(self, output_path: Path, *, macos_helper: Any) -> None:
        self.output_path = output_path
        self._macos_helper = macos_helper
        self._error: str | None = None

    def start(
        self,
        *,
        on_started: Callable[[], None],
        on_failed: RecordingFailedCallback,
    ) -> None:
        self._error = None
        try:
            self._macos_helper.start_wav_record(str(self.output_path), self._on_error)
        except (OSError, RuntimeError) as exc:
            on_failed(AudioRecordingError(f"Unable to start voice recorder: {exc}"))
            return
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
        try:
            self._macos_helper.end_wav_record()
        except (OSError, RuntimeError) as exc:
            on_failed(AudioRecordingError(f"Unable to stop voice recorder: {exc}"))
            return
        if self._error is not None:
            on_failed(AudioRecordingError(self._error))
            return
        on_completed(self.output_path)

    def _on_error(self, message: str) -> None:
        self._error = message

    def _current_error(self) -> str | None:
        return self._error


class _QtAudioSourceRecorderBackend:
    STARTUP_DELAY_SECONDS = 0.3
    STOP_PADDING_MS = 500

    def __init__(self, output_path: Path, *, mw: Any, parent: Any) -> None:
        self.output_path = output_path
        self._mw = mw
        self._parent = parent
        self._buffer = bytearray()
        self._iodevice: Any | None = None
        self._stop_timer: Any | None = None

        from PyQt6.QtMultimedia import QAudioFormat, QAudioSource, QMediaDevices

        device = QMediaDevices.defaultAudioInput()
        if hasattr(device, "isNull") and device.isNull():
            raise RuntimeError("No audio input device is available.")

        preferred_format = device.preferredFormat()
        int16_format = QAudioFormat(preferred_format)
        int16_format.setSampleFormat(QAudioFormat.SampleFormat.Int16)
        selected_format = int16_format if device.isFormatSupported(int16_format) else preferred_format

        self._audio_input = QAudioSource(device, selected_format, parent)
        self._format = self._audio_input.format()

    def start(
        self,
        *,
        on_started: Callable[[], None],
        on_failed: RecordingFailedCallback,
    ) -> None:
        self._buffer = bytearray()
        self._iodevice = self._audio_input.start()
        if self._iodevice is None:
            on_failed(AudioRecordingError("Unable to start audio input."))
            return

        self._iodevice.readyRead.connect(self._on_read_ready)
        on_started()

    def stop(
        self,
        *,
        on_completed: Callable[[Path], None],
        on_failed: RecordingFailedCallback,
    ) -> None:
        from PyQt6.QtCore import QTimer

        def on_stop_timer() -> None:
            self._on_read_ready()
            self._audio_input.stop()
            if self._has_audio_error(on_failed):
                return
            self._write_recording(on_completed=on_completed, on_failed=on_failed)

        self._stop_timer = QTimer(self._parent)
        self._stop_timer.timeout.connect(on_stop_timer)
        self._stop_timer.setSingleShot(True)
        self._stop_timer.start(self.STOP_PADDING_MS)

    def _on_read_ready(self) -> None:
        if self._iodevice is None:
            return
        self._buffer.extend(bytes(self._iodevice.readAll()))

    def _has_audio_error(self, on_failed: RecordingFailedCallback) -> bool:
        from PyQt6.QtMultimedia import QAudio

        error = self._audio_input.error()
        if error != QAudio.Error.NoError:
            on_failed(AudioRecordingError(f"Voice recording failed: {error}"))
            return True
        return False

    def _write_recording(
        self,
        *,
        on_completed: Callable[[Path], None],
        on_failed: RecordingFailedCallback,
    ) -> None:
        if hasattr(self._mw, "taskman") and hasattr(self._mw.taskman, "run_in_background"):
            self._mw.taskman.run_in_background(
                self._write_wav_file,
                lambda future: self._finish_background_write(future, on_completed, on_failed),
                uses_collection=False,
            )
            return

        try:
            self._write_wav_file()
        except (OSError, wave.Error) as exc:
            on_failed(AudioRecordingError(f"Unable to write voice recording: {exc}"))
            return
        on_completed(self.output_path)

    def _finish_background_write(
        self,
        future: Any,
        on_completed: Callable[[Path], None],
        on_failed: RecordingFailedCallback,
    ) -> None:
        try:
            future.result()
        except (OSError, wave.Error) as exc:
            on_failed(AudioRecordingError(f"Unable to write voice recording: {exc}"))
            return
        on_completed(self.output_path)

    def _write_wav_file(self) -> None:
        bytes_per_frame = self._format.bytesPerFrame()
        frames_to_skip = int(self._format.sampleRate() * self.STARTUP_DELAY_SECONDS)
        bytes_to_skip = frames_to_skip * bytes_per_frame
        audio_buffer = self._buffer[bytes_to_skip:]

        if self._is_float_sample_format():
            audio_data = _convert_float32_to_int16(audio_buffer)
            sample_width = 2
        else:
            audio_data = bytes(audio_buffer)
            sample_width = self._format.bytesPerSample()

        with wave.open(str(self.output_path), "wb") as wav_file:
            wav_file.setnchannels(self._format.channelCount())
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(self._format.sampleRate())
            wav_file.writeframes(audio_data)

    def _is_float_sample_format(self) -> bool:
        from PyQt6.QtMultimedia import QAudioFormat

        return self._format.sampleFormat() == QAudioFormat.SampleFormat.Float


def _convert_float32_to_int16(float_buffer: bytearray) -> bytes:
    float_count = len(float_buffer) // 4
    if float_count <= 0:
        return b""

    samples = struct.unpack(f"{float_count}f", float_buffer[: float_count * 4])
    int16_samples = [max(-32768, min(32767, int(max(-1.0, min(1.0, sample)) * 32767))) for sample in samples]
    return struct.pack(f"{len(int16_samples)}h", *int16_samples)
