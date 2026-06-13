"""E2E tests for editor audio size reduction."""

from __future__ import annotations

from pathlib import Path

from e2e.editor_audio_generation_helpers import _generate_high_bitrate_mp3
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
    _wait_for_generated_mp3,
    _wait_for_status_flow,
)
from e2e.helpers import click_selector, wait_for_selector


def test_compress_audio_button_renders_compressed_mp3_with_real_ffmpeg(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_size_reduce_source.mp3"
    _generate_high_bitrate_mp3(ffmpeg_config, source)
    original_bytes = source.read_bytes()
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, size_reduction_mode="normal")

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:reduce-size"), timeout=10.0)
        click_selector(editor.web, _button_selector("aqe:reduce-size"), timeout=5.0)
        generated_name = _wait_for_generated_mp3(note, media_dir, source.name)
        status = _wait_for_status_flow(
            editor,
            lambda value: value["text"] == "Compressed audio with Normal level.",
            timeout=10.0,
        )

        generated_path = media_dir / generated_name
        assert status["text"] == "Compressed audio with Normal level."
        assert generated_name.endswith(".mp3")
        assert generated_path.stat().st_size < len(original_bytes)
        assert source.read_bytes() == original_bytes
    finally:
        editor.set_note(None)
        parent.close()
