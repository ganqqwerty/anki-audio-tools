from __future__ import annotations

import importlib
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from anki_audio_quick_editor.audio_processor import (
    find_ffmpeg,
    format_ffmpeg_command,
    make_playback_segment_filename,
    probe_duration_ms,
    render_playback_segment,
)
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.errors import (
    AudioProcessingError,
)
from tests.audio_fixtures import (
    FFMPEG_AVAILABLE,
    FFMPEG_SKIP_REASON,
)


def test_make_playback_segment_filename_is_debuggable_and_sanitized() -> None:
    filename = make_playback_segment_filename("../短い test.wav", 700, "abc12345")

    assert filename == "aqe_playback_test__from_700ms_abc12345.mp3"


def test_make_playback_segment_filename_clamps_negative_start_and_bounds_length() -> None:
    filename = make_playback_segment_filename("x" * 500 + ".wav", -25, "abc12345")

    assert filename.startswith("aqe_playback_")
    assert "__from_0ms_abc12345.mp3" in filename
    assert len(filename) <= 160


def test_make_playback_segment_filename_uses_audio_for_empty_source_name() -> None:
    audio_processor_module = importlib.import_module("anki_audio_quick_editor.audio_processor")

    filename = audio_processor_module.make_playback_segment_filename("", 700, "abc12345")

    assert filename == "aqe_playback_audio__from_700ms_abc12345.mp3"


def test_make_playback_segment_filename_uses_eight_character_generated_token(monkeypatch) -> None:
    audio_processor_module = importlib.import_module("anki_audio_quick_editor.audio_processor")
    monkeypatch.setattr(audio_processor_module.uuid, "uuid4", lambda: SimpleNamespace(hex="1234567890abcdef"))

    filename = audio_processor_module.make_playback_segment_filename("clip.wav", 700)

    assert filename == "aqe_playback_clip__from_700ms_12345678.mp3"


def test_temp_playback_path_uses_generated_temp_dir_and_segment_filename(monkeypatch, tmp_path: Path) -> None:
    audio_processor_module = importlib.import_module("anki_audio_quick_editor.audio_processor")
    temp_dir = tmp_path / "aqe_playback_tmp"
    build_calls: list[tuple[str, int]] = []

    monkeypatch.setattr(audio_processor_module.tempfile, "mkdtemp", lambda prefix: str(temp_dir))
    monkeypatch.setattr(
        audio_processor_module,
        "make_playback_segment_filename",
        lambda source_filename, start_ms: build_calls.append((source_filename, start_ms)) or "segment.mp3",
    )

    path = audio_processor_module.temp_playback_path("clip.wav", 700)

    assert build_calls == [("clip.wav", 700)]
    assert path == temp_dir / "segment.mp3"



