"""E2E tests that exercise real ffmpeg audio rendering."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from e2e.helpers import generate_tone

FORMAT_FIXTURES = (
    ("aac", ("-c:a", "aac", "-f", "adts")),
    ("flac", ("-c:a", "flac")),
    ("m4a", ("-c:a", "aac", "-f", "mp4")),
    ("mp3", ("-c:a", "libmp3lame")),
    ("oga", ("-ac", "2", "-c:a", "vorbis", "-strict", "-2", "-f", "ogg")),
    ("ogg", ("-ac", "2", "-c:a", "vorbis", "-strict", "-2", "-f", "ogg")),
    ("opus", ("-ar", "48000", "-c:a", "opus", "-strict", "-2", "-f", "opus")),
    ("wav", ("-c:a", "pcm_s16le")),
    ("webm", ("-ar", "48000", "-c:a", "opus", "-strict", "-2", "-f", "webm")),
)


def _generate_audio_fixture(ffmpeg_config, path: Path, output_args: tuple[str, ...]) -> None:
    subprocess.run(
        [
            ffmpeg_config.ffmpeg_path,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=0.8",
            "-vn",
            "-ac",
            "1",
            "-ar",
            "44100",
            *output_args,
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


# noinspection PyUnusedLocal
def test_trim_left_renders_shorter_recording(
    anki_mw,
    tmp_path: Path,
    ffmpeg_config,
) -> None:
    from anki_audio_quick_editor.audio_processor import probe_duration_ms, render_audio
    from anki_audio_quick_editor.audio_state import AudioEditState

    del anki_mw
    source = tmp_path / "sentence with spaces.wav"
    output = tmp_path / "trimmed.mp3"
    generate_tone(ffmpeg_config, source, duration_s=2.0)

    original_duration_ms = probe_duration_ms(source, ffmpeg_config)
    render_audio(
        source,
        AudioEditState(source_file=source.name, left_trim_ms=500),
        ffmpeg_config,
        output_path=output,
    )
    trimmed_duration_ms = probe_duration_ms(output, ffmpeg_config)

    assert 1900 <= original_duration_ms <= 2100
    assert 1350 <= trimmed_duration_ms <= 1650
    assert trimmed_duration_ms < original_duration_ms - 350


# noinspection PyUnusedLocal
def test_speed_up_renders_shorter_mp3(
    anki_mw,
    tmp_path: Path,
    ffmpeg_config,
) -> None:
    from anki_audio_quick_editor.audio_processor import probe_duration_ms, render_audio
    from anki_audio_quick_editor.audio_state import AudioEditState

    del anki_mw
    source = tmp_path / "speed-source.wav"
    output = tmp_path / "faster.mp3"
    generate_tone(ffmpeg_config, source, duration_s=2.0)

    original_duration_ms = probe_duration_ms(source, ffmpeg_config)
    render_audio(
        source,
        AudioEditState(source_file=source.name, speed=1.25),
        ffmpeg_config,
        output_path=output,
    )
    faster_duration_ms = probe_duration_ms(output, ffmpeg_config)

    assert 1500 <= faster_duration_ms <= 1750
    assert faster_duration_ms < original_duration_ms - 250


# noinspection PyUnusedLocal
def test_volume_gain_renders_new_mp3_with_db_filter(
    anki_mw,
    tmp_path: Path,
    ffmpeg_config,
) -> None:
    from anki_audio_quick_editor.audio_processor import (
        format_ffmpeg_command,
        render_audio,
    )
    from anki_audio_quick_editor.audio_state import AudioEditState

    del anki_mw
    source = tmp_path / "volume-source.wav"
    louder = tmp_path / "louder.mp3"
    quieter = tmp_path / "quieter.mp3"
    generate_tone(ffmpeg_config, source, duration_s=1.0)

    louder_result = render_audio(
        source,
        AudioEditState(source_file=source.name, volume_db=6.0),
        ffmpeg_config,
        output_path=louder,
    )
    quieter_result = render_audio(
        source,
        AudioEditState(source_file=source.name, volume_db=-6.0),
        ffmpeg_config,
        output_path=quieter,
    )

    assert louder.is_file()
    assert quieter.is_file()
    assert "volume=6.00dB" in format_ffmpeg_command(louder_result.command)
    assert "volume=-6.00dB" in format_ffmpeg_command(quieter_result.command)


# noinspection PyUnusedLocal
@pytest.mark.parametrize(("extension", "output_args"), FORMAT_FIXTURES)
def test_common_audio_input_format_renders_to_mp3(
    anki_mw,
    tmp_path: Path,
    ffmpeg_config,
    extension: str,
    output_args: tuple[str, ...],
) -> None:
    from anki_audio_quick_editor.audio_processor import probe_duration_ms, render_audio
    from anki_audio_quick_editor.audio_state import AudioEditState

    del anki_mw
    source = tmp_path / f"common-input.{extension}"
    output = tmp_path / f"rendered-{extension}.mp3"
    _generate_audio_fixture(ffmpeg_config, source, output_args)

    result = render_audio(
        source,
        AudioEditState(source_file=source.name, volume_db=-1.0),
        ffmpeg_config,
        output_path=output,
    )

    assert output.is_file()
    assert result.output_path == output
    assert result.output_path.suffix == ".mp3"
    assert "libmp3lame" in result.command
    assert probe_duration_ms(output, ffmpeg_config) > 0


def test_final_save_writes_new_anki_media_without_overwriting_original(
    anki_mw,
    ffmpeg_config,
) -> None:
    from anki_audio_quick_editor.audio_processor import (
        make_output_filename,
        probe_duration_ms,
        render_audio,
        temp_final_path,
    )
    from anki_audio_quick_editor.audio_state import AudioEditState

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "original_sentence.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.5)
    original_bytes = source.read_bytes()

    desired_name = make_output_filename(source.name)
    rendered_path = temp_final_path(desired_name)
    render_audio(
        source,
        AudioEditState(source_file=source.name, left_trim_ms=400),
        ffmpeg_config,
        output_path=rendered_path,
    )
    saved_name = anki_mw.col.media.write_data(desired_name, rendered_path.read_bytes())
    saved_path = media_dir / saved_name

    assert saved_name.endswith(".mp3")
    assert saved_path.is_file()
    assert source.read_bytes() == original_bytes
    assert probe_duration_ms(saved_path, ffmpeg_config) < probe_duration_ms(source, ffmpeg_config)
