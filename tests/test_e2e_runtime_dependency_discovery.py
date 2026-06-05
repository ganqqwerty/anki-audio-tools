from __future__ import annotations

from pathlib import Path

from e2e import conftest as e2e_conftest


class _FakeAudioConfig:
    def __init__(self, *, ffmpeg_path: str) -> None:
        self.ffmpeg_path = ffmpeg_path


def test_e2e_default_config_leaves_ffmpeg_unpinned_for_runtime_resolution() -> None:
    assert e2e_conftest._default_config()["ffmpeg_path"] == ""


def test_e2e_ffmpeg_config_uses_runtime_aware_addon_helpers(monkeypatch, tmp_path: Path) -> None:
    ffmpeg = tmp_path / "user_files" / "runtime" / "manifest" / "windows-x86_64" / "ffmpeg.exe"
    ffprobe = ffmpeg.with_name("ffprobe.exe")
    calls: list[tuple[str, object]] = []

    class FakeAudioProcessor:
        @staticmethod
        def find_ffmpeg(configured_path: str) -> Path:
            calls.append(("find_ffmpeg", configured_path))
            return ffmpeg

        @staticmethod
        def find_ffprobe(ffmpeg_path: Path) -> Path:
            calls.append(("find_ffprobe", ffmpeg_path))
            return ffprobe

    monkeypatch.delenv("AQE_FFMPEG_PATH", raising=False)
    monkeypatch.delenv("FFMPEG_PATH", raising=False)

    config = e2e_conftest._runtime_ffmpeg_config(FakeAudioProcessor, _FakeAudioConfig)

    assert config.ffmpeg_path == str(ffmpeg)
    assert calls == [("find_ffmpeg", ""), ("find_ffprobe", ffmpeg)]


def test_e2e_ffmpeg_config_forwards_explicit_override(monkeypatch, tmp_path: Path) -> None:
    configured = tmp_path / "configured" / "ffmpeg.exe"
    calls: list[str] = []

    class FakeAudioProcessor:
        @staticmethod
        def find_ffmpeg(configured_path: str) -> Path:
            calls.append(configured_path)
            return configured

        @staticmethod
        def find_ffprobe(ffmpeg_path: Path) -> Path:
            return ffmpeg_path.with_name("ffprobe.exe")

    monkeypatch.setenv("AQE_FFMPEG_PATH", str(configured))
    monkeypatch.delenv("FFMPEG_PATH", raising=False)

    config = e2e_conftest._runtime_ffmpeg_config(FakeAudioProcessor, _FakeAudioConfig)

    assert config.ffmpeg_path == str(configured)
    assert calls == [str(configured)]
