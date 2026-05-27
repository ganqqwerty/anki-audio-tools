from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from anki_audio_quick_editor.audio_processor import (
    bundled_tool_path,
    current_platform_key,
    find_deep_filter,
    find_ffmpeg,
    find_ffprobe,
    find_rnnoise_bundle,
    find_silero_vad_bundle,
    find_spleeter_bundle,
)
from anki_audio_quick_editor.errors import (
    MissingDeepFilterError,
    MissingFfmpegError,
    MissingRnnoiseError,
    MissingSileroVadError,
    MissingSpleeterError,
)


def _disable_bundled_tool_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_tools.bundled_tool_path", lambda _tool_name: None)


def test_find_ffmpeg_uses_default_path_lookup_when_unconfigured(monkeypatch) -> None:
    calls: list[str] = []

    def fake_which(name: str) -> str:
        calls.append(name)
        return "/usr/local/bin/ffmpeg"

    _disable_bundled_tool_lookup(monkeypatch)
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.shutil.which", fake_which)

    assert find_ffmpeg() == Path("/usr/local/bin/ffmpeg")
    assert calls == ["ffmpeg"]


def test_find_ffmpeg_default_override_stays_empty_string() -> None:
    audio_processor_module = importlib.import_module("anki_audio_quick_editor.audio_processor")

    assert audio_processor_module.find_ffmpeg.__defaults__ == ("",)


def test_find_ffmpeg_raises_exact_message_when_missing_and_unconfigured(monkeypatch) -> None:
    _disable_bundled_tool_lookup(monkeypatch)
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.shutil.which", lambda _name: None)
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.Path",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("configured path should not be consulted")),
    )

    with pytest.raises(MissingFfmpegError) as exc_info:
        find_ffmpeg()

    assert str(exc_info.value) == (
        "Audio Quick Editor requires ffmpeg. The managed runtime may still be downloading "
        "or missing; open Settings > Diagnostics to install or repair it, configure an "
        "ffmpeg path, or make ffmpeg available in PATH."
    )


def test_find_ffmpeg_prefers_existing_configured_file(tmp_path: Path) -> None:
    ffmpeg = tmp_path / "ffmpeg"
    ffmpeg.write_text("")

    assert find_ffmpeg(str(ffmpeg)) == ffmpeg


@pytest.mark.parametrize(
    ("system", "machine", "expected"),
    [
        ("Darwin", "arm64", "macos-arm64"),
        ("Darwin", "aarch64", "macos-arm64"),
        ("Darwin", "x86_64", "macos-x86_64"),
        ("Windows", "AMD64", "windows-x86_64"),
        ("Windows", "x86_64", "windows-x86_64"),
        ("Windows", "64bit", "windows-x86_64"),
    ],
)
def test_current_platform_key_maps_supported_targets(
    monkeypatch,
    system: str,
    machine: str,
    expected: str,
) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_tools.platform.system", lambda: system)
    monkeypatch.setattr("anki_audio_quick_editor.audio_tools.platform.machine", lambda: machine)

    assert current_platform_key() == expected


def test_bundled_tool_path_uses_normalized_platform_layout(
    tmp_path: Path,
    monkeypatch,
) -> None:
    ffmpeg = tmp_path / "bin" / "macos-arm64" / "ffmpeg"
    ffmpeg.parent.mkdir(parents=True)
    ffmpeg.write_text("")
    monkeypatch.setattr("anki_audio_quick_editor.audio_tools._PACKAGE_DIR", tmp_path)
    monkeypatch.setattr("anki_audio_quick_editor.audio_tools.current_platform_key", lambda: "macos-arm64")

    assert bundled_tool_path("ffmpeg") == ffmpeg


def test_find_ffmpeg_uses_bundled_binary_before_path_lookup(
    tmp_path: Path,
    monkeypatch,
) -> None:
    bundled = tmp_path / "ffmpeg"
    bundled.write_text("")
    calls: list[str] = []

    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_tools.bundled_tool_path",
        lambda tool_name: bundled if tool_name == "ffmpeg" else None,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.shutil.which",
        lambda name: calls.append(name) or "/usr/local/bin/ffmpeg",
    )

    assert find_ffmpeg() == bundled
    assert calls == []


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

    with pytest.raises(MissingDeepFilterError, match="DeepFilterNet.*Standard denoise"):
        find_deep_filter()


def test_find_rnnoise_bundle_uses_bundled_executable_when_complete(
    tmp_path: Path,
    monkeypatch,
) -> None:
    bundled_dir = tmp_path / "macos-arm64"
    rnnoise_path = bundled_dir / "rnnoise-cli"
    rnnoise_path.parent.mkdir(parents=True)
    rnnoise_path.write_text("")

    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.expected_bundled_tool_path",
        lambda tool_name: rnnoise_path if tool_name == "rnnoise-cli" else None,
    )

    assert find_rnnoise_bundle() == rnnoise_path


