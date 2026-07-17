from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import anki_audio_quick_editor.audio_recording as audio_recording
import anki_audio_quick_editor.recorder.native_backend as native_backend
from anki_audio_quick_editor.audio_recording import (
    AudioRecordingError,
    NativeRecordingController,
    RecordingResult,
)
from anki_audio_quick_editor.recorder.native_macos import MacWavRecorderBackend


class _BackendStub:
    def __init__(self, completed_path: Path) -> None:
        self.completed_path = completed_path
        self.started = False
        self.stopped = False
        self.cancelled: list[str] = []
        self.disposed = False

    def start(self, *, on_started, on_failed) -> None:
        del on_failed
        self.started = True
        on_started()

    def stop(self, *, on_completed, on_failed) -> None:
        del on_failed
        self.stopped = True
        on_completed(self.completed_path)

    def cancel(self, reason: str) -> None:
        self.cancelled.append(reason)

    def dispose(self) -> None:
        self.disposed = True


class _DelayedBackend(_BackendStub):
    def __init__(self, completed_path: Path) -> None:
        super().__init__(completed_path)
        self.on_started = None
        self.on_completed = None
        self.on_failed = None

    def start(self, *, on_started, on_failed) -> None:
        self.started = True
        self.on_started = on_started
        self.on_failed = on_failed

    def stop(self, *, on_completed, on_failed) -> None:
        self.stopped = True
        self.on_completed = on_completed
        self.on_failed = on_failed


