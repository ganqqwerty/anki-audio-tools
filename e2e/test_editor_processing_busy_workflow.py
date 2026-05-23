"""E2E tests for editor processing busy-state locking."""

from __future__ import annotations

import json
from pathlib import Path

from e2e.editor_graph_helpers import _graph_state_js
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
    _sound_filename,
    _three_audio_field_note,
    _wait_for_generated_mp3,
    _wait_for_status,
    _wait_for_status_flow,
)
from e2e.helpers import (
    click_selector,
    generate_tone,
    run_js,
    wait_for_js_condition,
    wait_for_selector,
)


def test_fast_clicks_are_ignored_while_processing(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_fast_click_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=3.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        selector = _button_selector("aqe:faster")
        wait_for_selector(editor.web, selector, timeout=10.0)
        run_js(
            editor.web,
            f"""
            const button = document.querySelector({json.dumps(selector)});
            for (let i = 0; i < 5; i++) button.click();
            """,
        )
        generated_name = _wait_for_generated_mp3(note, media_dir, source.name)

        generated_for_source = list(media_dir.glob("editor_fast_click_source__aqe_*.mp3"))
        assert generated_for_source == [media_dir / generated_name]
        assert (media_dir / generated_name).is_file()
    finally:
        editor.set_note(None)
        parent.close()


def test_three_audio_fields_fast_cross_clicks_lock_globally_and_do_not_corrupt_fields(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    sources = (
        media_dir / "editor_three_fields_one.wav",
        media_dir / "editor_three_fields_two.wav",
        media_dir / "editor_three_fields_three.wav",
    )
    for source in sources:
        generate_tone(ffmpeg_config, source, duration_s=3.0)
    note = _three_audio_field_note(anki_mw, tuple(source.name for source in sources))
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:faster", 0), timeout=10.0)
        wait_for_selector(editor.web, _button_selector("aqe:faster", 1), timeout=10.0)
        wait_for_selector(editor.web, _button_selector("aqe:volume-up", 2), timeout=10.0)
        locked = wait_for_js_condition(
            editor.web,
            """
            (() => {
              document.querySelector('[data-testid="aqe-button-0-faster"]').click();
              const lockedAfterFirst = Array.from(document.querySelectorAll('.aqe-button')).every((button) => button.disabled);
              const firstButton = document.querySelector('[data-testid="aqe-button-0-faster"]');
              const controls = document.querySelector('[data-testid="aqe-controls-0"]');
              const buttonStyle = getComputedStyle(firstButton);
              const controlsStyle = getComputedStyle(controls);
              document.querySelector('[data-testid="aqe-button-1-faster"]').click();
              document.querySelector('[data-testid="aqe-button-2-volume-up"]').click();
              return {
                lockedAfterFirst,
                cursor: buttonStyle.cursor,
                opacity: Number(buttonStyle.opacity),
                borderStyle: controlsStyle.borderTopStyle
              };
            })()
            """,
            lambda value: value is not None and value["lockedAfterFirst"] is True,
            timeout=5.0,
        )
        generated_name = _wait_for_generated_mp3(note, media_dir, sources[0].name, field_index=0)
        unlocked = wait_for_js_condition(
            editor.web,
            _graph_state_js(0),
            lambda state: state is not None and state["allButtonsDisabled"] is False,
            timeout=5.0,
        )

        assert locked["lockedAfterFirst"] is True
        assert locked["cursor"] == "not-allowed"
        assert locked["opacity"] < 0.7
        assert locked["borderStyle"] == "dashed"
        assert unlocked["allButtonsDisabled"] is False
        assert _sound_filename(note.fields[0]) == generated_name
        assert _sound_filename(note.fields[1]) == sources[1].name
        assert _sound_filename(note.fields[2]) == sources[2].name
        assert list(media_dir.glob("editor_three_fields_one__aqe_*.mp3")) == [media_dir / generated_name]
    finally:
        editor.set_note(None)
        parent.close()


def test_still_processing_status_is_replaced_after_mid_render_undo_request(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_still_processing_volume_undo.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:volume-up"), timeout=10.0)
        click_selector(editor.web, _button_selector("aqe:volume-up"), timeout=5.0)
        editor.onBridgeCmd("aqe:undo")

        _wait_for_status(
            editor,
            lambda status: status is not None
            and status["kind"] == "processing"
            and status["text"] == "Still processing. Please wait.",
            timeout=10.0,
        )
        generated_name = _wait_for_generated_mp3(note, media_dir, source.name)
        final_status = _wait_for_status_flow(
            editor,
            lambda status: status["text"] == "Increased volume by 3 dB.",
            timeout=10.0,
        )

        assert generated_name != source.name
        assert final_status["text"] == "Increased volume by 3 dB."
    finally:
        editor.set_note(None)
        parent.close()
