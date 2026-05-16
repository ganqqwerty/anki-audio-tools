"""Tests for import-safe runtime diagnostics."""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

from anki_audio_quick_editor.diagnostics import build_deep_filter_health
from anki_audio_quick_editor.errors import MissingDeepFilterError


def test_deep_filter_health_reports_missing_configured_executable(monkeypatch) -> None:
    def fake_find_deep_filter(configured_path: str) -> Path:
        assert configured_path == "/missing/deep filter"
        raise MissingDeepFilterError("deep-filter is missing")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_deep_filter", fake_find_deep_filter)
    run_calls: list[object] = []
    monkeypatch.setattr("anki_audio_quick_editor.diagnostics.subprocess.run", lambda *args, **kwargs: run_calls.append((args, kwargs)))

    health = build_deep_filter_health({"deep_filter_path": "/missing/deep filter"})

    assert health == {
        "available": False,
        "path": "/missing/deep filter",
        "version": "",
        "error": "deep-filter is missing",
    }
    assert run_calls == []


def test_deep_filter_health_reports_os_error(monkeypatch) -> None:
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_deep_filter",
        lambda _configured_path: Path("/tools/deep-filter"),
    )

    def fake_run(*_args, **_kwargs) -> None:
        raise OSError(28, "No space left on device")

    monkeypatch.setattr("anki_audio_quick_editor.diagnostics.subprocess.run", fake_run)

    health = build_deep_filter_health({})

    assert health["available"] is False
    assert health["path"] == "/tools/deep-filter"
    assert health["version"] == ""
    assert "No space left on device" in health["error"]


def test_deep_filter_health_reports_timeout(monkeypatch) -> None:
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_deep_filter",
        lambda _configured_path: Path("/tools/deep-filter"),
    )

    def fake_run(cmd, *_args, **_kwargs) -> None:
        raise subprocess.TimeoutExpired(cmd, timeout=10)

    monkeypatch.setattr("anki_audio_quick_editor.diagnostics.subprocess.run", fake_run)

    health = build_deep_filter_health({})

    assert health == {
        "available": False,
        "path": "/tools/deep-filter",
        "version": "",
        "error": "deep-filter --version timed out.",
    }


def test_deep_filter_health_reports_nonzero_version_stderr_with_problematic_filename(monkeypatch) -> None:
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_deep_filter",
        lambda _configured_path: Path("/tools/deep-filter"),
    )

    def fake_run(cmd, capture_output: bool, text: bool, check: bool, timeout: int) -> SimpleNamespace:
        assert cmd == ["/tools/deep-filter", "--version"]
        assert capture_output is True
        assert text is True
        assert check is False
        assert timeout == 10
        return SimpleNamespace(
            returncode=2,
            stdout="",
            stderr="could not inspect 'bad name [final] #1.wav'",
        )

    monkeypatch.setattr("anki_audio_quick_editor.diagnostics.subprocess.run", fake_run)

    health = build_deep_filter_health({})

    assert health == {
        "available": False,
        "path": "/tools/deep-filter",
        "version": "",
        "error": "could not inspect 'bad name [final] #1.wav'",
    }
