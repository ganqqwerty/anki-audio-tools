"""Shared Qt audio recording test fixtures."""

from __future__ import annotations

import sys
import wave
from array import array
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest


class FakeSignal:
    def __init__(self) -> None:
        self._callbacks: list[object] = []

    def connect(self, callback: object) -> None:
        self._callbacks.append(callback)

    def emit(self) -> None:
        for callback in list(self._callbacks):
            assert callable(callback)
            callback()


class FakeAudioFormat:
    class SampleFormat:
        Int16 = "int16"
        Float = "float"

    def __init__(
        self,
        other: "FakeAudioFormat | None" = None,
        *,
        sample_format: str = SampleFormat.Int16,
        sample_rate: int = 10,
        channel_count: int = 1,
    ) -> None:
        if other is not None:
            self._sample_format = other._sample_format
            self._sample_rate = other._sample_rate
            self._channel_count = other._channel_count
        else:
            self._sample_format = sample_format
            self._sample_rate = sample_rate
            self._channel_count = channel_count

    def setSampleFormat(self, sample_format: str) -> None:
        self._sample_format = sample_format

    def sampleFormat(self) -> str:
        return self._sample_format

    def bytesPerSample(self) -> int:
        return 4 if self._sample_format == self.SampleFormat.Float else 2

    def bytesPerFrame(self) -> int:
        return self.bytesPerSample() * self._channel_count

    def sampleRate(self) -> int:
        return self._sample_rate

    def channelCount(self) -> int:
        return self._channel_count


class FakeAudioDevice:
    def __init__(
        self,
        preferred_format: FakeAudioFormat,
        *,
        is_null: bool = False,
        supports_int16: bool = True,
    ) -> None:
        self._preferred_format = preferred_format
        self._is_null = is_null
        self._supports_int16 = supports_int16

    def isNull(self) -> bool:
        return self._is_null

    def preferredFormat(self) -> FakeAudioFormat:
        return self._preferred_format

    def isFormatSupported(self, audio_format: FakeAudioFormat) -> bool:
        if audio_format.sampleFormat() == FakeAudioFormat.SampleFormat.Int16:
            return self._supports_int16
        return True


class FakeIODevice:
    def __init__(self, *chunks: bytes) -> None:
        self.readyRead = FakeSignal()
        self._chunks = list(chunks)

    def readAll(self) -> bytes:
        if not self._chunks:
            return b""
        return self._chunks.pop(0)


class FakeFuture:
    def __init__(self, error: Exception | None = None) -> None:
        self._error = error

    def result(self) -> None:
        if self._error is not None:
            raise self._error


def install_fake_qt(
    monkeypatch: pytest.MonkeyPatch,
    *,
    preferred_format: FakeAudioFormat,
    iodevice: FakeIODevice | None,
    is_null_device: bool = False,
    supports_int16: bool = True,
    audio_error: object = "no-error",
) -> SimpleNamespace:
    state = SimpleNamespace(
        device=FakeAudioDevice(
            preferred_format,
            is_null=is_null_device,
            supports_int16=supports_int16,
        ),
        iodevice=iodevice,
        audio_error=audio_error,
        timers=[],
        audio_sources=[],
    )

    qt_multimedia = ModuleType("PyQt6.QtMultimedia")
    qt_core = ModuleType("PyQt6.QtCore")
    pyqt6 = ModuleType("PyQt6")

    class QAudio:
        class Error:
            NoError = "no-error"

    class QAudioSource:
        def __init__(self, device: FakeAudioDevice, selected_format: FakeAudioFormat, parent: object) -> None:
            self.device = device
            self.selected_format = selected_format
            self.parent = parent
            self.stopped = False
            state.audio_sources.append(self)

        def format(self) -> FakeAudioFormat:
            return self.selected_format

        def start(self) -> FakeIODevice | None:
            return state.iodevice

        def stop(self) -> None:
            self.stopped = True

        def error(self) -> object:
            return state.audio_error

    class QMediaDevices:
        @staticmethod
        def defaultAudioInput() -> FakeAudioDevice:
            return state.device

    class QTimer:
        def __init__(self, parent: object) -> None:
            self.parent = parent
            self.timeout = FakeSignal()
            self.started_ms: int | None = None
            self.single_shot = False
            state.timers.append(self)

        def setSingleShot(self, single_shot: bool) -> None:
            self.single_shot = single_shot

        def start(self, timeout_ms: int) -> None:
            self.started_ms = timeout_ms

    qt_multimedia.QAudio = QAudio
    qt_multimedia.QAudioFormat = FakeAudioFormat
    qt_multimedia.QAudioSource = QAudioSource
    qt_multimedia.QMediaDevices = QMediaDevices
    qt_core.QTimer = QTimer
    pyqt6.QtMultimedia = qt_multimedia
    pyqt6.QtCore = qt_core

    monkeypatch.setitem(sys.modules, "PyQt6", pyqt6)
    monkeypatch.setitem(sys.modules, "PyQt6.QtMultimedia", qt_multimedia)
    monkeypatch.setitem(sys.modules, "PyQt6.QtCore", qt_core)
    return state


def read_wav_pcm(path: Path) -> tuple[int, int, int, array[int]]:
    with wave.open(str(path), "rb") as wav_file:
        sample_rate = wav_file.getframerate()
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        samples = array("h")
        samples.frombytes(wav_file.readframes(wav_file.getnframes()))
    return sample_rate, channels, sample_width, samples
