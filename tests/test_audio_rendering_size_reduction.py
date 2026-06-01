from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from anki_audio_quick_editor.audio_processor import render_size_reduced_audio
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.errors import AudioAlreadyCompactError


def test_render_size_reduced_audio_uses_expected_ffmpeg_invocation(
    monkeypatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.mp3"
    source.write_bytes(b"x" * 200)
    output = tmp_path / "smaller.mp3"
    calls: list[tuple[list[str], bool, bool, bool]] = []
    commands: list[tuple[str, ...]] = []

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: 1000)
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.probe_audio_metadata",
        lambda *_args: SimpleNamespace(sample_rate=44100, channels=2, bit_rate=128_000),
    )

    def fake_run(cmd: list[str], capture_output: bool, text: bool, check: bool) -> SimpleNamespace:
        output.write_bytes(b"y" * 100)
        calls.append((cmd, capture_output, text, check))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    result = render_size_reduced_audio(
        source,
        AudioProcessingConfig(ffmpeg_path="/custom/ffmpeg"),
        output_path=output,
        on_command=commands.append,
        mode="normal",
    )

    expected_command = (
        "/bin/ffmpeg",
        "-y",
        "-i",
        str(source),
        "-vn",
        "-codec:a",
        "libmp3lame",
        "-b:a",
        "64k",
        "-ar",
        "32000",
        "-ac",
        "1",
        str(output),
    )
    assert calls == [(list(expected_command), True, True, False)]
    assert commands == [expected_command]
    assert result.output_path == output
    assert result.command == expected_command
    assert result.duration_ms == 1000


def test_render_size_reduced_audio_skips_when_output_is_not_smaller(
    monkeypatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.mp3"
    source.write_bytes(b"x" * 100)
    output = tmp_path / "smaller.mp3"

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: 1000)
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.probe_audio_metadata",
        lambda *_args: SimpleNamespace(sample_rate=44100, channels=2, bit_rate=128_000),
    )

    def fake_run(*_args, **_kwargs) -> SimpleNamespace:
        output.write_bytes(b"y" * 100)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    with pytest.raises(AudioAlreadyCompactError, match="did not make a smaller file"):
        render_size_reduced_audio(
            source,
            AudioProcessingConfig(),
            output_path=output,
            mode="normal",
        )

    assert not output.exists()
