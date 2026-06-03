"""E2E tests for graph back-chaining practice."""

from __future__ import annotations

from e2e.editor_region_loop_helpers import (
    _force_repeat_wrap,
    _open_tone_editor,
    _shift_drag_region,
    _state,
)
from e2e.helpers import run_js, wait_for_js_condition


def test_back_chaining_practice_loops_suffixes_and_pauses_for_normal_play(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, _note, editor, parent, _track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_back_chaining_practice.wav",
        2.0,
    )
    try:
        _shift_drag_region(editor, 0.2, 0.8)
        markers = _state(
            editor,
            lambda state: state["selectionStartMs"] == 400
            and state["selectionEndMs"] == 1600
            and state["backChainingBaseStartMs"] == 0
            and state["backChainingBaseEndMs"] == 2000
            and state["backChainingMarkersMs"] == [0, 667, 1333],
        )

        _click_back_chaining_practice(editor)
        playing = _state(
            editor,
            lambda state: state["backChainingState"] == "playing"
            and state["selectionStartMs"] == 1333
            and state["selectionEndMs"] == 2000
            and state["playbackStartMs"] == 1333
            and state["playbackEndMs"] == 2000
            and state["repeatEnabled"] is True,
        )
        status_text = wait_for_js_condition(
            editor.web,
            "document.querySelector('[data-testid=\"aqe-controls-0\"] .aqe-status')?.textContent || ''",
            lambda value: "Practice mode. Use the toolbar buttons for back-chaining." in value,
            timeout=5.0,
        )
        wrapped = _force_repeat_wrap(editor, 1333)

        inserted = _click_back_chaining_marker(editor, 0.5, expected_count=4)
        after_insert_next = _click_back_chaining_next(editor, expected_index=2)

        longer = _click_back_chaining_next(editor, expected_index=1)

        _click_back_chaining_next(editor, expected_index=0)
        full_sentence = _state(
            editor,
            lambda state: state["backChainingActiveMarkerIndex"] == 0
            and state["selectionStartMs"] == 0
            and state["selectionEndMs"] == 2000,
        )
        shorter = _click_back_chaining_previous(editor, expected_index=1)

        run_js(editor.web, "document.querySelector('[data-testid=\"aqe-button-0-play\"]')?.click()")
        paused = _state(
            editor,
            lambda state: state["backChainingState"] == "paused"
            and state["repeatEnabled"] is False,
        )

        assert markers["backChainingState"] == "stopped"
        assert "Playing from 1.33s" in status_text
        assert playing["backChainingBaseStartMs"] == 0
        assert playing["backChainingMarkersMs"] == [0, 667, 1333]
        assert playing["backChainingActiveStartMs"] == 1333
        assert wrapped["backChainingActiveMarkerIndex"] == 2
        assert inserted["backChainingMarkersMs"] == [0, 667, 1000, 1333]
        assert inserted["backChainingActiveStartMs"] == 1333
        assert after_insert_next["backChainingActiveStartMs"] == 1000
        assert longer["backChainingActiveStartMs"] == 667
        assert full_sentence["backChainingActiveStartMs"] == 0
        assert shorter["backChainingActiveStartMs"] == 667
        assert shorter["selectionStartMs"] == 667
        assert paused["selectionStartMs"] == 667
    finally:
        editor.set_note(None)
        parent.close()


def test_back_chaining_marker_row_is_immediately_editable_after_graph_shows(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, _note, editor, parent, _track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_back_chaining_immediate_markers.wav",
        2.0,
    )
    try:
        initial = _state(
            editor,
            lambda state: state["backChainingBaseStartMs"] == 0
            and state["backChainingBaseEndMs"] == 2000
            and state["backChainingMarkersMs"] == [0, 667, 1333]
            and state["backChainingState"] == "stopped",
        )
        rail = wait_for_js_condition(
            editor.web,
            """
            (() => {
              const row = document.querySelector('[data-testid="aqe-back-chaining-marker-row-0"]');
              if (!row) return null;
              return {
                hidden: row.getAttribute("aria-hidden"),
                markerCount: row.querySelectorAll(".aqe-back-chaining-marker").length,
                trackVisible: !!row.querySelector(".aqe-back-chaining-marker-track"),
              };
            })()
            """,
            lambda value: value is not None
            and value["hidden"] == "false"
            and value["markerCount"] == 3
            and value["trackVisible"] is True,
            timeout=5.0,
        )

        inserted = _click_back_chaining_marker(editor, 0.5, expected_count=4)
        _click_back_chaining_practice(editor)
        playing = _state(
            editor,
            lambda state: state["backChainingState"] == "playing"
            and state["backChainingActiveStartMs"] == 1333
            and state["backChainingMarkersMs"] == [0, 667, 1000, 1333],
        )

        assert initial["backChainingCanPractice"] is True
        assert rail["hidden"] == "false"
        assert inserted["backChainingActiveStartMs"] == 1333
        assert playing["selectionStartMs"] == 1333
    finally:
        editor.set_note(None)
        parent.close()


