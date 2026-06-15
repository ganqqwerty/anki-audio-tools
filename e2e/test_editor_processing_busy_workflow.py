"""E2E tests for editor processing busy-state locking."""

from __future__ import annotations

import json
from pathlib import Path

from e2e.editor_graph_helpers import _click_graph_and_wait
from e2e.editor_note_helpers import (
    DEFAULT_VISIBLE_EDITOR_BUTTONS,
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

        generated_for_source = list(media_dir.glob("editor_fast_click_source__aqe_*"))
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
            """
            (() => {
              const slowerButton = document.querySelector('[data-testid="aqe-button-0-faster"]');
              const playbackButton = document.querySelector('[data-testid="aqe-button-0-play"]');
              const showFileButton = document.querySelector('[data-testid="aqe-button-0-show-file"]');
              return {
                allControlsEnabled:
                  !!slowerButton && !!playbackButton && !!showFileButton
                  && slowerButton.disabled === false
                  && playbackButton.disabled === false
                  && showFileButton.disabled === false,
              };
            })()
            """,
            lambda state: state is not None and state["allControlsEnabled"] is True,
            timeout=5.0,
        )

        assert locked["lockedAfterFirst"] is True
        assert locked["cursor"] == "not-allowed"
        assert locked["opacity"] < 0.7
        assert locked["borderStyle"] == "dashed"
        assert unlocked["allControlsEnabled"] is True
        assert _sound_filename(note.fields[0]) == generated_name
        assert _sound_filename(note.fields[1]) == sources[1].name
        assert _sound_filename(note.fields[2]) == sources[2].name
        assert list(media_dir.glob("editor_three_fields_one__aqe_*")) == [media_dir / generated_name]
    finally:
        editor.set_note(None)
        parent.close()


def test_processing_command_locks_playback_recording_history_graph_and_modification_controls(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    sources = (
        media_dir / "editor_busy_controls_one.wav",
        media_dir / "editor_busy_controls_two.wav",
        media_dir / "editor_busy_controls_three.wav",
    )
    for source in sources:
        generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _three_audio_field_note(anki_mw, tuple(source.name for source in sources))
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        visible_editor_buttons=[
            *DEFAULT_VISIBLE_EDITOR_BUTTONS,
            "aqe:record-voice",
            "aqe:play-recording",
            "aqe:share-recording",
            "aqe:show-recording-file",
        ],
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == sources[0].name, ord_=0)
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == sources[1].name, ord_=1)
        wait_for_js_condition(
            editor.web,
            """
            (() => {
              const record0 = document.querySelector('[data-testid="aqe-button-0-record-voice"]');
              const record1 = document.querySelector('[data-testid="aqe-button-1-record-voice"]');
              return !!record0 && !!record1 && !record0.disabled && !record1.disabled;
            })()
            """,
            lambda value: value is True,
            timeout=5.0,
        )

        run_js(
            editor.web,
            """
            window.__aqeSetHistorySnapshot(0, {
              canRedo: false,
              canUndo: true,
              redoItems: [],
              undoItems: [{ id: "seed", label: "Seeded history" }],
            });
            """,
        )
        wait_for_js_condition(
            editor.web,
            """
            (() => {
              const undo = document.querySelector('[data-testid="aqe-button-0-undo"]');
              const record1 = document.querySelector('[data-testid="aqe-button-1-record-voice"]');
              return !!undo && !!record1 && !undo.disabled && !record1.disabled;
            })()
            """,
            lambda value: value is True,
            timeout=5.0,
        )

        locked = wait_for_js_condition(
            editor.web,
            """
            (() => {
              const button = (ord, slug) => document.querySelector(`[data-testid="aqe-button-${ord}-${slug}"]`);
              button(0, "graph").click();
              return {
                field0Playback: button(0, "play")?.disabled === true,
                field1Playback: button(1, "play")?.disabled === true,
                field1Recording: button(1, "record-voice")?.disabled === true,
                field0History: button(0, "undo")?.disabled === true,
                field1Graph: button(1, "graph")?.disabled === true,
                field2Modification: button(2, "volume-up")?.disabled === true,
              };
            })()
            """,
            lambda state: state is not None and all(state.values()),
            timeout=5.0,
        )
        unlocked = wait_for_js_condition(
            editor.web,
            """
            (() => {
              const button = (ord, slug) => document.querySelector(`[data-testid="aqe-button-${ord}-${slug}"]`);
              return {
                field0Playback: button(0, "play")?.disabled === false,
                field1Recording: button(1, "record-voice")?.disabled === false,
                field0History: button(0, "undo")?.disabled === false,
                field1Graph: button(1, "graph")?.disabled === false,
                field2Modification: button(2, "volume-up")?.disabled === false,
              };
            })()
            """,
            lambda state: state is not None and all(state.values()),
            timeout=5.0,
        )

        assert locked == {
            "field0Playback": True,
            "field1Playback": True,
            "field1Recording": True,
            "field0History": True,
            "field1Graph": True,
            "field2Modification": True,
        }
        assert unlocked == {
            "field0Playback": True,
            "field1Recording": True,
            "field0History": True,
            "field1Graph": True,
            "field2Modification": True,
        }
        assert _sound_filename(note.fields[0]) == sources[0].name
        assert _sound_filename(note.fields[1]) == sources[1].name
        assert _sound_filename(note.fields[2]) == sources[2].name
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
        click_selector(editor.web, _button_selector("aqe:undo"), timeout=5.0)

        final_status = _wait_for_status_flow(
            editor,
            lambda status: status["text"] in {
                "Increased volume by 15 dB.",
                "Undid: Original audio.",
            },
            timeout=10.0,
        )

        if final_status["text"] == "Undid: Original audio.":
            assert _sound_filename(note.fields[0]) == source.name
        else:
            assert _sound_filename(note.fields[0]) != source.name
    finally:
        editor.set_note(None)
        parent.close()
