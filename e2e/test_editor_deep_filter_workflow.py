"""E2E tests for DeepFilter-backed editor commands."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from e2e.conftest import import_runtime_addon_module
from e2e.editor_audio_generation_helpers import (
    _fake_deep_filter_executable,
)
from e2e.editor_graph_helpers import _click_graph_and_wait, _wait_for_visualizer_track
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
    _sound_filename,
    _three_audio_field_note,
    _wait_for_generated_mp3,
    _wait_for_status_flow,
)
from e2e.helpers import (
    click_selector,
    generate_tone,
    wait_for_condition,
    wait_for_js_condition,
)

DEEP_FILTER_SAMPLE_FIXTURE = (
    Path(__file__).parent / "fixtures" / "audio" / "3d8ca69aee6_input_48k_mono.wav"
)


def test_standard_denoise_menu_runs_deep_filter_and_is_undoable(
    anki_mw,
    ffmpeg_config,
    tmp_path,
) -> None:
    probe_duration_ms = import_runtime_addon_module(".audio_processor").probe_duration_ms

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_standard_denoise_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.2)
    original_bytes = source.read_bytes()
    fake_deep_filter, deep_filter_log = _fake_deep_filter_executable(tmp_path)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        deep_filter_path=str(fake_deep_filter),
        deep_filter_post_filter=True,
        show_ffmpeg_commands=True,
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        click_selector(editor.web, _button_selector("aqe:denoise-standard"), timeout=5.0)
        generated_name = _wait_for_generated_mp3(note, media_dir, source.name)
        _wait_for_status_flow(
            editor,
            lambda status: status["text"] == "Cleaned audio with Standard.",
            timeout=10.0,
        )

        generated_path = media_dir / generated_name
        assert generated_path.is_file()
        assert generated_name.endswith(".mp3")
        assert source.read_bytes() == original_bytes
        assert probe_duration_ms(generated_path, ffmpeg_config) > 0
        assert abs(probe_duration_ms(generated_path, ffmpeg_config) - 1200) < 250

        deep_filter_args = json.loads(deep_filter_log.read_text(encoding="utf-8"))
        assert "-D" in deep_filter_args
        assert "--pf" in deep_filter_args
        assert "-o" in deep_filter_args
        output_dir = Path(deep_filter_args[deep_filter_args.index("-o") + 1])
        assert output_dir.name == "deep_filter_output"
        assert Path(deep_filter_args[-1]).name == "input_48k_mono.wav"

        _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == generated_name and value["cursorMs"] == 0,
            timeout=10.0,
        )

        click_selector(editor.web, _button_selector("aqe:undo"), timeout=5.0)
        wait_for_condition(
            lambda: _sound_filename(note.fields[0]) == source.name,
            timeout=5.0,
            message="Undo did not restore the original audio reference after standard denoise",
        )
        _wait_for_status_flow(
            editor,
            lambda status: status["text"] == "Undid: Original audio.",
            timeout=10.0,
        )
    finally:
        editor.set_note(None)
        parent.close()


def test_standard_denoise_menu_click_then_undo_and_redo_restores_reference(
    anki_mw,
    ffmpeg_config,
    tmp_path,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_standard_denoise_menu_undo_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.2)
    fake_deep_filter, _deep_filter_log = _fake_deep_filter_executable(tmp_path)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        deep_filter_path=str(fake_deep_filter),
        deep_filter_post_filter=True,
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        click_selector(editor.web, '[data-testid="aqe-split-0-denoise-standard-menu"]', timeout=10.0)
        wait_for_js_condition(
            editor.web,
            'document.querySelector(\'[data-testid="aqe-split-0-denoise-standard-popover"]\') !== null',
            lambda value: value is True,
            timeout=5.0,
        )
        click_selector(editor.web, _button_selector("aqe:denoise-standard"), timeout=5.0)
        generated_name = _wait_for_generated_mp3(note, media_dir, source.name)
        _wait_for_status_flow(
            editor,
            lambda status: status["text"] == "Cleaned audio with Standard.",
            timeout=10.0,
        )

        click_selector(editor.web, _button_selector("aqe:undo"), timeout=5.0)
        wait_for_condition(
            lambda: _sound_filename(note.fields[0]) == source.name,
            timeout=5.0,
            message="Undo after Denoise > Standard reported nothing to undo",
        )
        _wait_for_status_flow(
            editor,
            lambda status: status["text"] == "Undid: Original audio.",
            timeout=10.0,
        )

        click_selector(editor.web, _button_selector("aqe:redo"), timeout=5.0)
        wait_for_condition(
            lambda: _sound_filename(note.fields[0]) == generated_name,
            timeout=5.0,
            message="Redo did not restore the Standard denoise output",
        )
        _wait_for_status_flow(
            editor,
            lambda status: status["text"] == "Redid: Cleaned audio with Standard.",
            timeout=10.0,
        )
    finally:
        editor.set_note(None)
        parent.close()


def test_standard_denoise_menu_undo_with_user_meta_settings(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_standard_denoise_user_meta_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.2)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        debug_logging=True,
        deep_filter_path="",
        deep_filter_post_filter=True,
        repeat_playback_by_default=False,
        show_graph_by_default=True,
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == source.name,
            timeout=10.0,
        )
        click_selector(editor.web, '[data-testid="aqe-split-0-denoise-standard-menu"]', timeout=10.0)
        wait_for_js_condition(
            editor.web,
            'document.querySelector(\'[data-testid="aqe-split-0-denoise-standard-popover"]\') !== null',
            lambda value: value is True,
            timeout=5.0,
        )
        click_selector(editor.web, _button_selector("aqe:denoise-standard"), timeout=5.0)
        generated_name = _wait_for_generated_mp3(note, media_dir, source.name)
        _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == generated_name and value["cursorMs"] == 0,
            timeout=10.0,
        )

        click_selector(editor.web, _button_selector("aqe:undo"), timeout=5.0)
        wait_for_condition(
            lambda: _sound_filename(note.fields[0]) == source.name,
            timeout=5.0,
            message="Undo after Denoise > Standard failed with user meta settings",
        )
    finally:
        editor.set_note(None)
        parent.close()


def test_standard_denoise_menu_undo_with_user_meta_settings_on_local_sample(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / DEEP_FILTER_SAMPLE_FIXTURE.name
    shutil.copyfile(DEEP_FILTER_SAMPLE_FIXTURE, source)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        debug_logging=True,
        deep_filter_path="",
        deep_filter_post_filter=True,
        repeat_playback_by_default=False,
        show_graph_by_default=True,
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == source.name,
            timeout=10.0,
        )
        click_selector(editor.web, '[data-testid="aqe-split-0-denoise-standard-menu"]', timeout=10.0)
        wait_for_js_condition(
            editor.web,
            'document.querySelector(\'[data-testid="aqe-split-0-denoise-standard-popover"]\') !== null',
            lambda value: value is True,
            timeout=5.0,
        )
        click_selector(editor.web, _button_selector("aqe:denoise-standard"), timeout=5.0)
        generated_name = _wait_for_generated_mp3(note, media_dir, source.name)
        _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == generated_name and value["cursorMs"] == 0,
            timeout=10.0,
        )

        click_selector(editor.web, _button_selector("aqe:undo"), timeout=5.0)
        wait_for_condition(
            lambda: _sound_filename(note.fields[0]) == source.name,
            timeout=5.0,
            message="Undo after Denoise > Standard failed on the local sample",
        )
    finally:
        editor.set_note(None)
        parent.close()


def test_standard_denoise_menu_undo_with_user_meta_settings_and_multiple_audio_fields(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    sources = (
        media_dir / "editor_standard_denoise_multi_one.wav",
        media_dir / "editor_standard_denoise_multi_two.wav",
        media_dir / "editor_standard_denoise_multi_three.wav",
    )
    for index, source in enumerate(sources):
        generate_tone(ffmpeg_config, source, duration_s=0.8 + index * 0.1)
    note = _three_audio_field_note(anki_mw, tuple(source.name for source in sources))
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        debug_logging=True,
        deep_filter_path="",
        deep_filter_post_filter=True,
        repeat_playback_by_default=False,
        show_graph_by_default=True,
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == sources[2].name,
            timeout=10.0,
            ord_=2,
        )
        click_selector(editor.web, '[data-testid="aqe-split-0-denoise-standard-menu"]', timeout=10.0)
        wait_for_js_condition(
            editor.web,
            'document.querySelector(\'[data-testid="aqe-split-0-denoise-standard-popover"]\') !== null',
            lambda value: value is True,
            timeout=5.0,
        )
        click_selector(editor.web, _button_selector("aqe:denoise-standard"), timeout=5.0)
        generated_name = _wait_for_generated_mp3(note, media_dir, sources[0].name)
        _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == sources[2].name,
            timeout=10.0,
            ord_=2,
        )

        click_selector(editor.web, _button_selector("aqe:undo"), timeout=5.0)
        wait_for_condition(
            lambda: _sound_filename(note.fields[0]) == sources[0].name,
            timeout=5.0,
            message=(
                "Undo after Denoise > Standard failed after graph auto-analysis "
                f"advanced past {generated_name}"
            ),
        )
    finally:
        editor.set_note(None)
        parent.close()
