"""Tests for external command diagnostics."""

from __future__ import annotations

import json
import subprocess

import pytest

from anki_audio_quick_editor import diagnostics_runtime
from anki_audio_quick_editor.audio_external import _run_external_command
from anki_audio_quick_editor.errors import AudioProcessingError


@pytest.fixture(autouse=True)
def _reset_diagnostics() -> None:
    diagnostics_runtime.reset_for_tests()
    yield
    diagnostics_runtime.reset_for_tests()


def _jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_external_command_success_records_duration_and_returncode(tmp_path, monkeypatch) -> None:
    diagnostics_runtime.configure_runtime(tmp_path, debug_enabled=True)

    def fake_run(*_args, **_kwargs):
        return subprocess.CompletedProcess(["ffmpeg"], 0, stdout="ok", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_external.subprocess.run", fake_run)

    result = _run_external_command(("ffmpeg", "-version"), "launch failed")

    assert result.returncode == 0
    events = _jsonl(tmp_path / "anki_audio_quick_editor_events.jsonl")
    assert events[-1]["event"] == "external.command.finished"
    assert events[-1]["context"]["returncode"] == 0
    assert events[-1]["context"]["stdout"] == "ok"


def test_external_command_nonzero_records_stderr_tail(tmp_path, monkeypatch) -> None:
    diagnostics_runtime.configure_runtime(tmp_path, debug_enabled=True)

    def fake_run(*_args, **_kwargs):
        return subprocess.CompletedProcess(["ffmpeg"], 2, stdout="", stderr="bad input")

    monkeypatch.setattr("anki_audio_quick_editor.audio_external.subprocess.run", fake_run)

    result = _run_external_command(("ffmpeg", "-i", "clip.mp3"), "launch failed")

    assert result.returncode == 2
    events = _jsonl(tmp_path / "anki_audio_quick_editor_events.jsonl")
    assert events[-1]["level"] == "error"
    assert events[-1]["context"]["stderr"] == "bad input"


def test_external_command_launch_error_records_exception(tmp_path, monkeypatch) -> None:
    diagnostics_runtime.configure_runtime(tmp_path, debug_enabled=True)

    def fake_run(*_args, **_kwargs):
        raise OSError("permission denied")

    monkeypatch.setattr("anki_audio_quick_editor.audio_external.subprocess.run", fake_run)

    with pytest.raises(AudioProcessingError, match="permission denied"):
        _run_external_command(("ffmpeg", "-version"), "Could not start ffmpeg.")

    events = _jsonl(tmp_path / "anki_audio_quick_editor_events.jsonl")
    assert events[-1]["event"] == "external.command.launch_failed"
    assert events[-1]["context"]["launch_error"] == "permission denied"
