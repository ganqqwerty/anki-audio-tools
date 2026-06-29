"""E2E tests for marker-guided selected repeat playback."""

from __future__ import annotations

from e2e.editor_chorusing_helpers import (
    _click_chorusing_marker,
)
from e2e.editor_chorusing_playback_helpers import (
    _click_play,
    _configure_play_auto_advance,
)
from e2e.editor_graph_helpers import (
    _wait_for_html_playback,
)
from e2e.editor_playback_helpers import (
    PLAYBACK_INTERVAL_TOLERANCE_MS,
)
from e2e.editor_region_loop_helpers import (
    _force_repeat_wrap,
    _open_tone_editor,
    _shift_drag_region,
    _state,
)
from e2e.helpers import wait_for_js_condition


def test_chorusing_marker_navigation_selects_suffixes_for_normal_play(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, _note, editor, parent, _track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_marker_navigation.wav",
        2.0,
    )
    try:
        markers = _state(
            editor,
            lambda state: state["chorusingBaseStartMs"] == 0
            and state["chorusingBaseEndMs"] == 2000
            and state["chorusingMarkersMs"] == [0, 500, 1000, 1500],
        )

        rightmost = _click_chorusing_next(editor, expected_index=3)
        inserted = _click_chorusing_marker(editor, 0.625, expected_count=5)
        after_insert_next = _click_chorusing_next(editor, expected_index=3)
        longer = _click_chorusing_next(editor, expected_index=2)

        _click_chorusing_next(editor, expected_index=1)
        _click_chorusing_next(editor, expected_index=0)
        full_sentence = _state(
            editor,
            lambda state: state["chorusingActiveMarkerIndex"] == 0
            and state["selectionStartMs"] == 0
            and state["selectionEndMs"] == 2000,
        )
        shorter = _click_chorusing_previous(editor, expected_index=1)

        _click_play(editor)
        playing = _state(
            editor,
            lambda state: state["playbackState"] == "playing"
            and state["playbackStartMs"] == 500
            and state["playbackEndMs"] == 2000
            and state["repeatEnabled"] is False,
        )

        assert markers["chorusingState"] == "stopped"
        assert rightmost["selectionStartMs"] == 1500
        assert rightmost["selectionEndMs"] == 2000
        assert inserted["chorusingMarkersMs"] == [0, 500, 1000, 1250, 1500]
        assert inserted["chorusingActiveStartMs"] == 1500
        assert after_insert_next["chorusingActiveStartMs"] == 1250
        assert longer["chorusingActiveStartMs"] == 1000
        assert full_sentence["chorusingActiveStartMs"] == 0
        assert shorter["chorusingActiveStartMs"] == 500
        assert shorter["selectionStartMs"] == 500
        assert playing["selectionStartMs"] == 500
    finally:
        editor.set_note(None)
        parent.close()


def test_chorusing_auto_advance_walks_suffixes_without_manual_navigation(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, _note, editor, parent, _track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_chorusing_auto_advance.wav",
        2.0,
    )
    try:
        _configure_play_auto_advance(editor, pause_seconds=0.0, repeat_count=2)
        _click_chorusing_next(editor, expected_index=3)
        _click_play(editor)

        initial = _state(
            editor,
            lambda state: state["chorusingActiveMarkerIndex"] == 3
            and state["selectionStartMs"] == 1500
            and state["selectionEndMs"] == 2000
            and state["repeatEnabled"] is True,
        )

        first_repeat = _force_repeat_wrap(editor, 1500)
        first_advance = _force_repeat_wrap(editor, 1000)
        second_repeat = _force_repeat_wrap(editor, 1000)
        second_advance = _force_repeat_wrap(editor, 500)
        third_repeat = _force_repeat_wrap(editor, 500)
        third_advance = _force_repeat_wrap(editor, 0)

        assert initial["chorusingRepeatPassesCompleted"] == 0
        assert first_repeat["chorusingActiveMarkerIndex"] == 3
        assert first_repeat["chorusingRepeatPassesCompleted"] == 1
        assert first_advance["chorusingActiveMarkerIndex"] == 2
        assert first_advance["chorusingRepeatPassesCompleted"] == 0
        assert first_advance["selectionStartMs"] == 1000
        assert second_repeat["chorusingActiveMarkerIndex"] == 2
        assert second_repeat["chorusingRepeatPassesCompleted"] == 1
        assert second_advance["chorusingActiveMarkerIndex"] == 1
        assert second_advance["selectionStartMs"] == 500
        assert third_repeat["chorusingActiveMarkerIndex"] == 1
        assert third_repeat["chorusingRepeatPassesCompleted"] == 1
        assert third_advance["chorusingActiveMarkerIndex"] == 0
        assert third_advance["selectionStartMs"] == 0
        assert third_advance["selectionEndMs"] == 2000
    finally:
        editor.set_note(None)
        parent.close()


def test_chorusing_auto_advance_uses_live_html_progress_boundaries(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, _note, editor, parent, _track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_chorusing_auto_advance_live_boundary.wav",
        2.0,
    )
    try:
        _configure_play_auto_advance(editor, pause_seconds=0.0, repeat_count=3)
        _shift_drag_region(editor, 0.5, 0.75)
        _click_play(editor)

        started = _wait_for_html_playback(
            editor,
            lambda state: abs(state["selectionStartMs"] - 1000) <= PLAYBACK_INTERVAL_TOLERANCE_MS
            and state["selectionEndMs"] == 1500
            and state["repeatEnabled"] is True
            and state["chorusingAutoAdvance"] is True
            and state["chorusingRepeatCount"] == 3,
            timeout=5.0,
        )
        live_advanced = _wait_for_live_auto_advance_or_stuck(
            editor,
            expected_start_ms=500,
            stuck_start_ms=1000,
        )

        assert started["chorusingRepeatPassesCompleted"] == 0
        assert live_advanced["stuckLiveLoopCount"] < 4, live_advanced
        assert abs(live_advanced["selectionStartMs"] - 500) <= PLAYBACK_INTERVAL_TOLERANCE_MS
        assert live_advanced["selectionEndMs"] == 1500
        assert live_advanced["chorusingRepeatPassesCompleted"] == 0
        assert abs(live_advanced["playbackStartMs"] - 500) <= PLAYBACK_INTERVAL_TOLERANCE_MS
    finally:
        editor.set_note(None)
        parent.close()


