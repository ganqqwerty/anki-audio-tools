"""E2E tests for graph chorusing practice."""

from __future__ import annotations

from e2e.editor_region_loop_helpers import (
    _force_repeat_wrap,
    _open_tone_editor,
    _shift_drag_region,
    _state,
)
from e2e.helpers import run_js, wait_for_js_condition


def _matches_zoomed_marker_state(state) -> bool:
    start = int(state["viewportStartMs"])
    end = int(state["viewportEndMs"])
    duration = int(state["durationMs"])
    starts_after_zero = start > 0
    ends_before_duration = end < duration
    markers = state["chorusingMarkersMs"]
    return (
        starts_after_zero
        and end > start
        and ends_before_duration
        and end - start == 1200
        and state["chorusingBaseStartMs"] == 0
        and state["chorusingBaseEndMs"] == 2000
        and len(markers) == 4
        and markers[0:2] == [0, 667]
        and abs(markers[2] - 880) <= 5
        and markers[3] == 1333
    )


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
            and state["chorusingMarkersMs"] == [0, 667, 1333],
        )

        _click_chorusing_practice(editor)
        playing = _state(
            editor,
            lambda state: state["chorusingState"] == "playing"
            and state["selectionStartMs"] == 1333
            and state["selectionEndMs"] == 2000
            and state["playbackStartMs"] == 1333
            and state["playbackEndMs"] == 2000
            and state["repeatEnabled"] is True,
        )
        status_text = wait_for_js_condition(
            editor.web,
            "document.querySelector('[data-testid=\"aqe-controls-0\"] .aqe-status')?.textContent || ''",
            lambda value: "Practice mode. Use the toolbar buttons for chorusing." in value,
            timeout=5.0,
        )
        wrapped = _force_repeat_wrap(editor, 1333)

        inserted = _click_chorusing_marker(editor, 0.5, expected_count=4)
        after_insert_next = _click_chorusing_next(editor, expected_index=2)

        longer = _click_chorusing_next(editor, expected_index=1)

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
        assert "Playing from 1.33s" in status_text
        assert playing["chorusingBaseStartMs"] == 0
        assert playing["chorusingMarkersMs"] == [0, 667, 1333]
        assert playing["chorusingActiveStartMs"] == 1333
        assert wrapped["chorusingActiveMarkerIndex"] == 2
        assert inserted["chorusingMarkersMs"] == [0, 667, 1000, 1333]
        assert inserted["chorusingActiveStartMs"] == 1333
        assert after_insert_next["chorusingActiveStartMs"] == 1000
        assert longer["chorusingActiveStartMs"] == 667
        assert full_sentence["chorusingActiveStartMs"] == 0
        assert shorter["chorusingActiveStartMs"] == 667
        assert shorter["selectionStartMs"] == 667
        assert paused["selectionStartMs"] == 667
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
            and state["chorusingActiveMarkerIndex"] == 2
            and state["selectionStartMs"] == 1333
            and state["selectionEndMs"] == 2000
            and state["repeatEnabled"] is True,
        )

        first_wrap = _force_repeat_wrap(editor, 1333)
        second_wrap = _state(
            editor,
            lambda state: state["chorusingState"] == "playing"
            and state["chorusingActiveMarkerIndex"] == 1
            and state["selectionStartMs"] == 667
            and state["selectionEndMs"] == 2000
            and state["playbackStartMs"] == 667,
        )

        longer = _click_chorusing_next(editor, expected_index=0)
        shorter = _click_chorusing_previous(editor, expected_index=1)

        assert initial["chorusingRepeatPassesCompleted"] == 0
        assert first_wrap["chorusingRepeatPassesCompleted"] == 1
        assert second_wrap["chorusingRepeatPassesCompleted"] == 0
        assert longer["chorusingActiveStartMs"] == 0
        assert shorter["chorusingActiveStartMs"] == 667
    finally:
        editor.set_note(None)
        parent.close()


