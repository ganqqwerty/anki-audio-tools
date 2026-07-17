"""E2E tests for selected-region repeat playback behavior."""

from __future__ import annotations

import time

from e2e.editor_graph_helpers import (
    _wait_for_html_playback,
)
from e2e.editor_note_helpers import (
    _button_selector,
)
from e2e.editor_playback_helpers import (
    PLAYBACK_INTERVAL_TOLERANCE_MS,
    _record_fake_playback,
)
from e2e.editor_region_loop_helpers import (
    _force_audio_boundary,
    _force_repeat_wrap,
    _normal_drag,
    _open_tone_editor,
    _set_repeat,
    _shift_drag_region,
    _state,
)
from e2e.helpers import (
    click_selector,
    run_js,
    wait_for_condition,
)


def test_selected_repeat_loops_pauses_restarts_and_can_finish_current_pass(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir, source, _note, editor, parent, track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_region_repeat_middle.wav",
        2.0,
    )
    try:
        _shift_drag_region(editor, 0.25, 0.65)
        _set_repeat(editor, True)

        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _wait_for_html_playback(editor, lambda state: state["progressMs"] >= 500)
            looped = [_force_repeat_wrap(editor, 500) for _ in range(3)]
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            paused = _state(
                editor,
                lambda state: state["playbackState"] == "paused"
                and state["playButtonLabel"] == "Play",
            )
            paused_progress = paused["progressMs"]
            pause_deadline = time.monotonic() + 0.35
            wait_for_condition(
                lambda: time.monotonic() >= pause_deadline,
                timeout=1.0,
                message="short selected repeat pause wait failed",
            )
            frozen = _state(editor)
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            restarted = _wait_for_html_playback(
                editor,
                lambda state: state["playbackStartMs"] == 500
                and 500 <= state["progressMs"] <= 1300,
            )
            _set_repeat(editor, False)
            _force_audio_boundary(editor)
            finished = _state(
                editor,
                lambda state: state["playbackState"] == "stopped"
                and state["cursorMs"] == 500
                and state["repeatEnabled"] is False,
                timeout=5.0,
            )

        assert playback.attempts == []
        assert len(looped) == 3
        assert looped[-1]["playButtonLabel"] == "Pause"
        assert abs(frozen["progressMs"] - paused_progress) < PLAYBACK_INTERVAL_TOLERANCE_MS * 2
        assert restarted["playbackStartMs"] == 500
        assert finished["playbackEndMs"] == 1300
    finally:
        editor.set_note(None)
        parent.close()


def test_selected_repeat_restarts_from_segment_start_after_repositioned_paused_cursor(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir, source, _note, editor, parent, track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_region_repeat_reposition_cursor.wav",
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

        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _wait_for_html_playback(editor, lambda state: state["progressMs"] >= 650)
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _state(
                editor,
                lambda state: state["playbackState"] == "paused"
                and state["playButtonLabel"] == "Play",
            )

            _normal_drag(editor, 0.45, 0.45)
            repositioned = _state(
                editor,
                lambda state: all((
                    state["playbackState"] == "paused",
                    state["cursorMs"] > state["selectionStartMs"] + PLAYBACK_INTERVAL_TOLERANCE_MS,
                    state["cursorMs"] <= state["selectionEndMs"],
                    state["resumeRequiresRestart"] is True,
                )),
            )
            expected_restart_ms = repositioned["selectionStartMs"]

            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            restarted = _wait_for_html_playback(
                editor,
                lambda state: abs(state["playbackStartMs"] - expected_restart_ms)
                <= PLAYBACK_INTERVAL_TOLERANCE_MS
                and abs(state["progressMs"] - expected_restart_ms)
                <= PLAYBACK_INTERVAL_TOLERANCE_MS
                and state["playbackEndMs"] == 1300,
                timeout=5.0,
            )

        assert playback.attempts == []
        assert repositioned["repeatEnabled"] is True
        assert repositioned["selectionStartMs"] == 500
        assert repositioned["selectionEndMs"] == 1300
        assert restarted["playbackRegionMode"] == "selection"
        assert restarted["cursorMs"] == repositioned["cursorMs"]
    finally:
        editor.set_note(None)
        parent.close()
