"""Tests for external command diagnostics."""

from __future__ import annotations

import json
import subprocess

import pytest

from anki_audio_quick_editor import diagnostics_runtime
from anki_audio_quick_editor.audio_external import (
    _external_command_run_kwargs,
    _render_external_error_message,
    _run_external_command,
    probe_duration_ms,
)
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.errors import AudioProcessingError


@pytest.fixture(autouse=True)
def _reset_diagnostics() -> None:
    diagnostics_runtime.reset_for_tests()
    yield
    diagnostics_runtime.reset_for_tests()


def _jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_external_command_run_kwargs_hide_windows_console_when_debug_disabled(monkeypatch) -> None:
    diagnostics_runtime.set_debug_enabled(False)
    monkeypatch.setattr("anki_audio_quick_editor.audio_external._is_windows", lambda: True)
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_external.subprocess.CREATE_NO_WINDOW",
        0x08000000,
        raising=False,
    )

    assert _external_command_run_kwargs() == {"creationflags": 0x08000000}


def test_external_command_run_kwargs_keep_default_windows_behavior_in_debug(monkeypatch) -> None:
    diagnostics_runtime.set_debug_enabled(True)
    monkeypatch.setattr("anki_audio_quick_editor.audio_external._is_windows", lambda: True)
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_external.subprocess.CREATE_NO_WINDOW",
        0x08000000,
        raising=False,
    )

    assert _external_command_run_kwargs() == {}


def test_external_command_run_kwargs_omit_flags_on_non_windows(monkeypatch) -> None:
    diagnostics_runtime.set_debug_enabled(False)
    monkeypatch.setattr("anki_audio_quick_editor.audio_external._is_windows", lambda: False)

    assert _external_command_run_kwargs() == {}


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


def test_external_command_forwards_window_visibility_kwargs(tmp_path, monkeypatch) -> None:
    diagnostics_runtime.configure_runtime(tmp_path, debug_enabled=False)
    run_kwargs: list[dict[str, object]] = []
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_external._external_command_run_kwargs",
        lambda: {"creationflags": 0x08000000},
    )

    def fake_run(
        _cmd: list[str],
        *,
        capture_output: bool,
        text: bool,
        check: bool,
        **kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        assert capture_output is True
        assert text is True
        assert check is False
        run_kwargs.append(kwargs)
        return subprocess.CompletedProcess(["ffmpeg"], 0, stdout="ok", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_external.subprocess.run", fake_run)

    _run_external_command(("ffmpeg", "-version"), "launch failed")

    assert run_kwargs == [{"creationflags": 0x08000000}]


def test_external_command_merges_environment_overrides(tmp_path, monkeypatch) -> None:
    diagnostics_runtime.configure_runtime(tmp_path, debug_enabled=True)
    run_kwargs: list[dict[str, object]] = []

    def fake_run(
        _cmd: list[str],
        *,
        capture_output: bool,
        text: bool,
        check: bool,
        **kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        assert capture_output is True
        assert text is True
        assert check is False
        run_kwargs.append(kwargs)
        return subprocess.CompletedProcess(["dpdfnet"], 0, stdout="ok", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_external.subprocess.run", fake_run)

    _run_external_command(("dpdfnet", "--version"), "launch failed", env={"DPDFNET_FFMPEG": "/bin/ffmpeg"})

    assert run_kwargs
    env = run_kwargs[0]["env"]
    assert isinstance(env, dict)
    assert env["DPDFNET_FFMPEG"] == "/bin/ffmpeg"


def test_probe_duration_forwards_window_visibility_kwargs(tmp_path, monkeypatch) -> None:
    diagnostics_runtime.configure_runtime(tmp_path, debug_enabled=False)
    run_kwargs: list[dict[str, object]] = []
    monkeypatch.setattr("anki_audio_quick_editor.audio_external.find_ffmpeg", lambda _path: tmp_path / "ffmpeg")
    monkeypatch.setattr("anki_audio_quick_editor.audio_external.find_ffprobe", lambda _path: tmp_path / "ffprobe")
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_external._external_command_run_kwargs",
        lambda: {"creationflags": 0x08000000},
    )

    def fake_run(
        _cmd: list[str],
        *,
        capture_output: bool,
        text: bool,
        check: bool,
        **kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        assert capture_output is True
        assert text is True
        assert check is False
        run_kwargs.append(kwargs)
        return subprocess.CompletedProcess(
            ["ffprobe"],
            0,
            stdout='{"format":{"duration":"1.25"}}',
            stderr="",
        )

    monkeypatch.setattr("anki_audio_quick_editor.audio_external.subprocess.run", fake_run)

    assert probe_duration_ms(tmp_path / "clip.wav", AudioProcessingConfig()) == 1250
    assert run_kwargs == [{"creationflags": 0x08000000}]


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


def test_render_external_error_message_appends_ffmpeg_feature_guidance() -> None:
    result = subprocess.CompletedProcess(
        ["/tools/ffmpeg", "-i", "clip.wav"],
        1,
        stdout="",
        stderr="Unknown encoder 'libmp3lame'",
    )

    message = _render_external_error_message(result, "Audio processing failed.")

    assert "Unknown encoder 'libmp3lame'" in message
    assert "does not include the codec, encoder, decoder" in message
    assert "ffmpeg" in message


def test_probe_duration_ms_uses_guided_ffprobe_errors(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_external.find_ffmpeg",
        lambda _path: tmp_path / "ffmpeg",
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_external.find_ffprobe",
        lambda _path: tmp_path / "ffprobe",
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_external.subprocess.run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            [str(tmp_path / "ffprobe")],
            1,
            stdout="",
            stderr="Invalid data found when processing input",
        ),
    )

    with pytest.raises(AudioProcessingError) as exc_info:
        probe_duration_ms(tmp_path / "clip.wav", AudioProcessingConfig())

    assert "Invalid data found when processing input" in str(exc_info.value)
    assert "could not read or write this audio" in str(exc_info.value)