def test_chorusing_marker_row_is_immediately_editable_after_graph_shows(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, _note, editor, parent, _track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_chorusing_immediate_markers.wav",
        2.0,
    )
    try:
        initial = _state(
            editor,
            lambda state: state["chorusingBaseStartMs"] == 0
            and state["chorusingBaseEndMs"] == 2000
            and state["chorusingMarkersMs"] == [0, 667, 1333]
            and state["chorusingState"] == "stopped",
        )
        rail = wait_for_js_condition(
            editor.web,
            """
            (() => {
              const row = document.querySelector('[data-testid="aqe-chorusing-marker-row-0"]');
              if (!row) return null;
              return {
                hidden: row.getAttribute("aria-hidden"),
                markerCount: row.querySelectorAll(".aqe-chorusing-marker").length,
                trackVisible: !!row.querySelector(".aqe-chorusing-marker-track"),
              };
            })()
            """,
            lambda value: value is not None
            and value["hidden"] == "false"
            and value["markerCount"] == 3
            and value["trackVisible"] is True,
            timeout=5.0,
        )
        toolbar_panel = wait_for_js_condition(
            editor.web,
            """
            (() => {
              const panel = document.querySelector('[data-testid="aqe-chorusing-toolbar-panel-0"]');
              if (!panel) return null;
              const style = getComputedStyle(panel);
              return {
                ariaLabel: panel.getAttribute("aria-label"),
                borderRadius: style.borderRadius,
                borderTopWidth: style.borderTopWidth,
                commands: Array.from(panel.querySelectorAll("[data-aqe-command]"))
                  .map((button) => button.getAttribute("data-aqe-command")),
                container: panel.getAttribute("data-aqe-toolbar-button-container"),
                display: style.display,
                label: panel.querySelector(".aqe-toolbar-panel-label")?.textContent || "",
                role: panel.getAttribute("role"),
              };
            })()
            """,
            lambda value: value is not None
            and value["ariaLabel"] == "Chorusing"
            and value["borderRadius"] == "9px"
            and value["borderTopWidth"] == "0px"
            and value["commands"] == [
                "aqe:chorusing-practice",
                "aqe:chorusing-next",
                "aqe:chorusing-previous",
            ]
            and value["container"] == "true"
            and value["display"] in {"flex", "inline-flex"}
            and value["label"] == "Chorusing"
            and value["role"] == "group",
            timeout=5.0,
        )

        inserted = _click_chorusing_marker(editor, 0.5, expected_count=4)
        _click_chorusing_practice(editor)
        playing = _state(
            editor,
            lambda state: state["chorusingState"] == "playing"
            and state["chorusingActiveStartMs"] == 1333
            and state["chorusingMarkersMs"] == [0, 667, 1000, 1333],
        )

        assert initial["chorusingCanPractice"] is True
        assert rail["hidden"] == "false"
        assert toolbar_panel["commands"] == [
            "aqe:chorusing-practice",
            "aqe:chorusing-next",
            "aqe:chorusing-previous",
        ]
        assert inserted["chorusingActiveStartMs"] == 1333
        assert playing["selectionStartMs"] == 1333
    finally:
        editor.set_note(None)
        parent.close()


def test_chorusing_marker_placement_uses_zoomed_viewport(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, _note, editor, parent, _track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_chorusing_zoomed_marker.wav",
        2.0,
    )
    try:
        run_js(editor.web, "window.__aqeSetTimeViewportForTest?.(0, 400, 1600)")
        _state(
            editor,
            lambda value: value["viewportStartMs"] == 400
            and value["viewportEndMs"] == 1600,
        )
        _click_chorusing_marker(editor, 0.4, expected_count=4)

        state = _state(
            editor,
            _matches_zoomed_marker_state,
        )

        assert state["chorusingMarkerVisibleXs"]
    finally:
        editor.set_note(None)
        parent.close()


def test_chorusing_marker_rail_does_not_steal_top_of_graph_cursor_drag(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, _note, editor, parent, _track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_chorusing_top_drag.wav",
        2.0,
    )
    try:
        drag_state = wait_for_js_condition(
            editor.web,
            """
            (() => {
              const svg = document.querySelector('[data-testid="aqe-graph-svg-0"]');
              const rect = svg?.getBoundingClientRect();
              const bounds = window.__aqeGraphPixelBoundsForTest?.(0);
              if (!svg || !rect || !bounds) return null;
              const viewBoxHeight = svg.viewBox?.baseVal?.height || 150;
              const scale = Math.min(rect.width / (svg.viewBox?.baseVal?.width || 620), rect.height / viewBoxHeight) || 1;
              const xFor = (ratio) => bounds.left + bounds.width * ratio;
              const y = rect.top + (28 + 4) * scale;
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
                markersMs: state.chorusingMarkersMs,
                targetClass: target.getAttribute("class") || "",
              } : null;
            })()
            """,
            lambda value: value is not None
            and abs(value["cursorMs"] - 1200) <= 75
            and value["markersMs"] == [0, 667, 1333],
            timeout=5.0,
        )

        assert "aqe-chorusing-marker" not in drag_state["targetClass"]
    finally:
        editor.set_note(None)
        parent.close()


def _click_chorusing_marker(editor, ratio: float, *, expected_count: int):
    return wait_for_js_condition(
        editor.web,
        f"""
        (() => {{
          const row = document.querySelector('[data-testid="aqe-chorusing-marker-row-0"]');
          const hitbox = document.querySelector('.aqe-chorusing-marker-hitbox');
          const svg = document.querySelector('[data-testid="aqe-graph-svg-0"]');
          const rect = svg?.getBoundingClientRect();
          const bounds = window.__aqeGraphPixelBoundsForTest?.(0);
          if (!row || !hitbox || !svg || !rect || !bounds) return null;
          const EventCtor = window.PointerEvent || window.MouseEvent;
          const target = row.getAttribute("aria-hidden") === "true" ? hitbox : row;
          target.dispatchEvent(new EventCtor('pointerdown', {{
            bubbles: true,
            clientX: bounds.left + bounds.width * {ratio},
            clientY: rect.top + 14,
          }}));
          window.dispatchEvent(new EventCtor('pointerup', {{
            bubbles: true,
            clientX: bounds.left + bounds.width * {ratio},
            clientY: rect.top + 14,
          }}));
          return window.__aqeGraphStateForTest?.(0) || null;
        }})()
        """,
        lambda state: state is not None and len(state["chorusingMarkersMs"]) == expected_count,
        timeout=5.0,
    )


def _click_chorusing_practice(editor) -> None:
    wait_for_js_condition(
        editor.web,
        """
        (() => {
          const button = document.querySelector('[data-testid="aqe-button-0-chorusing-practice"]');
          if (!button || button.disabled) return null;
          button.click();
          return window.__aqeGraphStateForTest?.(0) || null;
        })()
        """,
        lambda state: state is not None and state["chorusingState"] == "playing",
        timeout=5.0,
    )


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
