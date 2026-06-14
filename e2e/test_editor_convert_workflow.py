"""E2E tests for editor convert-to-format workflow."""

from __future__ import annotations

from pathlib import Path

from e2e.conftest import import_runtime_addon_module
from e2e.editor_note_helpers import (
    ADDON_NUMERIC_ID,
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
    _processing_status_js,
    _sound_filename,
)
from e2e.helpers import (
    click_selector,
    generate_tone,
    wait_for_condition,
    wait_for_js_condition,
    wait_for_selector,
)
from e2e.test_editor_processing_split_buttons_workflow import _split_menu_selector


def _wait_for_generated_audio(
    note,
    media_dir: Path,
    previous_name: str,
    *,
    suffix: str,
    timeout: float = 10.0,
) -> str:
    def current_generated() -> str | None:
        filename = _sound_filename(note.fields[0])
        if filename != previous_name and filename.endswith(suffix) and (media_dir / filename).is_file():
            return filename
        return None

    wait_for_condition(
        lambda: current_generated() is not None,
        timeout=timeout,
        message=f"Expected generated {suffix} audio reference",
    )
    generated = current_generated()
    assert generated is not None
    return generated


def test_editor_convert_split_button_creates_selected_format_without_changing_settings(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_convert_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    original_bytes = source.read_bytes()
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, output_format="mp3")

    audio_processor = import_runtime_addon_module(".audio_processor")

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:convert"), timeout=10.0)
        click_selector(editor.web, _split_menu_selector("aqe:convert"), timeout=5.0)
        click_selector(editor.web, '[data-testid="aqe-split-0-convert-preset-flac"]', timeout=5.0)
        click_selector(editor.web, _button_selector("aqe:convert"), timeout=5.0)

        generated_name = _wait_for_generated_audio(note, media_dir, source.name, suffix=".flac")

        assert generated_name.endswith(".flac")
        assert source.read_bytes() == original_bytes
        assert (
            audio_processor.probe_duration_ms(media_dir / generated_name, audio_processor.AudioProcessingConfig())
            > 0
        )
        assert anki_mw.addonManager.getConfig(ADDON_NUMERIC_ID)["output_format"] == "mp3"
    finally:
        editor.set_note(None)
        parent.close()


def test_editor_convert_same_extension_notifies_and_leaves_field_unchanged(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_convert_noop.mp3"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    original_bytes = source.read_bytes()
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, output_format="mp3")

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:convert"), timeout=10.0)
        click_selector(editor.web, _button_selector("aqe:convert"), timeout=5.0)
        status = wait_for_js_condition(
            editor.web,
            _processing_status_js(),
            lambda value: value is not None and "Already in MP3 format." in value["text"],
            timeout=5.0,
        )

        assert "Already in MP3 format." in status["text"]
        assert _sound_filename(note.fields[0]) == source.name
        assert source.read_bytes() == original_bytes
        assert (media_dir / source.name).is_file()
    finally:
        editor.set_note(None)
        parent.close()