def test_render_playback_segment_rejects_cursor_at_end(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda *_args: Path("/tmp/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: 1000)

    with pytest.raises(AudioProcessingError, match="Cursor is at the end of the audio."):
        render_playback_segment(
            tmp_path / "source.wav",
            1000,
            AudioProcessingConfig(),
        )


def test_render_playback_segment_rejects_cursor_at_exact_end_threshold(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda *_args: Path("/tmp/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: 1000)

    with pytest.raises(AudioProcessingError, match="Cursor is at the end of the audio."):
        render_playback_segment(
            tmp_path / "source.wav",
            980,
            AudioProcessingConfig(),
        )


def test_render_playback_segment_rejects_tiny_audio_from_start(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda *_args: Path("/tmp/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: 10)

    with pytest.raises(AudioProcessingError, match="Cursor is at the end of the audio."):
        render_playback_segment(
            tmp_path / "source.wav",
            0,
            AudioProcessingConfig(),
        )


def test_render_playback_segment_clamps_negative_start_and_invokes_ffmpeg(monkeypatch, tmp_path: Path) -> None:
    calls: list[tuple[list[str], bool, bool, bool]] = []
    durations = iter([1000, 300])
    commands: list[tuple[str, ...]] = []
    ffmpeg_args: list[str | None] = []

    def fake_find_ffmpeg(path: str | None) -> Path:
        ffmpeg_args.append(path)
        return Path("/bin/ffmpeg")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", fake_find_ffmpeg)
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: next(durations))

    def fake_run(cmd: list[str], capture_output: bool, text: bool, check: bool) -> SimpleNamespace:
        calls.append((cmd, capture_output, text, check))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    output = tmp_path / "segment.mp3"
    result = render_playback_segment(
        tmp_path / "source.wav",
        -50,
        AudioProcessingConfig(ffmpeg_path="/custom/ffmpeg"),
        output_path=output,
        on_command=commands.append,
    )

    expected_command = (
        "/bin/ffmpeg",
        "-y",
        "-i",
        str(tmp_path / "source.wav"),
        "-vn",
        "-filter:a",
        "atrim=start=0.000,asetpts=PTS-STARTPTS",
        "-codec:a",
        "libmp3lame",
        "-q:a",
        "4",
        str(output),
    )
    assert ffmpeg_args == ["/custom/ffmpeg"]
    assert calls == [(list(expected_command), True, True, False)]
    assert commands == [expected_command]
    assert result.output_path == output
    assert result.command == expected_command
    assert result.duration_ms == 300


def test_render_playback_segment_honors_selected_end_boundary(monkeypatch, tmp_path: Path) -> None:
    calls: list[tuple[list[str], bool, bool, bool]] = []
    durations = iter([2000, 750])
    commands: list[tuple[str, ...]] = []

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: next(durations))

    def fake_run(cmd: list[str], capture_output: bool, text: bool, check: bool) -> SimpleNamespace:
        calls.append((cmd, capture_output, text, check))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    output = tmp_path / "segment.mp3"
    result = render_playback_segment(
        tmp_path / "source.wav",
        500,
        AudioProcessingConfig(),
        output_path=output,
        on_command=commands.append,
        end_ms=1250,
    )

    expected_command = (
        "/bin/ffmpeg",
        "-y",
        "-i",
        str(tmp_path / "source.wav"),
        "-vn",
        "-filter:a",
        "atrim=start=0.500:end=1.250,asetpts=PTS-STARTPTS",
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


def test_render_playback_segment_allows_cursor_before_end_threshold(monkeypatch, tmp_path: Path) -> None:
    durations = iter([1000, 21])

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: next(durations))
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )

    result = render_playback_segment(
        tmp_path / "source.wav",
        979,
        AudioProcessingConfig(),
        output_path=tmp_path / "segment.mp3",
    )

    assert result.duration_ms == 21


def test_render_playback_segment_uses_default_error_message_for_blank_stderr(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: 1000)
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=1, stdout="", stderr=""),
    )

    with pytest.raises(AudioProcessingError) as exc_info:
        render_playback_segment(
            tmp_path / "source.wav",
            100,
            AudioProcessingConfig(),
            output_path=tmp_path / "segment.mp3",
        )

    assert str(exc_info.value) == "Playback segment rendering failed."


def test_render_playback_segment_uses_exact_end_of_audio_message(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda *_args: Path("/tmp/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: 1000)

    with pytest.raises(AudioProcessingError) as exc_info:
        render_playback_segment(
            tmp_path / "source.wav",
            1000,
            AudioProcessingConfig(),
        )

    assert str(exc_info.value) == "Cursor is at the end of the audio."

@pytest.mark.skipif(
    not FFMPEG_AVAILABLE,
    reason=FFMPEG_SKIP_REASON,
)
def test_render_playback_segment_from_70_percent_is_shorter(tmp_path: Path) -> None:
    source = tmp_path / "cursor source.wav"
    output = tmp_path / "cursor segment.mp3"
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

    result = render_playback_segment(
        source,
        700,
        AudioProcessingConfig(),
        output_path=output,
    )

    assert result.output_path == output
    assert "atrim=start=0.700" in format_ffmpeg_command(result.command)
    assert output.is_file()
    assert 220 <= probe_duration_ms(output, AudioProcessingConfig()) <= 380
