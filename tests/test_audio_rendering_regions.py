"""Region and smoke rendering tests."""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from anki_audio_quick_editor.audio_processor import (
    find_ffmpeg,
    format_ffmpeg_command,
    probe_duration_ms,
    render_audio,
    render_audio_region_deleted,
    render_audio_region_kept,
)
from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.errors import AudioProcessingError
from tests.audio_fixtures import FFMPEG_AVAILABLE, FFMPEG_SKIP_REASON


def test_render_audio_region_deleted_uses_concat_filter(monkeypatch, tmp_path: Path) -> None:
    calls: list[tuple[list[str], bool, bool, bool]] = []
    durations = iter([2000, 1250])
    commands: list[tuple[str, ...]] = []
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: next(durations))
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.subprocess.run",
        lambda cmd, capture_output, text, check: calls.append((cmd, capture_output, text, check)) or SimpleNamespace(returncode=0, stdout="", stderr=""),
    )
    output = tmp_path / "cut.mp3"
    result = render_audio_region_deleted(
        tmp_path / "source.wav",
        500,
        1250,
        AudioProcessingConfig(),
        output_path=output,
        on_command=commands.append,
    )
    filter_complex = (
        "[0:a]atrim=start=0.000:end=0.500,asetpts=PTS-STARTPTS[a0];"
        "[0:a]atrim=start=1.250:end=2.000,asetpts=PTS-STARTPTS[a1];"
        "[a0][a1]concat=n=2:v=0:a=1[out]"
    )
    expected_command = (
        "/bin/ffmpeg",
        "-y",
        "-i",
        str(tmp_path / "source.wav"),
        "-vn",
        "-filter_complex",
        filter_complex,
        "-map",
        "[out]",
        "-codec:a",
        "libmp3lame",
        "-q:a",
        "4",
        str(output),
    )
    assert calls == [(list(expected_command), True, True, False)]
    assert commands == [expected_command]
    assert result.output_path == output
    assert result.command == expected_command
    assert result.duration_ms == 1250


def test_render_audio_region_kept_uses_single_trim_filter(monkeypatch, tmp_path: Path) -> None:
    calls: list[tuple[list[str], bool, bool, bool]] = []
    durations = iter([2000, 750])
    commands: list[tuple[str, ...]] = []
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: next(durations))
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.subprocess.run",
        lambda cmd, capture_output, text, check: calls.append((cmd, capture_output, text, check)) or SimpleNamespace(returncode=0, stdout="", stderr=""),
    )
    output = tmp_path / "kept.mp3"
    result = render_audio_region_kept(
        tmp_path / "source.wav",
        500,
        1250,
        AudioProcessingConfig(),
        output_path=output,
        on_command=commands.append,
    )
    expected_command = (
        "/bin/ffmpeg",
        "-y",
        "-i",
        str(tmp_path / "source.wav"),
        "-vn",
        "-filter_complex",
        "[0:a]atrim=start=0.500:end=1.250,asetpts=PTS-STARTPTS[out]",
        "-map",
        "[out]",
        "-codec:a",
        "libmp3lame",
        "-q:a",
        "4",
        str(output),
    )
    assert calls == [(list(expected_command), True, True, False)]
    assert commands == [expected_command]
    assert result.output_path == output
    assert result.command == expected_command
    assert result.duration_ms == 750


def test_render_audio_uses_default_error_message_for_blank_stderr(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: 1000)
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.build_audio_filters", lambda *_args: "filters")
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=1, stdout="", stderr="   "),
    )
    with pytest.raises(AudioProcessingError, match="Audio processing failed."):
        render_audio(
            tmp_path / "source.wav",
            AudioEditState("clip.wav"),
            AudioProcessingConfig(),
            output_path=tmp_path / "output.mp3",
        )


@pytest.mark.skipif(not FFMPEG_AVAILABLE, reason=FFMPEG_SKIP_REASON)
def test_render_audio_smoke_with_path_spaces_and_non_ascii(tmp_path: Path) -> None:
    source_dir = tmp_path / "media with spaces"
    source_dir.mkdir()
    source = source_dir / "短い clip.wav"
    output = tmp_path / "edited preview.mp3"
    ffmpeg_path = find_ffmpeg(AudioProcessingConfig().ffmpeg_path)
    subprocess.run(
        [str(ffmpeg_path), "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=1", str(source)],
        check=True,
        capture_output=True,
        text=True,
    )
    result = render_audio(
        source,
        AudioEditState("短い clip.wav", left_trim_ms=100, speed=1.05),
        AudioProcessingConfig(),
        output_path=output,
    )
    assert result.output_path == output
    assert " -y -i " in format_ffmpeg_command(result.command)
    assert output.is_file()
    assert 700 <= probe_duration_ms(output, AudioProcessingConfig()) <= 1000


@pytest.mark.skipif(not FFMPEG_AVAILABLE, reason=FFMPEG_SKIP_REASON)
def test_render_audio_region_kept_smoke_outputs_selected_duration(tmp_path: Path) -> None:
    source = tmp_path / "source.wav"
    output = tmp_path / "kept.mp3"
    ffmpeg_path = find_ffmpeg(AudioProcessingConfig().ffmpeg_path)
    subprocess.run(
        [str(ffmpeg_path), "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=2", str(source)],
        check=True,
        capture_output=True,
        text=True,
    )
    result = render_audio_region_kept(source, 500, 1250, AudioProcessingConfig(), output_path=output)
    probed_duration_ms = probe_duration_ms(output, AudioProcessingConfig())
    assert result.output_path == output
    assert output.is_file()
    assert result.duration_ms == probed_duration_ms
    assert 650 <= probed_duration_ms <= 900
