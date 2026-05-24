"""Bundled-tool runtime diagnostics tests."""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.diagnostics import (
    build_dpdfnet_health,
    build_rnnoise_health,
    build_spleeter_health,
)


def test_rnnoise_health_reports_missing_bundle_at_expected_path(monkeypatch, tmp_path: Path) -> None:
    expected_dir = tmp_path / "rnnoise-cli-macos-arm64"
    expected_path = expected_dir / "rnnoise-cli"
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.expected_bundled_tool_path",
        lambda tool_name: expected_path if tool_name == "rnnoise-cli" else None,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_rnnoise_bundle",
        MagicMock(side_effect=RuntimeError("rnnoise bundle is incomplete")),
    )
    run_calls: list[object] = []
    monkeypatch.setattr("anki_audio_quick_editor.diagnostics.subprocess.run", lambda *args, **kwargs: run_calls.append((args, kwargs)))

    health = build_rnnoise_health()
    assert health == {
        "available": False,
        "path": str(expected_path),
        "source": "bundled",
        "version": "",
        "error": "rnnoise bundle is incomplete",
    }
    assert run_calls == []


def test_rnnoise_health_reports_successful_version(monkeypatch) -> None:
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.expected_bundled_tool_path",
        lambda tool_name: Path("/addon/bin/macos-arm64/rnnoise-cli") if tool_name == "rnnoise-cli" else None,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_rnnoise_bundle",
        lambda: Path("/addon/bin/macos-arm64/rnnoise-cli"),
    )

    def fake_run(cmd, capture_output: bool, text: bool, check: bool, timeout: int) -> SimpleNamespace:
        assert cmd == ["/addon/bin/macos-arm64/rnnoise-cli", "--version"]
        return SimpleNamespace(returncode=0, stdout="rnnoise-cli 0.2\n", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.diagnostics.subprocess.run", fake_run)
    assert build_rnnoise_health() == {
        "available": True,
        "path": "/addon/bin/macos-arm64/rnnoise-cli",
        "source": "bundled",
        "version": "rnnoise-cli 0.2",
        "error": "",
    }


def test_rnnoise_health_reports_timeout_and_os_error(monkeypatch) -> None:
    rnnoise_path = Path("/addon/bin/rnnoise-cli")
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.expected_bundled_tool_path",
        lambda tool_name: rnnoise_path if tool_name == "rnnoise-cli" else None,
    )
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_rnnoise_bundle", lambda: rnnoise_path)

    def timeout_run(cmd, *_args, **_kwargs) -> None:
        raise subprocess.TimeoutExpired(cmd, timeout=10)

    monkeypatch.setattr("anki_audio_quick_editor.diagnostics.subprocess.run", timeout_run)
    assert build_rnnoise_health() == {
        "available": False,
        "path": str(rnnoise_path),
        "source": "bundled",
        "version": "",
        "error": "rnnoise-cli --version timed out.",
    }

    monkeypatch.setattr("anki_audio_quick_editor.diagnostics.subprocess.run", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("permission denied")))
    health = build_rnnoise_health()
    assert health["available"] is False
    assert health["path"] == str(rnnoise_path)
    assert health["source"] == "bundled"
    assert health["version"] == ""
    assert "permission denied" in health["error"]


def test_rnnoise_health_reports_nonzero_version_output(monkeypatch) -> None:
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.expected_bundled_tool_path",
        lambda tool_name: Path("/addon/bin/macos-arm64/rnnoise-cli") if tool_name == "rnnoise-cli" else None,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_rnnoise_bundle",
        lambda: Path("/addon/bin/macos-arm64/rnnoise-cli"),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.diagnostics.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=2, stdout="", stderr="invalid arch"),
    )
    assert build_rnnoise_health() == {
        "available": False,
        "path": "/addon/bin/macos-arm64/rnnoise-cli",
        "source": "bundled",
        "version": "",
        "error": "invalid arch",
    }


def test_dpdfnet_health_reports_missing_bundle_at_expected_path(monkeypatch) -> None:
    expected_path = Path("/addon/bin/macos-arm64/dpdfnet")
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.expected_bundled_tool_path",
        lambda tool_name: expected_path if tool_name == "dpdfnet" else None,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_dpdfnet_bundle",
        MagicMock(side_effect=RuntimeError("dpdfnet bundle is incomplete")),
    )
    run_calls: list[object] = []
    monkeypatch.setattr("anki_audio_quick_editor.diagnostics.subprocess.run", lambda *args, **kwargs: run_calls.append((args, kwargs)))

    health = build_dpdfnet_health()
    assert health == {
        "available": False,
        "path": str(expected_path),
        "source": "bundled",
        "version": "",
        "error": "dpdfnet bundle is incomplete",
    }
    assert run_calls == []


