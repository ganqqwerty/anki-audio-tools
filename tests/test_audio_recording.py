from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

from anki_audio_quick_editor.audio_recording import (
    AudioRecordingError,
    RecordingController,
    RecordingResult,
    recording_result_from_path,
)


class _FakeRecordingController:
    def __init__(
        self,
        output_path: Path,
        *,
        start_error: AudioRecordingError | None = None,
        stop_error: AudioRecordingError | None = None,
    ) -> None:
        self.output_path = output_path
        self.start_error = start_error
        self.stop_error = stop_error
        self.generation: int | None = None

    def start(
        self,
        generation: int,
        *,
        on_started: object,
        on_failed: object,
    ) -> None:
        self.generation = generation
        if self.start_error is not None:
            if callable(on_failed):
                on_failed(self.start_error)
            return
        if callable(on_started):
            on_started(generation)

    def stop(self, *, on_completed: object, on_failed: object) -> None:
        if self.stop_error is not None:
            if callable(on_failed):
                on_failed(self.stop_error)
            return
        if self.generation is None:
            raise AssertionError("fake recorder stopped before start")
        if callable(on_completed):
            on_completed(
                recording_result_from_path(self.output_path, generation=self.generation)
            )


def test_fake_recording_controller_completes_with_generation_and_wav_path(
    tmp_path: Path,
) -> None:
    wav_path = tmp_path / "learner.wav"
    wav_path.write_bytes(b"RIFFfakeWAVE")
    recorder = _FakeRecordingController(wav_path)
    started: list[int] = []
    completed: list[RecordingResult] = []
    failures: list[AudioRecordingError] = []

    assert isinstance(recorder, RecordingController)

    recorder.start(42, on_started=started.append, on_failed=failures.append)
    recorder.stop(on_completed=completed.append, on_failed=failures.append)

    assert started == [42]
    assert failures == []
    assert completed == [
        RecordingResult(path=wav_path, generation=42, duration_ms=None)
    ]


def test_fake_recording_start_failure_surfaces_typed_error(tmp_path: Path) -> None:
    error = AudioRecordingError("microphone unavailable")
    recorder = _FakeRecordingController(tmp_path / "missing.wav", start_error=error)
    started: list[int] = []
    failures: list[AudioRecordingError] = []

    recorder.start(7, on_started=started.append, on_failed=failures.append)

    assert started == []
    assert failures == [error]


def test_fake_recording_stop_failure_surfaces_typed_error(tmp_path: Path) -> None:
    wav_path = tmp_path / "learner.wav"
    wav_path.write_bytes(b"RIFFfakeWAVE")
    error = AudioRecordingError("recording backend failed")
    recorder = _FakeRecordingController(wav_path, stop_error=error)
    completed: list[RecordingResult] = []
    failures: list[AudioRecordingError] = []

    recorder.start(8, on_started=lambda _generation: None, on_failed=failures.append)
    recorder.stop(on_completed=completed.append, on_failed=failures.append)

    assert completed == []
    assert failures == [error]


def test_recording_result_from_path_rejects_missing_or_empty_files(
    tmp_path: Path,
) -> None:
    missing_path = tmp_path / "missing.wav"
    with pytest.raises(AudioRecordingError, match="did not produce"):
        recording_result_from_path(missing_path, generation=1)

    empty_path = tmp_path / "empty.wav"
    empty_path.touch()
    with pytest.raises(AudioRecordingError, match="empty"):
        recording_result_from_path(empty_path, generation=1)


def test_recording_result_from_path_includes_elapsed_duration(tmp_path: Path) -> None:
    wav_path = tmp_path / "learner.wav"
    wav_path.write_bytes(b"RIFFfakeWAVE")

    result = recording_result_from_path(
        wav_path,
        generation=3,
        started_at=10.0,
        stopped_at=11.25,
    )

    assert result == RecordingResult(path=wav_path, generation=3, duration_ms=1250)


def test_audio_recording_import_does_not_load_qt_multimedia_or_macos_helper() -> None:
    sys.modules.pop("anki_audio_quick_editor.audio_recording", None)
    sys.modules.pop("PyQt6.QtMultimedia", None)
    sys.modules.pop("aqt._macos_helper", None)

    importlib.import_module("anki_audio_quick_editor.audio_recording")

    assert "PyQt6.QtMultimedia" not in sys.modules
    assert "aqt._macos_helper" not in sys.modules