def test_native_recording_controller_completes_with_generation_and_duration(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "learner.wav"
    output_path.write_bytes(b"RIFFfakeWAVE")
    backend = _BackendStub(output_path)
    times = iter([10.0, 11.25])
    started: list[int] = []
    completed: list[RecordingResult] = []
    failures: list[AudioRecordingError] = []

    monkeypatch.setattr(audio_recording, "_create_native_backend", lambda *_args, **_kwargs: backend)
    monkeypatch.setattr(audio_recording.time, "monotonic", lambda: next(times))

    controller = NativeRecordingController(output_path, mw=object(), parent=object())
    controller.start(7, on_started=started.append, on_failed=failures.append)
    controller.stop(on_completed=completed.append, on_failed=failures.append)

    assert backend.started is True
    assert backend.stopped is True
    assert started == [7]
    assert failures == []
    assert completed == [
        RecordingResult(path=output_path, generation=7, duration_ms=1250)
    ]


def test_native_recording_controller_requires_active_recording_before_stop(
    tmp_path: Path,
) -> None:
    failures: list[AudioRecordingError] = []
    completed: list[RecordingResult] = []
    controller = NativeRecordingController(tmp_path / "learner.wav", mw=object(), parent=object())

    controller.stop(on_completed=completed.append, on_failed=failures.append)

    assert completed == []
    assert len(failures) == 1
    assert "No voice recording is active." in str(failures[0])


def test_native_controller_cancel_before_start_ack_suppresses_late_callbacks(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    backend = _DelayedBackend(tmp_path / "learner.wav")
    monkeypatch.setattr(audio_recording, "_create_native_backend", lambda *_args, **_kwargs: backend)
    started: list[int] = []
    failures: list[AudioRecordingError] = []
    controller = NativeRecordingController(tmp_path / "learner.wav", mw=object(), parent=object())

    controller.start(5, on_started=started.append, on_failed=failures.append)
    controller.cancel("note_changed")
    assert backend.on_started is not None
    backend.on_started()
    assert backend.on_failed is not None
    backend.on_failed(AudioRecordingError("late"))

    assert started == []
    assert failures == []
    assert backend.cancelled == ["note_changed"]


def test_native_controller_cancel_during_stop_is_idempotent_and_suppresses_completion(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "learner.wav"
    output_path.write_bytes(b"RIFFfakeWAVE")
    backend = _DelayedBackend(output_path)
    monkeypatch.setattr(audio_recording, "_create_native_backend", lambda *_args, **_kwargs: backend)
    completed: list[RecordingResult] = []
    failures: list[AudioRecordingError] = []
    controller = NativeRecordingController(output_path, mw=object(), parent=object())
    controller.start(8, on_started=lambda _generation: None, on_failed=failures.append)
    assert backend.on_started is not None
    backend.on_started()
    controller.stop(on_completed=completed.append, on_failed=failures.append)

    controller.cancel("editor_closed")
    controller.cancel("editor_closed")
    controller.dispose()
    assert backend.on_completed is not None
    backend.on_completed(output_path)

    assert completed == []
    assert failures == []
    assert backend.cancelled == ["editor_closed"]
    assert backend.disposed is True


def test_native_recording_controller_reports_backend_initialization_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    started: list[int] = []
    failures: list[AudioRecordingError] = []

    def raise_init_error(*_args, **_kwargs):
        raise RuntimeError("microphone unavailable")

    monkeypatch.setattr(audio_recording, "_create_native_backend", raise_init_error)
    controller = NativeRecordingController(tmp_path / "learner.wav", mw=object(), parent=object())
    controller.start(3, on_started=started.append, on_failed=failures.append)

    assert started == []
    assert len(failures) == 1
    assert "Unable to initialize voice recorder: microphone unavailable" in str(failures[0])


@pytest.mark.parametrize(
    ("raised_error", "message"),
    [
        (OSError("disk read failed"), "Unable to read completed recording:"),
        (AudioRecordingError("Recording produced an empty audio file."), "Recording produced an empty audio file."),
    ],
)
def test_native_recording_controller_reports_completed_recording_validation_failures(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    raised_error: Exception,
    message: str,
) -> None:
    output_path = tmp_path / "learner.wav"
    output_path.write_bytes(b"RIFFfakeWAVE")
    backend = _BackendStub(output_path)
    failures: list[AudioRecordingError] = []
    completed: list[RecordingResult] = []

    monkeypatch.setattr(audio_recording, "_create_native_backend", lambda *_args, **_kwargs: backend)
    monkeypatch.setattr(audio_recording.time, "monotonic", lambda: 10.0)

    def raise_validation_error(*_args, **_kwargs):
        raise raised_error

    monkeypatch.setattr(audio_recording, "recording_result_from_path", raise_validation_error)

    controller = NativeRecordingController(output_path, mw=object(), parent=object())
    controller.start(9, on_started=lambda _generation: None, on_failed=failures.append)
    controller.stop(on_completed=completed.append, on_failed=failures.append)

    assert completed == []
    assert len(failures) == 1
    assert message in str(failures[0])


def test_load_macos_helper_returns_helper_when_module_is_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = object()

    monkeypatch.setattr(
        native_backend,
        "import_module",
        lambda name: SimpleNamespace(macos_helper=helper) if name == "aqt._macos_helper" else None,
    )

    assert native_backend.load_macos_helper() is helper


def test_load_macos_helper_returns_none_when_module_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_missing(*_args, **_kwargs):
        raise ModuleNotFoundError("aqt._macos_helper")

    monkeypatch.setattr(native_backend, "import_module", raise_missing)

    assert native_backend.load_macos_helper() is None


def test_create_native_backend_prefers_macos_helper_on_arm64(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    helper = object()

    monkeypatch.setattr(native_backend, "load_macos_helper", lambda: helper)
    monkeypatch.setattr(native_backend.platform, "machine", lambda: "arm64")

    backend = audio_recording._create_native_backend(tmp_path / "learner.wav", mw=object(), parent=object())

    assert isinstance(backend, MacWavRecorderBackend)
    assert backend.output_path == tmp_path / "learner.wav"


def test_create_native_backend_uses_qt_backend_when_helper_is_not_selected(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    sentinel = object()

    monkeypatch.setattr(native_backend, "load_macos_helper", lambda: object())
    monkeypatch.setattr(native_backend.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(native_backend, "QtAudioSourceRecorderBackend", lambda *_args, **_kwargs: sentinel)

    backend = audio_recording._create_native_backend(tmp_path / "learner.wav", mw=object(), parent=object())

    assert backend is sentinel


def test_macos_backend_start_reports_helper_errors(
    tmp_path: Path,
) -> None:
    class FailingHelper:
        def start_wav_record(self, _path: str, _callback) -> None:
            raise RuntimeError("permission denied")

    backend = MacWavRecorderBackend(
        tmp_path / "learner.wav",
        macos_helper=FailingHelper(),
    )
    started: list[str] = []
    failures: list[AudioRecordingError] = []

    backend.start(
        on_started=lambda: started.append("started"),
        on_failed=failures.append,
    )

    assert started == []
    assert len(failures) == 1
    assert "Unable to start voice recorder: permission denied" in str(failures[0])


def test_macos_backend_start_and_stop_follow_helper_callback_state(
    tmp_path: Path,
) -> None:
    class CallbackHelper:
        def __init__(self) -> None:
            self.callback = None

        def start_wav_record(self, _path: str, callback) -> None:
            self.callback = callback

        def end_wav_record(self) -> None:
            return None

    helper = CallbackHelper()
    backend = MacWavRecorderBackend(tmp_path / "learner.wav", macos_helper=helper)
    started: list[str] = []
    completed: list[Path] = []
    failures: list[AudioRecordingError] = []

    backend.start(
        on_started=lambda: started.append("started"),
        on_failed=failures.append,
    )
    backend.stop(on_completed=completed.append, on_failed=failures.append)

    assert started == ["started"]
    assert failures == []
    assert completed == [tmp_path / "learner.wav"]


def test_macos_backend_stop_surfaces_recording_error_from_helper_callback(
    tmp_path: Path,
) -> None:
    class CallbackHelper:
        def start_wav_record(self, _path: str, callback) -> None:
            callback("microphone disconnected")

        def end_wav_record(self) -> None:
            return None

    backend = MacWavRecorderBackend(tmp_path / "learner.wav", macos_helper=CallbackHelper())
    started: list[str] = []
    completed: list[Path] = []
    failures: list[AudioRecordingError] = []

    backend.start(
        on_started=lambda: started.append("started"),
        on_failed=failures.append,
    )
    backend.stop(on_completed=completed.append, on_failed=failures.append)

    assert started == []
    assert completed == []
    assert [str(error) for error in failures] == [
        "microphone disconnected",
        "microphone disconnected",
    ]


def test_macos_backend_stop_reports_helper_shutdown_errors(
    tmp_path: Path,
) -> None:
    class FailingHelper:
        def start_wav_record(self, _path: str, _callback) -> None:
            return None

        def end_wav_record(self) -> None:
            raise OSError("stop failed")

    backend = MacWavRecorderBackend(
        tmp_path / "learner.wav",
        macos_helper=FailingHelper(),
    )
    completed: list[Path] = []
    failures: list[AudioRecordingError] = []

    backend.start(on_started=lambda: None, on_failed=failures.append)
    backend.stop(on_completed=completed.append, on_failed=failures.append)

    assert completed == []
    assert len(failures) == 1
    assert "Unable to stop voice recorder: stop failed" in str(failures[0])


def test_macos_backend_cancel_ends_once_and_removes_only_attempt_owned_output(
    tmp_path: Path,
) -> None:
    class Helper:
        def __init__(self) -> None:
            self.end_count = 0

        def start_wav_record(self, path: str, _callback) -> None:
            Path(path).write_bytes(b"partial")

        def end_wav_record(self) -> None:
            self.end_count += 1

    helper = Helper()
    output_path = tmp_path / "learner.wav"
    backend = MacWavRecorderBackend(output_path, macos_helper=helper)
    backend.start(on_started=lambda: None, on_failed=lambda _error: None)

    backend.cancel("note_changed")
    backend.cancel("note_changed")
    backend.dispose()

    assert helper.end_count == 1
    assert output_path.exists() is False


def test_macos_backend_cancel_preserves_preexisting_output(tmp_path: Path) -> None:
    class Helper:
        def start_wav_record(self, _path: str, _callback) -> None:
            return None

        def end_wav_record(self) -> None:
            return None

    output_path = tmp_path / "existing.wav"
    output_path.write_bytes(b"user-owned")
    backend = MacWavRecorderBackend(output_path, macos_helper=Helper())
    backend.start(on_started=lambda: None, on_failed=lambda _error: None)

    backend.cancel("editor_closed")

    assert output_path.read_bytes() == b"user-owned"
