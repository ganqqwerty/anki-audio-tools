"""E2E coverage for cursor, selection, playback, repeat, and zoom interactions."""

from __future__ import annotations

from e2e.editor_graph_helpers import (
    _drag_cursor_to_ratio,
    _wait_for_html_playback,
)
from e2e.editor_note_helpers import (
    _button_selector,
    _sound_filename,
    _wait_for_generated_mp3,
)
from e2e.editor_playback_helpers import (
    PLAYBACK_INTERVAL_TOLERANCE_MS,
    _record_fake_playback,
)
from e2e.editor_region_loop_helpers import (
    _force_audio_boundary,
    _normal_drag,
    _open_tone_editor,
    _set_repeat,
    _shift_click_region,
    _shift_drag_region,
    _state,
)
from e2e.helpers import (
    click_selector,
    run_js,
)


def test_full_cover_repeat_playback_starts_from_moved_cursor(anki_mw, ffmpeg_config) -> None:
    media_dir, source, _note, editor, parent, track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_cursor_full_repeat.wav",
        2.0,
    )
    try:
        _drag_cursor_to_ratio(editor, 0.5)
        positioned = _state(
            editor,
            lambda state: abs(state["cursorMs"] - 1000) <= PLAYBACK_INTERVAL_TOLERANCE_MS,
        )
        _set_repeat(editor, True)

        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            started = _wait_for_html_playback(
                editor,
                lambda state: abs(state["playbackStartMs"] - positioned["cursorMs"])
                <= PLAYBACK_INTERVAL_TOLERANCE_MS
                and state["repeatEnabled"] is True,
                timeout=5.0,
            )

        assert playback.attempts == []
        assert abs(started["cursorMs"] - positioned["cursorMs"]) <= PLAYBACK_INTERVAL_TOLERANCE_MS
        assert started["playbackEndMs"] == round(track["durationMs"])
        assert started["selectionActive"] is True
    finally:
        editor.set_note(None)
        parent.close()


def test_paused_selected_one_shot_reposition_restarts_and_completion_resets(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir, source, _note, editor, parent, track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_cursor_selected_pause_reposition.wav",
        2.0,
    )
    try:
        _shift_drag_region(editor, 0.25, 0.75)

        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _wait_for_html_playback(editor, lambda state: state["progressMs"] >= 600)
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _state(editor, lambda state: state["playbackState"] == "paused")
            _normal_drag(editor, 0.5, 0.5)
            repositioned = _state(
                editor,
                lambda state: state["playbackState"] == "paused"
                and abs(state["cursorMs"] - 1000) <= PLAYBACK_INTERVAL_TOLERANCE_MS
                and state["resumeRequiresRestart"] is True,
            )

            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            restarted = _wait_for_html_playback(
                editor,
                lambda state: abs(state["playbackStartMs"] - repositioned["cursorMs"])
                <= PLAYBACK_INTERVAL_TOLERANCE_MS
                and state["playbackEndMs"] == 1500,
                timeout=5.0,
            )
            _force_audio_boundary(editor)
            finished = _state(
                editor,
                lambda state: state["playbackState"] == "stopped"
                and abs(state["cursorMs"] - 500) <= PLAYBACK_INTERVAL_TOLERANCE_MS,
                timeout=5.0,
            )

        assert playback.attempts == []
        assert restarted["playbackRegionMode"] == "selection"
        assert finished["selectionStartMs"] == 500
    finally:
        editor.set_note(None)
        parent.close()


def test_paused_full_playback_uses_new_selection_start_after_shift_drag(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir, source, _note, editor, parent, track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_cursor_full_pause_then_selection.wav",
        2.0,
    )
    try:
        _drag_cursor_to_ratio(editor, 0.4)

        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _wait_for_html_playback(editor, lambda state: state["progressMs"] >= 800)
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _state(editor, lambda state: state["playbackState"] == "paused")

            _shift_drag_region(editor, 0.25, 0.65)
            selected = _state(
                editor,
                lambda state: state["playbackState"] == "paused"
                and state["selectionStartMs"] == 500
                and state["selectionEndMs"] == 1300
                and state["resumeRequiresRestart"] is True,
            )

            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            restarted = _wait_for_html_playback(
                editor,
                lambda state: state["playbackStartMs"] == 500
                and state["playbackEndMs"] == 1300,
                timeout=5.0,
            )
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _state(editor, lambda state: state["playbackState"] == "paused")

        assert playback.attempts == []
        assert selected["cursorMs"] == 500
        assert restarted["playbackRegionMode"] == "selection"
    finally:
        editor.set_note(None)
        parent.close()


