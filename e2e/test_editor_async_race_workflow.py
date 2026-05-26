from __future__ import annotations

from pathlib import Path

import pytest

from .conftest import runtime_addon_import_path
from .editor_graph_helpers import _graph_state_js, _wait_for_visualizer_track
from .editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
    _sound_filename,
    _three_audio_field_note,
)
from .editor_region_loop_helpers import _shift_drag_region
from .helpers import (
    click_selector,
    generate_tone,
    wait_for_js_condition,
    wait_for_selector,
)
from .race_helpers import (
    DelayedRenderer,
    assert_note_field,
    generated_aqe_files,
    pump_events_for,
)


def test_stale_standard_render_does_not_mutate_new_note_or_write_media(
    anki_mw,
    ffmpeg_config,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    before_generated = set(generated_aqe_files(media_dir))
    first_audio = media_dir / "aqe_race_first.wav"
    second_audio = media_dir / "aqe_race_second.wav"
    generate_tone(ffmpeg_config, first_audio, duration_s=0.35)
    generate_tone(ffmpeg_config, second_audio, duration_s=0.35)
    note_a = _basic_audio_note(anki_mw, first_audio.name)
    note_b = _basic_audio_note(anki_mw, second_audio.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)
    editor, parent = _open_editor(anki_mw, note_a)

    delayed = DelayedRenderer()
    try:
        wait_for_selector(editor.web, _button_selector("aqe:faster"))
        monkeypatch.setattr(
            runtime_addon_import_path(".editor_dependencies", "render_audio"),
            delayed.render_audio,
        )

        click_selector(editor.web, _button_selector("aqe:faster"))
        delayed.wait_started()
        editor.set_note(note_b, hide=False, focusTo=0)
        wait_for_selector(editor.web, _button_selector("aqe:faster"))
        delayed.allow_completion()
        pump_events_for(1.0)

        assert _sound_filename(note_a.fields[0]) == first_audio.name
        assert _sound_filename(note_b.fields[0]) == second_audio.name
        assert set(generated_aqe_files(media_dir)) == before_generated
    finally:
        editor.set_note(None)
        parent.close()


def test_stale_region_delete_does_not_mutate_new_field_or_write_media(
    anki_mw,
    ffmpeg_config,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    before_generated = set(generated_aqe_files(media_dir))
    first_audio = media_dir / "aqe_region_race_first.wav"
    second_audio = media_dir / "aqe_region_race_second.wav"
    third_audio = media_dir / "aqe_region_race_third.wav"
    generate_tone(ffmpeg_config, first_audio, duration_s=0.9)
    generate_tone(ffmpeg_config, second_audio, duration_s=0.9)
    generate_tone(ffmpeg_config, third_audio, duration_s=0.9)
    note = _three_audio_field_note(anki_mw, (first_audio.name, second_audio.name, third_audio.name))
    original_fields = list(note.fields)
    _configure_ffmpeg(anki_mw, ffmpeg_config, show_graph_by_default=True)
    editor, parent = _open_editor(anki_mw, note)

    delayed = DelayedRenderer()
    try:
        _wait_for_visualizer_track(editor, lambda value: value["sourceFilename"] == first_audio.name, ord_=0)
        _wait_for_visualizer_track(editor, lambda value: value["sourceFilename"] == second_audio.name, ord_=1)
        _wait_for_visualizer_track(editor, lambda value: value["sourceFilename"] == third_audio.name, ord_=2)
        _shift_drag_region(editor, 0.2, 0.5, ord_=0)
        wait_for_js_condition(
            editor.web,
            _graph_state_js(0),
            lambda state: state is not None and state["selectionActive"] is True,
            timeout=5.0,
        )
        monkeypatch.setattr(
            runtime_addon_import_path(".editor_dependencies", "render_audio_region_deleted"),
            delayed.render_region,
        )

        click_selector(editor.web, _button_selector("aqe:delete-selection", ord_=0))
        delayed.wait_started()
        editor.currentField = 1
        delayed.allow_completion()
        pump_events_for(1.0)

        assert list(note.fields) == original_fields
        assert_note_field(note, 1, original_fields[1])
        assert set(generated_aqe_files(media_dir)) == before_generated
    finally:
        editor.set_note(None)
        parent.close()