def test_dpdfnet_health_reports_successful_version(monkeypatch) -> None:
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.expected_bundled_tool_path",
        lambda tool_name: Path("/addon/bin/macos-arm64/dpdfnet") if tool_name == "dpdfnet" else None,
    )
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_dpdfnet_bundle", lambda: Path("/addon/bin/macos-arm64/dpdfnet"))

    def fake_run(cmd, capture_output: bool, text: bool, check: bool, timeout: int) -> SimpleNamespace:
        assert cmd == ["/addon/bin/macos-arm64/dpdfnet", "--version"]
        return SimpleNamespace(returncode=0, stdout="dpdfnet-lite 0.1.0\n", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.diagnostics.subprocess.run", fake_run)
    assert build_dpdfnet_health() == {
        "available": True,
        "path": "/addon/bin/macos-arm64/dpdfnet",
        "source": "bundled",
        "version": "dpdfnet-lite 0.1.0",
        "error": "",
    }


def test_dpdfnet_health_reports_timeout_and_os_error(monkeypatch) -> None:
    dpdfnet_path = Path("/addon/bin/macos-arm64/dpdfnet")
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.expected_bundled_tool_path",
        lambda tool_name: dpdfnet_path if tool_name == "dpdfnet" else None,
    )
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_dpdfnet_bundle", lambda: dpdfnet_path)

    def timeout_run(cmd, *_args, **_kwargs) -> None:
        raise subprocess.TimeoutExpired(cmd, timeout=10)

    monkeypatch.setattr("anki_audio_quick_editor.diagnostics.subprocess.run", timeout_run)
    assert build_dpdfnet_health() == {
        "available": False,
        "path": str(dpdfnet_path),
        "source": "bundled",
        "version": "",
        "error": "dpdfnet --version timed out.",
    }

    monkeypatch.setattr("anki_audio_quick_editor.diagnostics.subprocess.run", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("permission denied")))
    health = build_dpdfnet_health()
    assert health["available"] is False
    assert health["path"] == str(dpdfnet_path)
    assert health["source"] == "bundled"
    assert health["version"] == ""
    assert "permission denied" in health["error"]


def test_dpdfnet_health_reports_nonzero_version_output(monkeypatch) -> None:
    dpdfnet_path = Path("/addon/bin/macos-arm64/dpdfnet")
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.expected_bundled_tool_path",
        lambda tool_name: dpdfnet_path if tool_name == "dpdfnet" else None,
    )
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_dpdfnet_bundle", lambda: dpdfnet_path)
    monkeypatch.setattr(
        "anki_audio_quick_editor.diagnostics.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=2, stdout="", stderr="invalid arch"),
    )
    assert build_dpdfnet_health() == {
        "available": False,
        "path": str(dpdfnet_path),
        "source": "bundled",
        "version": "",
        "error": "invalid arch",
    }


def test_spleeter_health_reports_missing_bundle_at_expected_path(monkeypatch, tmp_path: Path) -> None:
    expected_path = tmp_path / "macos-arm64" / "sherpa-spleeter"
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.expected_bundled_tool_path",
        lambda tool_name: expected_path if tool_name == "sherpa-spleeter" else None,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_spleeter_bundle",
        MagicMock(side_effect=RuntimeError("sherpa spleeter bundle is incomplete")),
    )
    run_calls: list[object] = []
    monkeypatch.setattr("anki_audio_quick_editor.diagnostics.subprocess.run", lambda *args, **kwargs: run_calls.append((args, kwargs)))

    health = build_spleeter_health()
    assert health == {
        "available": False,
        "path": str(expected_path),
        "source": "bundled",
        "version": "",
        "error": "sherpa spleeter bundle is incomplete",
    }
    assert run_calls == []


def test_spleeter_health_reports_successful_help_probe(monkeypatch) -> None:
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.expected_bundled_tool_path",
        lambda tool_name: Path("/addon/bin/macos-arm64/sherpa-spleeter") if tool_name == "sherpa-spleeter" else None,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_spleeter_bundle",
        lambda: (
            Path("/addon/bin/macos-arm64/sherpa-spleeter"),
            Path("/addon/bin/models/spleeter-2stems-fp16/vocals.fp16.onnx"),
            Path("/addon/bin/models/spleeter-2stems-fp16/accompaniment.fp16.onnx"),
        ),
    )

    def fake_run(cmd, capture_output: bool, text: bool, check: bool, timeout: int) -> SimpleNamespace:
        assert cmd == ["/addon/bin/macos-arm64/sherpa-spleeter", "--help"]
        return SimpleNamespace(returncode=0, stdout="Non-streaming source separation with sherpa-onnx.\n", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.diagnostics.subprocess.run", fake_run)
    assert build_spleeter_health() == {
        "available": True,
        "path": "/addon/bin/macos-arm64/sherpa-spleeter",
        "source": "bundled",
        "version": "Non-streaming source separation with sherpa-onnx.",
        "error": "",
    }