def test_clearing_selection_while_paused_replays_full_audio_from_cursor(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir, source, _note, editor, parent, track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_cursor_clear_selection_paused.wav",
        2.0,
    )
    try:
        _shift_drag_region(editor, 0.25, 0.65)

        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _wait_for_html_playback(editor, lambda state: state["progressMs"] >= 650)
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _state(editor, lambda state: state["playbackState"] == "paused")
            _normal_drag(editor, 0.45, 0.45)
            repositioned = _state(
                editor,
                lambda state: all((
                    state["playbackState"] == "paused",
                    state["cursorMs"] > 500,
                    state["cursorMs"] < 1300,
                )),
            )
            _shift_click_region(editor, 0.45)
            cleared = _state(
                editor,
                lambda state: state["selectionActive"] is False
                and state["playbackRegionMode"] == "full",
            )

            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            restarted = _wait_for_html_playback(
                editor,
                lambda state: abs(state["playbackStartMs"] - repositioned["cursorMs"])
                <= PLAYBACK_INTERVAL_TOLERANCE_MS
                and state["playbackEndMs"] == 2000
                and state["playbackRegionMode"] == "full",
                timeout=5.0,
            )

        assert playback.attempts == []
        assert cleared["cursorMs"] == repositioned["cursorMs"]
        assert restarted["selectionActive"] is False
    finally:
        editor.set_note(None)
        parent.close()


def test_zoomed_selected_playback_pans_to_offscreen_selection_start(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir, source, _note, editor, parent, track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_cursor_zoomed_selection_play.wav",
        2.0,
    )
    try:
        _shift_drag_region(editor, 0.25, 0.65)
        run_js(
            editor.web,
            """
            (() => {
              window.__aqeSetTimeViewportForTest?.(0, 1400, 2000);
              return true;
            })()
            """,
        )
        _state(
            editor,
            lambda state: state["timecodeFlagVisible"] is False
            and state["viewportStartMs"] == 1400,
        )

        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            followed = _wait_for_html_playback(
                editor,
                lambda state: all((
                    state["playbackStartMs"] == 500,
                    state["selectionStartMs"] == 500,
                    state["selectionEndMs"] == 1300,
                    state["viewportStartMs"] <= 500,
                    state["viewportEndMs"] >= 500,
                    state["timecodeFlagVisible"] is True,
                )),
                timeout=5.0,
            )

        assert playback.attempts == []
        assert followed["playbackRegionMode"] == "selection"
    finally:
        editor.set_note(None)
        parent.close()


def test_zoomed_selected_repeat_stops_before_transformation_and_redraws_cleanly(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir, source, note, editor, parent, track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_cursor_zoomed_repeat_transform.wav",
        2.0,
    )
    try:
        _shift_drag_region(editor, 0.25, 0.65)
        _set_repeat(editor, True)
        run_js(
            editor.web,
            """
            (() => {
              window.__aqeSetTimeViewportForTest?.(0, 400, 1400);
              return true;
            })()
            """,
        )
        previous_name = _sound_filename(note.fields[0])

        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _wait_for_html_playback(editor, lambda state: state["progressMs"] >= 650)
            click_selector(editor.web, _button_selector("aqe:volume-up"), timeout=5.0)
            generated_name = _wait_for_generated_mp3(note, media_dir, previous_name)
            redrawn = _state(
                editor,
                lambda state: state["sourceFilename"] == generated_name
                and state["playbackState"] == "stopped"
                and state["allButtonsDisabled"] is False
                and state["repeatEnabled"] is True
                and state["selectionActive"] is True
                and state["selectionStartMs"] == 0
                and abs(state["selectionEndMs"] - state["durationMs"]) <= 1
                and state["viewportStartMs"] == 0
                and state["viewportEndMs"] > state["viewportStartMs"],
                timeout=10.0,
            )

        assert playback.attempts == []
        assert redrawn["sourceFilename"] == generated_name
    finally:
        editor.set_note(None)
        parent.close()
