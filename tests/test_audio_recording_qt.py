from __future__ import annotations

import struct
import wave
from pathlib import Path
from types import SimpleNamespace

import pytest

from anki_audio_quick_editor.audio_recording import (
    AudioRecordingError,
    _convert_float32_to_int16,
    _QtAudioSourceRecorderBackend,
)
from tests.audio_recording_qt_fixtures import (
    FakeAudioFormat,
    FakeFuture,
    FakeIODevice,
    install_fake_qt,
    read_wav_pcm,
)


def test_qt_backend_rejects_missing_audio_input_device(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    preferred_format = FakeAudioFormat(sample_format=FakeAudioFormat.SampleFormat.Int16)
    install_fake_qt(
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
    preferred_format = FakeAudioFormat(
        sample_format=FakeAudioFormat.SampleFormat.Int16,
        sample_rate=10,
        channel_count=1,
    )
    iodevice = FakeIODevice(
        struct.pack("<2h", 10, 20),
        struct.pack("<3h", 30, 40, 50),
    )
    state = install_fake_qt(monkeypatch, preferred_format=preferred_format, iodevice=iodevice)
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
    sample_rate, channels, sample_width, samples = read_wav_pcm(output_path)
    assert sample_rate == 10
    assert channels == 1
    assert sample_width == 2
    assert list(samples) == [40, 50]


def test_qt_backend_start_reports_when_audio_input_cannot_start(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    preferred_format = FakeAudioFormat(sample_format=FakeAudioFormat.SampleFormat.Int16)
    install_fake_qt(monkeypatch, preferred_format=preferred_format, iodevice=None)
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
    preferred_format = FakeAudioFormat(sample_format=FakeAudioFormat.SampleFormat.Int16)
    install_fake_qt(monkeypatch, preferred_format=preferred_format, iodevice=FakeIODevice())
    backend = _QtAudioSourceRecorderBackend(tmp_path / "learner.wav", mw=object(), parent=object())

    backend._on_read_ready()

    assert backend._buffer == bytearray()


def test_qt_backend_stop_reports_audio_errors_without_writing_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "learner.wav"
    preferred_format = FakeAudioFormat(sample_format=FakeAudioFormat.SampleFormat.Int16)
    state = install_fake_qt(
        monkeypatch,
        preferred_format=preferred_format,
        iodevice=FakeIODevice(struct.pack("<2h", 10, 20)),
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
    preferred_format = FakeAudioFormat(
        sample_format=FakeAudioFormat.SampleFormat.Int16,
        sample_rate=10,
        channel_count=1,
    )
    state = install_fake_qt(
        monkeypatch,
        preferred_format=preferred_format,
        iodevice=FakeIODevice(struct.pack("<4h", 10, 20, 30, 40)),
    )
    background_calls: list[bool] = []
    completed: list[Path] = []
    failures: list[AudioRecordingError] = []

    class Taskman:
        def run_in_background(self, worker, callback, *, uses_collection: bool) -> None:
            background_calls.append(uses_collection)
            worker()
            callback(FakeFuture())

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
    preferred_format = FakeAudioFormat(sample_format=FakeAudioFormat.SampleFormat.Int16)
    install_fake_qt(monkeypatch, preferred_format=preferred_format, iodevice=FakeIODevice())
    failures: list[AudioRecordingError] = []
    completed: list[Path] = []

    class Taskman:
        def run_in_background(self, worker, callback, *, uses_collection: bool) -> None:
            del worker, uses_collection
            callback(FakeFuture(wave.Error("bad wav")))

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
    preferred_format = FakeAudioFormat(sample_format=FakeAudioFormat.SampleFormat.Int16)
    install_fake_qt(monkeypatch, preferred_format=preferred_format, iodevice=FakeIODevice())
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
    preferred_format = FakeAudioFormat(
        sample_format=FakeAudioFormat.SampleFormat.Float,
        sample_rate=4,
        channel_count=1,
    )
    state = install_fake_qt(
        monkeypatch,
        preferred_format=preferred_format,
        iodevice=FakeIODevice(struct.pack("<4f", -1.5, -0.5, 0.5, 1.5)),
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
    sample_rate, channels, sample_width, samples = read_wav_pcm(output_path)
    assert sample_rate == 4
    assert channels == 1
    assert sample_width == 2
    assert list(samples) == [-32767, -16383, 16383, 32767]


def test_convert_float32_to_int16_handles_empty_and_clamps_samples() -> None:
    assert _convert_float32_to_int16(bytearray()) == b""

    packed = _convert_float32_to_int16(bytearray(struct.pack("<4f", -2.0, -0.25, 0.25, 2.0)))
    samples = struct.unpack("<4h", packed)

    assert samples == (-32767, -8191, 8191, 32767)
