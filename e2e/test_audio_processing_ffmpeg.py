"""E2E tests that exercise real ffmpeg audio rendering."""

from __future__ import annotations

from pathlib import Path

from e2e.helpers import generate_tone


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
