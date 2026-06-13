from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import anki_audio_quick_editor.audio_recording as audio_recording
from anki_audio_quick_editor.audio_recording import (
    AudioRecordingError,
    NativeRecordingController,
    RecordingResult,
)


class _BackendStub:
    def __init__(self, completed_path: Path) -> None:
        self.completed_path = completed_path
        self.started = False
        self.stopped = False

    def start(self, *, on_started, on_failed) -> None:
        del on_failed
        self.started = True
        on_started()

    def stop(self, *, on_completed, on_failed) -> None:
        del on_failed
        self.stopped = True
        on_completed(self.completed_path)


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
        audio_recording,
        "import_module",
        lambda name: SimpleNamespace(macos_helper=helper) if name == "aqt._macos_helper" else None,
    )

    assert audio_recording._load_macos_helper() is helper


def test_load_macos_helper_returns_none_when_module_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_missing(*_args, **_kwargs):
        raise ModuleNotFoundError("aqt._macos_helper")

    monkeypatch.setattr(audio_recording, "import_module", raise_missing)

    assert audio_recording._load_macos_helper() is None


def test_create_native_backend_prefers_macos_helper_on_arm64(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    helper = object()

    monkeypatch.setattr(audio_recording, "_load_macos_helper", lambda: helper)
    monkeypatch.setattr(audio_recording.platform, "machine", lambda: "arm64")

    backend = audio_recording._create_native_backend(tmp_path / "learner.wav", mw=object(), parent=object())

    assert isinstance(backend, audio_recording._MacWavRecorderBackend)
    assert backend.output_path == tmp_path / "learner.wav"


def test_create_native_backend_uses_qt_backend_when_helper_is_not_selected(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    sentinel = object()

    monkeypatch.setattr(audio_recording, "_load_macos_helper", lambda: object())
    monkeypatch.setattr(audio_recording.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(audio_recording, "_QtAudioSourceRecorderBackend", lambda *_args, **_kwargs: sentinel)

    backend = audio_recording._create_native_backend(tmp_path / "learner.wav", mw=object(), parent=object())

    assert backend is sentinel


def test_macos_backend_start_reports_helper_errors(
    tmp_path: Path,
) -> None:
    class FailingHelper:
        def start_wav_record(self, _path: str, _callback) -> None:
            raise RuntimeError("permission denied")

    backend = audio_recording._MacWavRecorderBackend(
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
    backend = audio_recording._MacWavRecorderBackend(tmp_path / "learner.wav", macos_helper=helper)
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

    backend = audio_recording._MacWavRecorderBackend(tmp_path / "learner.wav", macos_helper=CallbackHelper())
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

    backend = audio_recording._MacWavRecorderBackend(
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
