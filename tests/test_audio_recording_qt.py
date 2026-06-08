from __future__ import annotations

import struct
import sys
import wave
from array import array
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

import anki_audio_quick_editor.audio_recording as audio_recording
from anki_audio_quick_editor.audio_recording import (
    AudioRecordingError,
    _QtAudioSourceRecorderBackend,
    _convert_float32_to_int16,
)


class _Signal:
    def __init__(self) -> None:
        self._callbacks: list[object] = []

    def connect(self, callback: object) -> None:
        self._callbacks.append(callback)

    def emit(self) -> None:
        for callback in list(self._callbacks):
            assert callable(callback)
            callback()


class _FakeAudioFormat:
    class SampleFormat:
        Int16 = "int16"
        Float = "float"

    def __init__(
        self,
        other: "_FakeAudioFormat | None" = None,
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


class _FakeAudioDevice:
    def __init__(
        self,
        preferred_format: _FakeAudioFormat,
        *,
        is_null: bool = False,
        supports_int16: bool = True,
    ) -> None:
        self._preferred_format = preferred_format
        self._is_null = is_null
        self._supports_int16 = supports_int16

    def isNull(self) -> bool:
        return self._is_null

    def preferredFormat(self) -> _FakeAudioFormat:
        return self._preferred_format

    def isFormatSupported(self, audio_format: _FakeAudioFormat) -> bool:
        if audio_format.sampleFormat() == _FakeAudioFormat.SampleFormat.Int16:
            return self._supports_int16
        return True


class _FakeIODevice:
    def __init__(self, *chunks: bytes) -> None:
        self.readyRead = _Signal()
        self._chunks = list(chunks)

    def readAll(self) -> bytes:
        if not self._chunks:
            return b""
        return self._chunks.pop(0)


class _FakeFuture:
    def __init__(self, error: Exception | None = None) -> None:
        self._error = error

    def result(self) -> None:
        if self._error is not None:
            raise self._error


def _install_fake_qt(
    monkeypatch: pytest.MonkeyPatch,
    *,
    preferred_format: _FakeAudioFormat,
    iodevice: _FakeIODevice | None,
    is_null_device: bool = False,
    supports_int16: bool = True,
    audio_error: object = "no-error",
) -> SimpleNamespace:
    state = SimpleNamespace(
        device=_FakeAudioDevice(
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
        def __init__(self, device: _FakeAudioDevice, selected_format: _FakeAudioFormat, parent: object) -> None:
            self.device = device
            self.selected_format = selected_format
            self.parent = parent
            self.stopped = False
            state.audio_sources.append(self)

        def format(self) -> _FakeAudioFormat:
            return self.selected_format

        def start(self) -> _FakeIODevice | None:
            return state.iodevice

        def stop(self) -> None:
            self.stopped = True

        def error(self) -> object:
            return state.audio_error

    class QMediaDevices:
        @staticmethod
        def defaultAudioInput() -> _FakeAudioDevice:
            return state.device

    class QTimer:
        def __init__(self, parent: object) -> None:
            self.parent = parent
            self.timeout = _Signal()
            self.started_ms: int | None = None
            self.single_shot = False
            state.timers.append(self)

        def setSingleShot(self, single_shot: bool) -> None:
            self.single_shot = single_shot

        def start(self, timeout_ms: int) -> None:
            self.started_ms = timeout_ms

    qt_multimedia.QAudio = QAudio
    qt_multimedia.QAudioFormat = _FakeAudioFormat
    qt_multimedia.QAudioSource = QAudioSource
    qt_multimedia.QMediaDevices = QMediaDevices
    qt_core.QTimer = QTimer
    pyqt6.QtMultimedia = qt_multimedia
    pyqt6.QtCore = qt_core

    monkeypatch.setitem(sys.modules, "PyQt6", pyqt6)
    monkeypatch.setitem(sys.modules, "PyQt6.QtMultimedia", qt_multimedia)
    monkeypatch.setitem(sys.modules, "PyQt6.QtCore", qt_core)
    return state


def _read_wav_pcm(path: Path) -> tuple[int, int, int, array[int]]:
    with wave.open(str(path), "rb") as wav_file:
        sample_rate = wav_file.getframerate()
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        samples = array("h")
        samples.frombytes(wav_file.readframes(wav_file.getnframes()))
    return sample_rate, channels, sample_width, samples


def test_qt_backend_rejects_missing_audio_input_device(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    preferred_format = _FakeAudioFormat(sample_format=_FakeAudioFormat.SampleFormat.Int16)
    _install_fake_qt(
        monkeypatch,
        preferred_format=preferred_format,
        iodevice=None,
        is_null_device=True,
    )

    with pytest.raises(RuntimeError, match="No audio input device is available."):
        _QtAudioSourceRecorderBackend(tmp_path / "learner.wav", mw=object(), parent=object())


def test_qt_backend_start_stop_writes_wav_after_timeout(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "learner.wav"
    preferred_format = _FakeAudioFormat(
        sample_format=_FakeAudioFormat.SampleFormat.Int16,
        sample_rate=10,
        channel_count=1,
    )
    iodevice = _FakeIODevice(
        struct.pack("<2h", 10, 20),
        struct.pack("<3h", 30, 40, 50),
    )
    state = _install_fake_qt(monkeypatch, preferred_format=preferred_format, iodevice=iodevice)
    completed: list[Path] = []
    failures: list[AudioRecordingError] = []
    started: list[str] = []
    backend = _QtAudioSourceRecorderBackend(output_path, mw=object(), parent=object())

    backend.start(
        on_started=lambda: started.append("started"),
        on_failed=failures.append,
    )

    assert output_path.exists() is False
    state.iodevice.readyRead.emit()
    state.iodevice.readyRead.emit()

    backend.stop(on_completed=completed.append, on_failed=failures.append)

    assert output_path.exists() is False
    assert len(state.timers) == 1
    state.timers[0].timeout.emit()

    assert started == ["started"]
    assert failures == []
    assert completed == [output_path]
    assert state.audio_sources[0].stopped is True
    sample_rate, channels, sample_width, samples = _read_wav_pcm(output_path)
    assert sample_rate == 10
    assert channels == 1
    assert sample_width == 2
    assert list(samples) == [40, 50]


def test_qt_backend_start_reports_when_audio_input_cannot_start(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    preferred_format = _FakeAudioFormat(sample_format=_FakeAudioFormat.SampleFormat.Int16)
    _install_fake_qt(monkeypatch, preferred_format=preferred_format, iodevice=None)
    failures: list[AudioRecordingError] = []
    started: list[str] = []
    backend = _QtAudioSourceRecorderBackend(tmp_path / "learner.wav", mw=object(), parent=object())

    backend.start(
        on_started=lambda: started.append("started"),
        on_failed=failures.append,
    )

    assert started == []
    assert len(failures) == 1
    assert "Unable to start audio input." in str(failures[0])


def test_qt_backend_ignores_read_ready_before_start(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    preferred_format = _FakeAudioFormat(sample_format=_FakeAudioFormat.SampleFormat.Int16)
    _install_fake_qt(monkeypatch, preferred_format=preferred_format, iodevice=_FakeIODevice())
    backend = _QtAudioSourceRecorderBackend(tmp_path / "learner.wav", mw=object(), parent=object())

    backend._on_read_ready()

    assert backend._buffer == bytearray()


def test_qt_backend_stop_reports_audio_errors_without_writing_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "learner.wav"
    preferred_format = _FakeAudioFormat(sample_format=_FakeAudioFormat.SampleFormat.Int16)
    state = _install_fake_qt(
        monkeypatch,
        preferred_format=preferred_format,
        iodevice=_FakeIODevice(struct.pack("<2h", 10, 20)),
        audio_error="device-lost",
    )
    failures: list[AudioRecordingError] = []
    completed: list[Path] = []
    backend = _QtAudioSourceRecorderBackend(output_path, mw=object(), parent=object())

    backend.start(on_started=lambda: None, on_failed=failures.append)
    state.iodevice.readyRead.emit()
    backend.stop(on_completed=completed.append, on_failed=failures.append)
    state.timers[0].timeout.emit()

    assert completed == []
    assert len(failures) == 1
    assert "Voice recording failed: device-lost" in str(failures[0])
    assert output_path.exists() is False


def test_qt_backend_stop_uses_background_writer_when_available(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "learner.wav"
    preferred_format = _FakeAudioFormat(
        sample_format=_FakeAudioFormat.SampleFormat.Int16,
        sample_rate=10,
        channel_count=1,
    )
    state = _install_fake_qt(
        monkeypatch,
        preferred_format=preferred_format,
        iodevice=_FakeIODevice(struct.pack("<4h", 10, 20, 30, 40)),
    )
    background_calls: list[bool] = []
    completed: list[Path] = []
    failures: list[AudioRecordingError] = []

    class Taskman:
        def run_in_background(self, worker, callback, *, uses_collection: bool) -> None:
            background_calls.append(uses_collection)
            worker()
            callback(_FakeFuture())

    mw = SimpleNamespace(taskman=Taskman())
    backend = _QtAudioSourceRecorderBackend(output_path, mw=mw, parent=object())

    backend.start(on_started=lambda: None, on_failed=failures.append)
    state.iodevice.readyRead.emit()
    backend.stop(on_completed=completed.append, on_failed=failures.append)
    state.timers[0].timeout.emit()

    assert background_calls == [False]
    assert failures == []
    assert completed == [output_path]


def test_qt_backend_background_write_surfaces_future_errors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "learner.wav"
    preferred_format = _FakeAudioFormat(sample_format=_FakeAudioFormat.SampleFormat.Int16)
    _install_fake_qt(monkeypatch, preferred_format=preferred_format, iodevice=_FakeIODevice())
    failures: list[AudioRecordingError] = []
    completed: list[Path] = []

    class Taskman:
        def run_in_background(self, worker, callback, *, uses_collection: bool) -> None:
            del worker, uses_collection
            callback(_FakeFuture(wave.Error("bad wav")))

    backend = _QtAudioSourceRecorderBackend(
        output_path,
        mw=SimpleNamespace(taskman=Taskman()),
        parent=object(),
    )

    backend._write_recording(on_completed=completed.append, on_failed=failures.append)

    assert completed == []
    assert len(failures) == 1
    assert "Unable to write voice recording: bad wav" in str(failures[0])


def test_qt_backend_direct_write_surfaces_disk_errors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    preferred_format = _FakeAudioFormat(sample_format=_FakeAudioFormat.SampleFormat.Int16)
    _install_fake_qt(monkeypatch, preferred_format=preferred_format, iodevice=_FakeIODevice())
    failures: list[AudioRecordingError] = []
    completed: list[Path] = []
    backend = _QtAudioSourceRecorderBackend(tmp_path / "learner.wav", mw=object(), parent=object())

    monkeypatch.setattr(backend, "_write_wav_file", lambda: (_ for _ in ()).throw(OSError("disk full")))

    backend._write_recording(on_completed=completed.append, on_failed=failures.append)

    assert completed == []
    assert len(failures) == 1
    assert "Unable to write voice recording: disk full" in str(failures[0])


def test_qt_backend_float_input_writes_pcm16_output(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "learner.wav"
    preferred_format = _FakeAudioFormat(
        sample_format=_FakeAudioFormat.SampleFormat.Float,
        sample_rate=4,
        channel_count=1,
    )
    state = _install_fake_qt(
        monkeypatch,
        preferred_format=preferred_format,
        iodevice=_FakeIODevice(struct.pack("<4f", -1.5, -0.5, 0.5, 1.5)),
        supports_int16=False,
    )
    completed: list[Path] = []
    failures: list[AudioRecordingError] = []
    monkeypatch.setattr(_QtAudioSourceRecorderBackend, "STARTUP_DELAY_SECONDS", 0.0)
    backend = _QtAudioSourceRecorderBackend(output_path, mw=object(), parent=object())

    backend.start(on_started=lambda: None, on_failed=failures.append)
    state.iodevice.readyRead.emit()
    backend.stop(on_completed=completed.append, on_failed=failures.append)
    state.timers[0].timeout.emit()

    assert failures == []
    assert completed == [output_path]
    sample_rate, channels, sample_width, samples = _read_wav_pcm(output_path)
    assert sample_rate == 4
    assert channels == 1
    assert sample_width == 2
    assert list(samples) == [-32767, -16383, 16383, 32767]


def test_convert_float32_to_int16_handles_empty_and_clamps_samples() -> None:
    assert _convert_float32_to_int16(bytearray()) == b""

    packed = _convert_float32_to_int16(bytearray(struct.pack("<4f", -2.0, -0.25, 0.25, 2.0)))
    samples = struct.unpack("<4h", packed)

    assert samples == (-32767, -8191, 8191, 32767)
