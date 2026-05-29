from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from anki_audio_quick_editor.audio_processor import (
    find_ffmpeg,
    probe_duration_ms,
    render_converted_audio,
)
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.errors import AudioProcessingError
from tests.audio_fixtures import (
    FFMPEG_AVAILABLE,
    FFMPEG_SKIP_REASON,
)


def test_render_converted_audio_uses_expected_ffmpeg_invocation(monkeypatch, tmp_path: Path) -> None:
    calls: list[tuple[list[str], bool, bool, bool]] = []
    commands: list[tuple[str, ...]] = []

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: 1000)
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.resolve_output_policy",
        lambda *_args, **_kwargs: SimpleNamespace(
            extension=".flac",
            mime_type="audio/flac",
            codec_args=("-codec:a", "flac", "-compression_level", "5"),
        ),
    )

    def fake_run(cmd: list[str], capture_output: bool, text: bool, check: bool) -> SimpleNamespace:
        calls.append((cmd, capture_output, text, check))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    output = tmp_path / "converted.flac"
    result = render_converted_audio(
        tmp_path / "source.wav",
        AudioProcessingConfig(ffmpeg_path="/custom/ffmpeg"),
        "flac",
        output_path=output,
        on_command=commands.append,
    )

    expected_command = (
        "/bin/ffmpeg",
        "-y",
        "-i",
        str(tmp_path / "source.wav"),
        "-vn",
        "-codec:a",
        "flac",
        "-compression_level",
        "5",
        str(output),
    )
    assert calls == [(list(expected_command), True, True, False)]
    assert commands == [expected_command]
    assert result.output_path == output
    assert result.command == expected_command
    assert result.duration_ms == 1000


def test_render_converted_audio_uses_default_error_message_for_blank_stderr(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.resolve_output_policy",
        lambda *_args, **_kwargs: SimpleNamespace(
            extension=".m4a",
            mime_type="audio/mp4",
            codec_args=("-codec:a", "aac", "-b:a", "192k"),
        ),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=1, stdout="", stderr="   "),
    )

    with pytest.raises(AudioProcessingError, match="Audio conversion failed."):
        render_converted_audio(
            tmp_path / "source.wav",
            AudioProcessingConfig(),
            "m4a",
            output_path=tmp_path / "output.m4a",
        )


@pytest.mark.parametrize("target_format", ["mp3", "m4a", "wav", "flac"])
@pytest.mark.skipif(
    not FFMPEG_AVAILABLE,
    reason=FFMPEG_SKIP_REASON,
)
def test_render_converted_audio_smoke_for_supported_formats(
    target_format: str,
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.wav"
    output = tmp_path / f"converted.{target_format}"
    ffmpeg_path = find_ffmpeg(AudioProcessingConfig().ffmpeg_path)

    subprocess.run(
        [
            str(ffmpeg_path),
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=1",
            str(source),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    result = render_converted_audio(
        source,
        AudioProcessingConfig(),
        target_format,
        output_path=output,
    )

    assert result.output_path == output
    assert output.is_file()
    assert 900 <= probe_duration_ms(output, AudioProcessingConfig()) <= 1100
