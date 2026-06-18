"""E2E tests for graph chorusing practice."""

from __future__ import annotations

from e2e.editor_chorusing_markers_workflow import (
    _click_chorusing_marker,
    _click_chorusing_practice,
)
from e2e.editor_region_loop_helpers import (
    _force_repeat_wrap,
    _open_tone_editor,
    _shift_drag_region,
    _state,
)
from e2e.helpers import run_js, wait_for_js_condition


def test_chorusing_practice_loops_suffixes_and_pauses_for_normal_play(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, _note, editor, parent, _track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_chorusing_practice.wav",
        2.0,
    )
    try:
        _shift_drag_region(editor, 0.2, 0.8)
        markers = _state(
            editor,
            lambda state: state["selectionStartMs"] == 400
            and state["selectionEndMs"] == 1600
            and state["chorusingBaseStartMs"] == 0
            and state["chorusingBaseEndMs"] == 2000
            and state["chorusingMarkersMs"] == [0, 500, 1000, 1500],
        )

        _click_chorusing_practice(editor)
        playing = _state(
            editor,
            lambda state: state["chorusingState"] == "playing"
            and state["selectionStartMs"] == 1500
            and state["selectionEndMs"] == 2000
            and state["playbackStartMs"] == 1500
            and state["playbackEndMs"] == 2000
            and state["repeatEnabled"] is True,
        )
        status_text = wait_for_js_condition(
            editor.web,
            "document.querySelector('[data-testid=\"aqe-controls-0\"] .aqe-status')?.textContent || ''",
            lambda value: "Practice mode. Use the toolbar buttons for chorusing." in value,
            timeout=5.0,
        )
        wrapped = _force_repeat_wrap(editor, 1500)

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

        run_js(editor.web, "document.querySelector('[data-testid=\"aqe-button-0-play\"]')?.click()")
        paused = _state(
            editor,
            lambda state: state["chorusingState"] == "paused"
            and state["repeatEnabled"] is False,
        )

        assert markers["chorusingState"] == "stopped"
        assert "Playing from 1.50s" in status_text
        assert playing["chorusingBaseStartMs"] == 0
        assert playing["chorusingMarkersMs"] == [0, 500, 1000, 1500]
        assert playing["chorusingActiveStartMs"] == 1500
        assert wrapped["chorusingActiveMarkerIndex"] == 3
        assert inserted["chorusingMarkersMs"] == [0, 500, 1000, 1250, 1500]
        assert inserted["chorusingActiveStartMs"] == 1500
        assert after_insert_next["chorusingActiveStartMs"] == 1250
        assert longer["chorusingActiveStartMs"] == 1000
        assert full_sentence["chorusingActiveStartMs"] == 0
        assert shorter["chorusingActiveStartMs"] == 500
        assert shorter["selectionStartMs"] == 500
        assert paused["selectionStartMs"] == 500
    finally:
        editor.set_note(None)
        parent.close()


def test_chorusing_auto_advance_uses_split_menu_and_keeps_manual_navigation(
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
        _configure_chorusing_auto_advance(editor, pause_seconds=0.0, repeat_count=2)
        _click_chorusing_practice(editor)

        initial = _state(
            editor,
            lambda state: state["chorusingState"] == "playing"
            and state["chorusingActiveMarkerIndex"] == 3
            and state["selectionStartMs"] == 1500
            and state["selectionEndMs"] == 2000
            and state["repeatEnabled"] is True,
        )

        first_wrap = _force_repeat_wrap(editor, 1500)
        second_wrap = _state(
            editor,
            lambda state: state["chorusingState"] == "playing"
            and state["chorusingActiveMarkerIndex"] == 2
            and state["selectionStartMs"] == 1000
            and state["selectionEndMs"] == 2000
            and state["playbackStartMs"] == 1000,
        )

        longer = _click_chorusing_next(editor, expected_index=1)
        shorter = _click_chorusing_previous(editor, expected_index=2)

        assert initial["chorusingRepeatPassesCompleted"] == 0
        assert first_wrap["chorusingRepeatPassesCompleted"] == 1
        assert second_wrap["chorusingRepeatPassesCompleted"] == 0
        assert longer["chorusingActiveStartMs"] == 500
        assert shorter["chorusingActiveStartMs"] == 1000
    finally:
        editor.set_note(None)
        parent.close()


def _configure_chorusing_auto_advance(editor, *, pause_seconds: float, repeat_count: int) -> None:
    wait_for_js_condition(
        editor.web,
        f"""
        (() => {{
          const menu = document.querySelector('[data-testid="aqe-split-0-chorusing-practice-menu"]');
          const pause = document.querySelector('[data-testid="aqe-split-0-chorusing-pause-seconds"]');
          const autoAdvance = document.querySelector('[data-testid="aqe-split-0-chorusing-auto-advance"]');
          const repeatCount = document.querySelector('[data-testid="aqe-split-0-chorusing-repeat-count"]');
          if (!menu) return null;
          menu.click();
          if (!pause || !autoAdvance || !repeatCount) return null;
          pause.value = "{pause_seconds}";
          pause.dispatchEvent(new Event("input", {{ bubbles: true }}));
          if (!autoAdvance.checked) autoAdvance.click();
          repeatCount.value = "{repeat_count}";
          repeatCount.dispatchEvent(new Event("input", {{ bubbles: true }}));
          return window.__aqeGraphStateForTest?.(0) || null;
        }})()
        """,
        lambda state: state is not None,
        timeout=5.0,
    )


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
