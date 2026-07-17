"""Cancelable Qt audio-source recorder adapter."""

from __future__ import annotations

import struct
import wave
from pathlib import Path
from typing import Any, Callable

from .native_types import (
    AudioRecordingError,
    RecordingCancelReason,
    RecordingFailedCallback,
)


class QtAudioSourceRecorderBackend:
    """Capture microphone PCM with Qt and finalize it as WAV."""

    STARTUP_DELAY_SECONDS = 0.3
    STOP_PADDING_MS = 500

    def __init__(self, output_path: Path, *, mw: Any, parent: Any) -> None:
        self.output_path = output_path
        self._mw = mw
        self._parent = parent
        self._buffer = bytearray()
        self._iodevice: Any | None = None
        self._stop_timer: Any | None = None
        self._operation_token = 0
        self._active = False
        self._stop_started = False
        self._audio_input_stopped = False
        self._cancelled = False
        self._disposed = False
        self._terminal = False
        self._output_existed_before_start = False

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
        if self._disposed:
            on_failed(AudioRecordingError("Voice recorder has been disposed."))
            return
        self._operation_token += 1
        self._buffer = bytearray()
        self._active = False
        self._stop_started = False
        self._audio_input_stopped = False
        self._cancelled = False
        self._terminal = False
        self._output_existed_before_start = self.output_path.exists()
        self._iodevice = self._audio_input.start()
        if self._iodevice is None:
            self._terminal = True
            on_failed(AudioRecordingError("Unable to start audio input."))
            return

        self._iodevice.readyRead.connect(self._on_read_ready)
        self._active = True
        on_started()

    def stop(
        self,
        *,
        on_completed: Callable[[Path], None],
        on_failed: RecordingFailedCallback,
    ) -> None:
        if self._cancelled or self._disposed or self._terminal or self._stop_started:
            return
        from PyQt6.QtCore import QTimer

        self._stop_started = True
        operation_token = self._operation_token

        def on_stop_timer() -> None:
            if not self._accepts_operation(operation_token):
                return
            self._on_read_ready()
            self._disconnect_read_ready()
            self._stop_audio_input_once()
            if self._has_audio_error(on_failed):
                self._terminal = True
                return
            self._write_recording(
                on_completed=on_completed,
                on_failed=on_failed,
                operation_token=operation_token,
            )

        self._stop_timer = QTimer(self._parent)
        self._stop_timer.timeout.connect(on_stop_timer)
        self._stop_timer.setSingleShot(True)
        self._stop_timer.start(self.STOP_PADDING_MS)

    def _on_read_ready(self) -> None:
        if self._iodevice is None or self._cancelled or self._disposed:
            return
        self._buffer.extend(bytes(self._iodevice.readAll()))

    def cancel(self, _reason: RecordingCancelReason) -> None:
        if self._cancelled or self._disposed:
            return
        self._cancelled = True
        self._operation_token += 1
        if self._stop_timer is not None:
            self._stop_timer.stop()
        self._disconnect_read_ready()
        self._stop_audio_input_once()
        self._iodevice = None
        self._buffer = bytearray()
        self._remove_attempt_owned_output()

    def dispose(self) -> None:
        if self._disposed:
            return
        self.cancel("dispose")
        self._disposed = True

    def _accepts_operation(self, operation_token: int) -> bool:
        return (
            operation_token == self._operation_token
            and not self._cancelled
            and not self._disposed
            and not self._terminal
        )

    def _disconnect_read_ready(self) -> None:
        if self._iodevice is None:
            return
        try:
            self._iodevice.readyRead.disconnect(self._on_read_ready)
        except (RuntimeError, TypeError):
            pass

    def _stop_audio_input_once(self) -> None:
        if self._audio_input_stopped or not self._active:
            return
        self._audio_input_stopped = True
        self._active = False
        self._audio_input.stop()

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
        operation_token: int | None = None,
    ) -> None:
        if hasattr(self._mw, "taskman") and hasattr(self._mw.taskman, "run_in_background"):
            self._mw.taskman.run_in_background(
                self._write_wav_file,
                lambda future: self._finish_background_write(
                    future,
                    on_completed,
                    on_failed,
                    operation_token=operation_token,
                ),
                uses_collection=False,
            )
            return

        try:
            self._write_wav_file()
        except (OSError, wave.Error) as exc:
            if operation_token is not None and not self._accepts_operation(operation_token):
                self._remove_attempt_owned_output()
                return
            self._terminal = True
            on_failed(AudioRecordingError(f"Unable to write voice recording: {exc}"))
            return
        if operation_token is not None and not self._accepts_operation(operation_token):
            self._remove_attempt_owned_output()
            return
        self._terminal = True
        on_completed(self.output_path)

    def _finish_background_write(
        self,
        future: Any,
        on_completed: Callable[[Path], None],
        on_failed: RecordingFailedCallback,
        *,
        operation_token: int | None = None,
    ) -> None:
        try:
            future.result()
        except (OSError, wave.Error) as exc:
            if operation_token is not None and not self._accepts_operation(operation_token):
                self._remove_attempt_owned_output()
                return
            self._terminal = True
            on_failed(AudioRecordingError(f"Unable to write voice recording: {exc}"))
            return
        if operation_token is not None and not self._accepts_operation(operation_token):
            self._remove_attempt_owned_output()
            return
        self._terminal = True
        on_completed(self.output_path)

    def _remove_attempt_owned_output(self) -> None:
        if self._output_existed_before_start:
            return
        try:
            self.output_path.unlink(missing_ok=True)
        except OSError:
            pass

    def _write_wav_file(self) -> None:
        bytes_per_frame = self._format.bytesPerFrame()
        frames_to_skip = int(self._format.sampleRate() * self.STARTUP_DELAY_SECONDS)
        bytes_to_skip = frames_to_skip * bytes_per_frame
        audio_buffer = self._buffer[bytes_to_skip:]

        if self._is_float_sample_format():
            audio_data = convert_float32_to_int16(audio_buffer)
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


def convert_float32_to_int16(float_buffer: bytearray) -> bytes:
    """Convert clamped native-endian float32 PCM to signed int16 PCM."""
    float_count = len(float_buffer) // 4
    if float_count <= 0:
        return b""

    samples = struct.unpack(f"{float_count}f", float_buffer[: float_count * 4])
    int16_samples = [
        max(-32768, min(32767, int(max(-1.0, min(1.0, sample)) * 32767)))
        for sample in samples
    ]
    return struct.pack(f"{len(int16_samples)}h", *int16_samples)


__all__ = ["QtAudioSourceRecorderBackend", "convert_float32_to_int16"]