def test_chorusing_auto_advance_handles_navigation_and_marker_edits(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, _note, editor, parent, _track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_chorusing_auto_advance_mixed.wav",
        2.0,
    )
    try:
        _configure_play_auto_advance(editor, pause_seconds=0.0, repeat_count=2)
        _click_chorusing_next(editor, expected_index=3)
        _click_play(editor)

        first_repeat = _force_repeat_wrap(editor, 1500)
        manual_next = _click_chorusing_next(editor, expected_index=2)
        manual_previous = _click_chorusing_previous(editor, expected_index=3)
        manual_next_again = _click_chorusing_next(editor, expected_index=2)
        repeat_after_manual = _force_repeat_wrap(editor, 1000)

        inserted_left = _click_chorusing_marker(editor, 0.375, expected_count=5)
        advance_to_inserted = _force_repeat_wrap(editor, 750)
        repeat_on_inserted = _force_repeat_wrap(editor, 750)
        removed_current = _click_chorusing_marker(editor, 0.375, expected_count=4)
        advance_after_removal = _force_repeat_wrap(editor, 500)

        assert first_repeat["chorusingRepeatPassesCompleted"] == 1
        assert manual_next["chorusingRepeatPassesCompleted"] == 0
        assert manual_next["selectionStartMs"] == 1000
        assert manual_previous["chorusingRepeatPassesCompleted"] == 0
        assert manual_previous["selectionStartMs"] == 1500
        assert manual_next_again["chorusingRepeatPassesCompleted"] == 0
        assert repeat_after_manual["chorusingRepeatPassesCompleted"] == 1
        assert inserted_left["chorusingMarkersMs"] == [0, 500, 750, 1000, 1500]
        assert inserted_left["chorusingRepeatPassesCompleted"] == 1
        assert inserted_left["selectionStartMs"] == 1000
        assert advance_to_inserted["chorusingActiveStartMs"] == 750
        assert advance_to_inserted["chorusingRepeatPassesCompleted"] == 0
        assert repeat_on_inserted["chorusingRepeatPassesCompleted"] == 1
        assert removed_current["chorusingActiveMarkerIndex"] is None
        assert removed_current["chorusingActiveStartMs"] == 750
        assert removed_current["chorusingMarkersMs"] == [0, 500, 1000, 1500]
        assert removed_current["chorusingRepeatPassesCompleted"] == 1
        assert removed_current["selectionStartMs"] == 750
        assert advance_after_removal["chorusingActiveStartMs"] == 500
        assert advance_after_removal["selectionStartMs"] == 500
        assert advance_after_removal["chorusingRepeatPassesCompleted"] == 0
    finally:
        editor.set_note(None)
        parent.close()


def _click_chorusing_next(editor, *, expected_index: int = 1):
    return wait_for_js_condition(
        editor.web,
        """
        (() => {
          const button = document.querySelector('[data-testid="aqe-button-0-chorusing-next"]');
          if (!button || button.disabled) return null;
          button.click();
          return window.__aqeGraphStateForTest?.(0) || null;
        })()
        """,
        lambda state: state is not None and state["chorusingActiveMarkerIndex"] == expected_index,
        timeout=5.0,
    )


def _click_chorusing_previous(editor, *, expected_index: int = 1):
    return wait_for_js_condition(
        editor.web,
        """
        (() => {
          const button = document.querySelector('[data-testid="aqe-button-0-chorusing-previous"]');
          if (!button || button.disabled) return null;
          button.click();
          return window.__aqeGraphStateForTest?.(0) || null;
        })()
        """,
        lambda state: state is not None and state["chorusingActiveMarkerIndex"] == expected_index,
        timeout=5.0,
    )


def _wait_for_live_auto_advance_or_stuck(
    editor,
    *,
    expected_start_ms: int,
    stuck_start_ms: int,
):
    return wait_for_js_condition(
        editor.web,
        f"""
        (() => {{
          const state = window.__aqeGraphStateForTest?.(0);
          if (!state) return null;
          const key = "__aqeLiveAutoAdvanceProbe";
          const probe = window[key] || {{
            previousProgressMs: null,
            stuckLiveLoopCount: 0,
          }};
          const progressMs = Number(state.progressMs || 0);
          if (
            state.playbackState === "playing"
            && Math.abs(state.playbackStartMs - {stuck_start_ms}) <= {PLAYBACK_INTERVAL_TOLERANCE_MS}
            && probe.previousProgressMs !== null
            && probe.previousProgressMs > {stuck_start_ms + 300}
            && progressMs < {stuck_start_ms + 150}
          ) {{
            probe.stuckLiveLoopCount += 1;
          }}
          probe.previousProgressMs = progressMs;
          window[key] = probe;
          return {{ ...state, stuckLiveLoopCount: probe.stuckLiveLoopCount }};
        }})()
        """,
        lambda state: state is not None
        and state["playbackState"] == "playing"
        and (
            abs(state["selectionStartMs"] - expected_start_ms) <= PLAYBACK_INTERVAL_TOLERANCE_MS
            or state["stuckLiveLoopCount"] >= 4
        ),
        timeout=6.0,
    )
