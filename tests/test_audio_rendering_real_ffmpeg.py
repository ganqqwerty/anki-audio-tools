from __future__ import annotations

from pathlib import Path

import pytest

from anki_audio_quick_editor.audio_processor import (
    format_ffmpeg_command,
    make_output_filename,
    probe_duration_ms,
    render_audio,
    temp_final_path,
)
from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from tests.audio_fixtures import (
    FFMPEG_AVAILABLE,
    FFMPEG_SKIP_REASON,
    _ffmpeg_paths,
    _run_ffmpeg,
)
from tests.media_oracles import db_ratio, decode_mono_f32, probe_audio, rms

INPUT_FORMAT_FIXTURES = (
    ("aac", ("-c:a", "aac", "-f", "adts")),
    ("flac", ("-c:a", "flac")),
    ("m4a", ("-c:a", "aac", "-f", "mp4")),
    ("oga", ("-ac", "2", "-c:a", "vorbis", "-strict", "-2", "-f", "ogg")),
    ("ogg", ("-ac", "2", "-c:a", "vorbis", "-strict", "-2", "-f", "ogg")),
    ("opus", ("-ar", "48000", "-c:a", "opus", "-strict", "-2", "-f", "opus")),
    ("wav", ("-c:a", "pcm_s16le")),
    ("webm", ("-ar", "48000", "-c:a", "opus", "-strict", "-2", "-f", "webm")),
)


def _generate_tone(path: Path, *, duration_s: float = 1.0) -> None:
    _run_ffmpeg(
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=440:duration={duration_s}",
        "-vn",
        str(path),
    )


def _generate_input_format(path: Path, *, output_args: tuple[str, ...]) -> None:
    _run_ffmpeg(
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
    )


@pytest.mark.allow_managed_runtime
def test_render_audio_writes_temp_final_output_without_mutating_source_file(
    monkeypatch,
    tmp_path: Path,
) -> None:
    assert FFMPEG_AVAILABLE, FFMPEG_SKIP_REASON
    source = tmp_path / "source.wav"
    _generate_tone(source, duration_s=1.0)
    original_source_bytes = source.read_bytes()
    desired_name = make_output_filename(source.name)
    temp_root = tmp_path / "aqe_final_test"
    temp_root.mkdir()
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_rendering.tempfile.mkdtemp",
        lambda *, prefix: str(temp_root),
    )
    final_output = temp_final_path(desired_name)
    output = render_audio(
        source,
        AudioEditState(source_file=source.name, left_trim_ms=250),
        AudioProcessingConfig(),
        output_path=final_output,
    )

    assert source.is_file()
    assert source.read_bytes() == original_source_bytes
    assert output.output_path == final_output
    assert output.output_path.suffix == ".wav"
    assert output.output_path.exists()


@pytest.mark.allow_managed_runtime
def test_render_audio_left_trim_reduces_output_duration_on_real_ffmpeg(tmp_path: Path) -> None:
    assert FFMPEG_AVAILABLE, FFMPEG_SKIP_REASON
    source = tmp_path / "source.wav"
    output = tmp_path / "trimmed.mp3"
    _generate_tone(source, duration_s=2.0)

    result = render_audio(
        source,
        AudioEditState(source.name, left_trim_ms=500),
        AudioProcessingConfig(),
        output_path=output,
    )
    original_duration = probe_duration_ms(source, AudioProcessingConfig())
    output_duration = probe_duration_ms(output, AudioProcessingConfig())

    assert 1900 <= original_duration <= 2100
    assert 1350 <= output_duration <= 1650
    assert output_duration < original_duration - 350
    assert result.output_path == output


@pytest.mark.allow_managed_runtime
def test_render_audio_speed_up_shows_reduced_duration_on_real_ffmpeg(tmp_path: Path) -> None:
    assert FFMPEG_AVAILABLE, FFMPEG_SKIP_REASON
    source = tmp_path / "speed.wav"
    output = tmp_path / "faster.mp3"
    _generate_tone(source, duration_s=2.0)

    result = render_audio(
        source,
        AudioEditState(source.name, speed=1.25),
        AudioProcessingConfig(),
        output_path=output,
    )
    output_duration = probe_duration_ms(output, AudioProcessingConfig())

    assert 1500 <= output_duration <= 1750
    assert result.duration_ms == output_duration
    assert result.output_path == output


@pytest.mark.allow_managed_runtime
def test_render_audio_volume_gain_changes_decoded_pcm_by_expected_db(tmp_path: Path) -> None:
    assert FFMPEG_AVAILABLE, FFMPEG_SKIP_REASON
    source = tmp_path / "gain.wav"
    louder = tmp_path / "louder.mp3"
    quieter = tmp_path / "quieter.mp3"
    _generate_tone(source, duration_s=1.0)

    louder_result = render_audio(
        source,
        AudioEditState(source.name, volume_db=6.0),
        AudioProcessingConfig(),
        output_path=louder,
    )
    quieter_result = render_audio(
        source,
        AudioEditState(source.name, volume_db=-6.0),
        AudioProcessingConfig(),
        output_path=quieter,
    )

    ffmpeg, ffprobe = _ffmpeg_paths()
    source_rms = rms(decode_mono_f32(ffmpeg, source))
    louder_rms = rms(decode_mono_f32(ffmpeg, louder))
    quieter_rms = rms(decode_mono_f32(ffmpeg, quieter))

    assert db_ratio(source_rms, louder_rms) == pytest.approx(6.0, abs=0.35)
    assert db_ratio(source_rms, quieter_rms) == pytest.approx(-6.0, abs=0.35)
    assert probe_audio(ffprobe, louder).duration_s == pytest.approx(1.0, abs=0.08)
    assert probe_audio(ffprobe, quieter).duration_s == pytest.approx(1.0, abs=0.08)
    assert louder_result.output_path == louder
    assert quieter_result.output_path == quieter


@pytest.mark.parametrize(("extension", "output_args"), INPUT_FORMAT_FIXTURES)
@pytest.mark.allow_managed_runtime
def test_render_audio_accepts_multiple_input_encodings_on_real_ffmpeg(
    extension: str,
    output_args: tuple[str, ...],
    tmp_path: Path,
) -> None:
    assert FFMPEG_AVAILABLE, FFMPEG_SKIP_REASON
    source = tmp_path / f"source.{extension}"
    output = tmp_path / f"rendered.{extension}.mp3"
    _generate_input_format(source, output_args=output_args)

    result = render_audio(
        source,
        AudioEditState(source.name, volume_db=-1.0),
        AudioProcessingConfig(),
        output_path=output,
    )

    assert output.is_file()
    assert result.output_path == output
    assert result.output_path.suffix == ".mp3"
    assert "libmp3lame" in format_ffmpeg_command(result.command)
    assert probe_duration_ms(output, AudioProcessingConfig()) > 0