def test_back_chaining_marker_placement_uses_zoomed_viewport(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, _note, editor, parent, _track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_back_chaining_zoomed_marker.wav",
        2.0,
    )
    try:
        run_js(editor.web, "window.__aqeSetTimeViewportForTest?.(0, 400, 1600)")
        _click_back_chaining_marker(editor, 0.5, expected_count=4)

        state = _state(
            editor,
            lambda value: value["viewportStartMs"] == 400
            and value["viewportEndMs"] == 1600
            and value["backChainingBaseStartMs"] == 0
            and value["backChainingBaseEndMs"] == 2000
            and value["backChainingMarkersMs"] == [0, 667, 1000, 1333],
        )

        assert state["backChainingMarkerVisibleXs"]
    finally:
        editor.set_note(None)
        parent.close()


def test_back_chaining_marker_rail_does_not_steal_top_of_graph_cursor_drag(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, _note, editor, parent, _track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_back_chaining_top_drag.wav",
        2.0,
    )
    try:
        drag_state = wait_for_js_condition(
            editor.web,
            """
            (() => {
              const svg = document.querySelector('[data-testid="aqe-graph-svg-0"]');
              if (!svg) return null;
              const rect = svg.getBoundingClientRect();
              const plot = { width: 620, height: 150, left: 44, right: 10, top: 28 };
              const plotLeft = rect.left + (plot.left / plot.width) * rect.width;
              const plotWidth = ((plot.width - plot.left - plot.right) / plot.width) * rect.width;
              const xFor = (ratio) => plotLeft + plotWidth * ratio;
              const y = rect.top + ((plot.top + 4) / plot.height) * rect.height;
              const target = document.elementFromPoint(xFor(0.25), y);
              if (!target) return null;
              const EventCtor = window.PointerEvent || window.MouseEvent;
              target.dispatchEvent(new EventCtor("pointerdown", {
                bubbles: true,
                clientX: xFor(0.25),
                clientY: y,
              }));
              window.dispatchEvent(new EventCtor("pointermove", {
                bubbles: true,
                clientX: xFor(0.6),
                clientY: y,
              }));
              window.dispatchEvent(new EventCtor("pointerup", {
                bubbles: true,
                clientX: xFor(0.6),
                clientY: y,
              }));
              const state = window.__aqeGraphStateForTest?.(0);
              return state ? {
                cursorMs: state.cursorMs,
                markersMs: state.backChainingMarkersMs,
                targetClass: target.getAttribute("class") || "",
              } : null;
            })()
            """,
            lambda value: value is not None
            and abs(value["cursorMs"] - 1200) <= 75
            and value["markersMs"] == [0, 667, 1333],
            timeout=5.0,
        )

        assert "aqe-back-chaining-marker" not in drag_state["targetClass"]
    finally:
        editor.set_note(None)
        parent.close()


def _click_back_chaining_marker(editor, ratio: float, *, expected_count: int):
    return wait_for_js_condition(
        editor.web,
        f"""
        (() => {{
          const row = document.querySelector('[data-testid="aqe-back-chaining-marker-row-0"]');
          const hitbox = document.querySelector('.aqe-back-chaining-marker-hitbox');
          const svg = document.querySelector('[data-testid="aqe-graph-svg-0"]');
          if (!row || !hitbox || !svg) return null;
          const rect = svg.getBoundingClientRect();
          const plot = {{ width: 620, left: 44, right: 10 }};
          const plotLeft = rect.left + (plot.left / plot.width) * rect.width;
          const plotWidth = ((plot.width - plot.left - plot.right) / plot.width) * rect.width;
          const EventCtor = window.PointerEvent || window.MouseEvent;
          const target = row.getAttribute("aria-hidden") === "true" ? hitbox : row;
          target.dispatchEvent(new EventCtor('pointerdown', {{
            bubbles: true,
            clientX: plotLeft + plotWidth * {ratio},
            clientY: rect.top + 14,
          }}));
          window.dispatchEvent(new EventCtor('pointerup', {{
            bubbles: true,
            clientX: plotLeft + plotWidth * {ratio},
            clientY: rect.top + 14,
          }}));
          return window.__aqeGraphStateForTest?.(0) || null;
        }})()
        """,
        lambda state: state is not None and len(state["backChainingMarkersMs"]) == expected_count,
        timeout=5.0,
    )


def _click_back_chaining_practice(editor) -> None:
    wait_for_js_condition(
        editor.web,
        """
        (() => {
          const button = document.querySelector('[data-testid="aqe-button-0-back-chain-practice"]');
          if (!button || button.disabled) return null;
          button.click();
          return window.__aqeGraphStateForTest?.(0) || null;
        })()
        """,
        lambda state: state is not None and state["backChainingState"] == "playing",
        timeout=5.0,
    )


def _click_back_chaining_next(editor, *, expected_index: int = 1):
    return wait_for_js_condition(
        editor.web,
        """
        (() => {
          const button = document.querySelector('[data-testid="aqe-button-0-back-chain-next"]');
          if (!button || button.disabled) return null;
          button.click();
          return window.__aqeGraphStateForTest?.(0) || null;
        })()
        """,
        lambda state: state is not None and state["backChainingActiveMarkerIndex"] == expected_index,
        timeout=5.0,
    )


def _click_back_chaining_previous(editor, *, expected_index: int = 1):
    return wait_for_js_condition(
        editor.web,
        """
        (() => {
          const button = document.querySelector('[data-testid="aqe-button-0-back-chain-previous"]');
          if (!button || button.disabled) return null;
          button.click();
          return window.__aqeGraphStateForTest?.(0) || null;
        })()
        """,
        lambda state: state is not None and state["backChainingActiveMarkerIndex"] == expected_index,
        timeout=5.0,
    )
