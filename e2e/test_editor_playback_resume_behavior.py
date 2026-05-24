"""Playback resume and restart e2e coverage."""

from __future__ import annotations

from pathlib import Path

from .editor_graph_helpers import (
    _click_graph_and_wait,
    _drag_cursor_to_ratio,
    _graph_state_js,
    _install_html_audio_test_driver,
    _wait_for_html_playback,
)
from .editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
)
from .editor_playback_helpers import (
    PLAYBACK_INTERVAL_TOLERANCE_MS,
    _record_fake_playback,
    _shift_click_region,
)
from .helpers import (
    click_selector,
    generate_tone,
    run_js,
    wait_for_js_condition,
)


def test_playback_completion_clears_status_and_returns_cursor_to_anchor(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_playback_finish_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        track = _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        _install_html_audio_test_driver(editor)
        _shift_click_region(editor, 0.5)
        wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda state: state is not None and state["selectionActive"] is False,
            timeout=5.0,
        )
        run_js(editor.web, "window.__aqeSetCursorForTest(0, 300, false)")
        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _wait_for_html_playback(
                editor,
                lambda state: state["audioClockCurrentMs"] >= 300 - PLAYBACK_INTERVAL_TOLERANCE_MS,
            )
            finished = wait_for_js_condition(
                editor.web,
                """
                (() => {
                  const state = window.__aqeGraphStateForTest ? window.__aqeGraphStateForTest(0) : null;
                  const status = document.querySelector('.aqe-controls[data-aqe-field-ord="0"] .aqe-status')?.textContent || "";
                  return state ? { ...state, status } : null;
                })()
                """,
                lambda state: state is not None
                and state["playbackState"] == "stopped"
                and state["playButtonLabel"] == "Play"
                and state["status"] == ""
                and state["cursorMs"] == 300,
                timeout=5.0,
            )

        assert finished["anchorMs"] == 300
        assert playback.attempts == []
    finally:
        editor.set_note(None)
        parent.close()


def test_drag_while_playing_restarts_playback_from_released_cursor(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_drag_while_playing_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        track = _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        _install_html_audio_test_driver(editor)
        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _wait_for_html_playback(editor, lambda state: state["progressMs"] >= 250)
            _drag_cursor_to_ratio(editor, 0.75)
            restarted = _wait_for_html_playback(
                editor,
                lambda state: 1400 <= state["anchorMs"] <= 1600
                and state["audioClockCurrentMs"] >= state["anchorMs"] - PLAYBACK_INTERVAL_TOLERANCE_MS,
            )

        assert playback.attempts == []
        assert restarted["playButtonLabel"] == "Pause"
        assert abs(restarted["progressMs"] - restarted["audioClockCurrentMs"]) <= PLAYBACK_INTERVAL_TOLERANCE_MS * 2
    finally:
        editor.set_note(None)
        parent.close()
