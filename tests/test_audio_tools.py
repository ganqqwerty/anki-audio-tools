from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from anki_audio_quick_editor.audio_processor import (
    find_deep_filter,
    find_ffmpeg,
    find_ffprobe,
    find_rnnoise_bundle,
)
from anki_audio_quick_editor.errors import (
    MissingDeepFilterError,
    MissingFfmpegError,
    MissingRnnoiseError,
)


def test_find_ffmpeg_uses_default_path_lookup_when_unconfigured(monkeypatch) -> None:
    calls: list[str] = []

    def fake_which(name: str) -> str:
        calls.append(name)
        return "/usr/local/bin/ffmpeg"

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.shutil.which", fake_which)

    assert find_ffmpeg() == Path("/usr/local/bin/ffmpeg")
    assert calls == ["ffmpeg"]


def test_find_ffmpeg_default_override_stays_empty_string() -> None:
    audio_processor_module = importlib.import_module("anki_audio_quick_editor.audio_processor")

    assert audio_processor_module.find_ffmpeg.__defaults__ == ("",)


def test_find_ffmpeg_raises_exact_message_when_missing_and_unconfigured(monkeypatch) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.shutil.which", lambda _name: None)
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.Path",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("configured path should not be consulted")),
    )

    with pytest.raises(MissingFfmpegError) as exc_info:
        find_ffmpeg()

    assert str(exc_info.value) == (
        "Audio Quick Editor requires ffmpeg. Please install ffmpeg and make sure it is "
        "available in PATH, or configure its path in the add-on settings."
    )


def test_find_ffmpeg_prefers_existing_configured_file(tmp_path: Path) -> None:
    ffmpeg = tmp_path / "ffmpeg"
    ffmpeg.write_text("")

    assert find_ffmpeg(str(ffmpeg)) == ffmpeg


def test_find_deep_filter_uses_default_path_lookup_when_unconfigured(monkeypatch) -> None:
    calls: list[str] = []

    def fake_which(name: str) -> str:
        calls.append(name)
        return "/usr/local/bin/deep-filter"

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor._bundled_deep_filter_path", lambda: None)
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.shutil.which", fake_which)

    assert find_deep_filter() == Path("/usr/local/bin/deep-filter")
    assert calls == ["deep-filter"]


def test_find_deep_filter_uses_bundled_binary_before_path_lookup(
    tmp_path: Path,
    monkeypatch,
) -> None:
    bundled = tmp_path / "deep-filter"
    bundled.write_text("")
    calls: list[str] = []

    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor._bundled_deep_filter_path",
        lambda: bundled,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.shutil.which",
        lambda name: calls.append(name) or "/usr/local/bin/deep-filter",
    )

    assert find_deep_filter() == bundled
    assert calls == []


def test_find_deep_filter_prefers_existing_configured_file(tmp_path: Path) -> None:
    deep_filter = tmp_path / "deep-filter"
    deep_filter.write_text("")

    assert find_deep_filter(str(deep_filter)) == deep_filter


def test_find_deep_filter_raises_when_missing(monkeypatch) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor._bundled_deep_filter_path", lambda: None)
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.shutil.which", lambda _name: None)

    with pytest.raises(MissingDeepFilterError, match="DeepFilterNet.*Standard denoise.*Shorten Pauses"):
        find_deep_filter()


def test_find_rnnoise_bundle_uses_bundled_executable_when_complete(
    tmp_path: Path,
    monkeypatch,
) -> None:
    bundled_dir = tmp_path / "rnnoise-cli-macos-arm64"
    rnnoise_path = bundled_dir / "bin" / "rnnoise-cli"
    rnnoise_path.parent.mkdir(parents=True)
    rnnoise_path.write_text("")

    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.expected_bundled_rnnoise_dir",
        lambda: bundled_dir,
    )

    assert find_rnnoise_bundle() == rnnoise_path


def test_find_rnnoise_bundle_raises_when_bundle_is_incomplete(
    tmp_path: Path,
    monkeypatch,
) -> None:
    bundled_dir = tmp_path / "rnnoise-cli-macos-arm64"
    (bundled_dir / "bin").mkdir(parents=True)

    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.expected_bundled_rnnoise_dir",
        lambda: bundled_dir,
    )

    with pytest.raises(MissingRnnoiseError, match="bundled rnnoise-cli executable"):
        find_rnnoise_bundle()


def test_find_ffprobe_prefers_sibling_binary(tmp_path: Path, monkeypatch) -> None:
    ffmpeg = tmp_path / "ffmpeg"
    ffprobe = tmp_path / "ffprobe"
    ffmpeg.write_text("")
    ffprobe.write_text("")
    called = False

    def fake_which(_name: str) -> str:
        nonlocal called
        called = True
        return "/usr/local/bin/ffprobe"

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.shutil.which", fake_which)

    assert find_ffprobe(ffmpeg) == ffprobe
    assert called is False


def test_find_ffprobe_falls_back_to_path_lookup(monkeypatch, tmp_path: Path) -> None:
    calls: list[str] = []

    def fake_which(name: str) -> str:
        calls.append(name)
        return "/usr/local/bin/ffprobe"

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.shutil.which", fake_which)

    assert find_ffprobe(tmp_path / "ffmpeg") == Path("/usr/local/bin/ffprobe")
    assert calls == ["ffprobe"]


def test_find_ffprobe_raises_when_no_binary_available(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.shutil.which", lambda _name: None)

    with pytest.raises(MissingFfmpegError) as exc_info:
        find_ffprobe(tmp_path / "ffmpeg")

    assert str(exc_info.value) == "Audio Quick Editor requires ffprobe alongside ffmpeg to inspect audio duration."

