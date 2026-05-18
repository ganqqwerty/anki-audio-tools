"""E2E tests for DeepFilter comparison and failure paths."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from e2e.editor_audio_generation_helpers import (
    _fake_deep_filter_executable,
    _render_direct_deep_filter_reference,
)
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
    _processing_status_js,
    _sound_filename,
    _wait_for_generated_mp3,
)
from e2e.helpers import click_selector, generate_tone, wait_for_js_condition

DEEP_FILTER_SAMPLE_FIXTURE = (
    Path(__file__).parent / "fixtures" / "audio" / "3d8ca69aee6_input_48k_mono.wav"
)


def test_standard_denoise_menu_matches_direct_deep_filter_output(
    anki_mw,
    ffmpeg_config,
    tmp_path,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / DEEP_FILTER_SAMPLE_FIXTURE.name
    shutil.copyfile(DEEP_FILTER_SAMPLE_FIXTURE, source)
    direct_output = tmp_path / "3d8ca69aee6_input_48k_mono_direct_deep_filter.mp3"
    _render_direct_deep_filter_reference(
        ffmpeg_config,
        source,
        direct_output,
        post_filter=True,
    )

    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        deep_filter_path="",
        deep_filter_post_filter=True,
        show_ffmpeg_commands=True,
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        click_selector(editor.web, _button_selector("aqe:denoise-standard"), timeout=5.0)
        generated_name = _wait_for_generated_mp3(note, media_dir, source.name)
        generated_path = media_dir / generated_name

        ui_bytes = generated_path.read_bytes()
        direct_bytes = direct_output.read_bytes()
        assert ui_bytes == direct_bytes, (
            "Standard denoise menu output differs from direct DeepFilterNet output: "
            f"ui={generated_path} ({len(ui_bytes)} bytes), "
            f"direct={direct_output} ({len(direct_bytes)} bytes)"
        )
    finally:
        editor.set_note(None)
        parent.close()


def test_standard_denoise_failure_leaves_note_unchanged(
    anki_mw,
    ffmpeg_config,
    tmp_path,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_standard_denoise_failure_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=0.8)
    original_field = f"Prompt [sound:{source.name}]"
    fake_deep_filter, deep_filter_log = _fake_deep_filter_executable(tmp_path, fail=True)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        deep_filter_path=str(fake_deep_filter),
        deep_filter_post_filter=True,
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        click_selector(editor.web, _button_selector("aqe:denoise-standard"), timeout=10.0)
        status = wait_for_js_condition(
            editor.web,
            _processing_status_js(),
            lambda value: value is not None
            and value["kind"] == "error"
            and "fake deep-filter failed" in value["text"],
            timeout=10.0,
        )

        assert status["title"] == ""
        assert note.fields[0] == original_field
        assert _sound_filename(note.fields[0]) == source.name
        assert json.loads(deep_filter_log.read_text(encoding="utf-8"))[-1].endswith(
            "input_48k_mono.wav"
        )
        assert not list(media_dir.glob("editor_standard_denoise_failure_source__aqe_*.mp3"))
    finally:
        editor.set_note(None)
        parent.close()