def test_find_rnnoise_bundle_raises_when_bundle_is_incomplete(
    tmp_path: Path,
    monkeypatch,
) -> None:
    bundled_dir = tmp_path / "macos-arm64"
    bundled_dir.mkdir(parents=True)

    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.expected_bundled_tool_path",
        lambda tool_name: bundled_dir / "rnnoise-cli" if tool_name == "rnnoise-cli" else None,
    )
    monkeypatch.setattr("anki_audio_quick_editor.audio_tools._PACKAGE_DIR", tmp_path)
    monkeypatch.setattr("anki_audio_quick_editor.audio_tools.current_platform_key", lambda: "macos-arm64")

    with pytest.raises(MissingRnnoiseError, match="bundled rnnoise-cli executable"):
        find_rnnoise_bundle()


def test_find_spleeter_bundle_uses_bundled_executable_and_models(
    tmp_path: Path,
    monkeypatch,
) -> None:
    executable = tmp_path / "bin" / "macos-arm64" / "sherpa-spleeter"
    vocals = tmp_path / "bin" / "models" / "spleeter-2stems-fp16" / "vocals.fp16.onnx"
    accompaniment = vocals.parent / "accompaniment.fp16.onnx"
    executable.parent.mkdir(parents=True)
    vocals.parent.mkdir(parents=True)
    executable.write_text("")
    vocals.write_text("")
    accompaniment.write_text("")

    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.expected_bundled_tool_path",
        lambda tool_name: executable if tool_name == "sherpa-spleeter" else None,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.expected_bundled_spleeter_model_path",
        lambda model_name: vocals if model_name == "vocals.fp16.onnx" else accompaniment,
    )

    assert find_spleeter_bundle() == (executable, vocals, accompaniment)


def test_find_spleeter_bundle_reports_missing_model(
    tmp_path: Path,
    monkeypatch,
) -> None:
    executable = tmp_path / "bin" / "macos-arm64" / "sherpa-spleeter"
    vocals = tmp_path / "bin" / "models" / "spleeter-2stems-fp16" / "vocals.fp16.onnx"
    accompaniment = vocals.parent / "accompaniment.fp16.onnx"
    executable.parent.mkdir(parents=True)
    vocals.parent.mkdir(parents=True)
    executable.write_text("")
    vocals.write_text("")

    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.expected_bundled_tool_path",
        lambda tool_name: executable if tool_name == "sherpa-spleeter" else None,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.expected_bundled_spleeter_model_path",
        lambda model_name: vocals if model_name == "vocals.fp16.onnx" else accompaniment,
    )

    with pytest.raises(MissingSpleeterError, match="accompaniment.fp16.onnx"):
        find_spleeter_bundle()


def test_find_silero_vad_bundle_uses_bundled_executable_and_model(
    tmp_path: Path,
    monkeypatch,
) -> None:
    executable = tmp_path / "bin" / "macos-arm64" / "silero-vad"
    model = tmp_path / "bin" / "models" / "silero-vad" / "silero_vad.onnx"
    executable.parent.mkdir(parents=True)
    model.parent.mkdir(parents=True)
    executable.write_text("")
    model.write_text("")

    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.expected_bundled_tool_path",
        lambda tool_name: executable if tool_name == "silero-vad" else None,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.expected_bundled_silero_vad_model_path",
        lambda: model,
    )

    assert find_silero_vad_bundle() == (executable, model)


def test_find_silero_vad_bundle_reports_missing_model(
    tmp_path: Path,
    monkeypatch,
) -> None:
    executable = tmp_path / "bin" / "macos-arm64" / "silero-vad"
    model = tmp_path / "bin" / "models" / "silero-vad" / "silero_vad.onnx"
    executable.parent.mkdir(parents=True)
    executable.write_text("")

    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.expected_bundled_tool_path",
        lambda tool_name: executable if tool_name == "silero-vad" else None,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.expected_bundled_silero_vad_model_path",
        lambda: model,
    )

    with pytest.raises(MissingSileroVadError, match="silero_vad.onnx"):
        find_silero_vad_bundle()


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

    _disable_bundled_tool_lookup(monkeypatch)
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.shutil.which", fake_which)

    assert find_ffprobe(tmp_path / "ffmpeg") == Path("/usr/local/bin/ffprobe")
    assert calls == ["ffprobe"]


def test_find_ffprobe_uses_bundled_binary_before_path_lookup(
    tmp_path: Path,
    monkeypatch,
) -> None:
    bundled = tmp_path / "ffprobe"
    bundled.write_text("")
    calls: list[str] = []

    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_tools.bundled_tool_path",
        lambda tool_name: bundled if tool_name == "ffprobe" else None,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.shutil.which",
        lambda name: calls.append(name) or "/usr/local/bin/ffprobe",
    )

    assert find_ffprobe(tmp_path / "ffmpeg") == bundled
    assert calls == []


def test_find_ffprobe_raises_when_no_binary_available(monkeypatch, tmp_path: Path) -> None:
    _disable_bundled_tool_lookup(monkeypatch)
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.shutil.which", lambda _name: None)

    with pytest.raises(MissingFfmpegError) as exc_info:
        find_ffprobe(tmp_path / "ffmpeg")

    assert str(exc_info.value) == "Audio Quick Editor requires ffprobe alongside ffmpeg to inspect audio duration."
