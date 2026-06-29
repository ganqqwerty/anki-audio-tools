"""E2E tests for graph chorusing marker placement and editing."""

from __future__ import annotations

from e2e.editor_chorusing_helpers import (
    _click_chorusing_marker,
)
from e2e.editor_region_loop_helpers import (
    _open_tone_editor,
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
        and len(markers) == 5
        and markers[0:2] == [0, 500]
        and abs(markers[2] - 880) <= 5
        and markers[3:5] == [1000, 1500]
    )


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
            and state["chorusingMarkersMs"] == [0, 500, 1000, 1500]
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
            and value["markerCount"] == 4
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
            and value["ariaLabel"] == "Markers"
            and value["borderRadius"] == "9px"
            and value["borderTopWidth"] == "0px"
            and value["commands"] == [
                "aqe:chorusing-next",
                "aqe:chorusing-previous",
            ]
            and value["container"] == "true"
            and value["display"] in {"flex", "inline-flex"}
            and value["label"] == "Markers"
            and value["role"] == "group",
            timeout=5.0,
        )

        inserted = _click_chorusing_marker(editor, 0.625, expected_count=5)
        selected = wait_for_js_condition(
            editor.web,
            """
            (() => {
              const button = document.querySelector('[data-testid="aqe-button-0-chorusing-next"]');
              if (!button || button.disabled) return null;
              button.click();
              return window.__aqeGraphStateForTest?.(0) || null;
            })()
            """,
            lambda state: state is not None
            and state["chorusingActiveMarkerIndex"] == 4
            and state["chorusingActiveStartMs"] == 1500,
            timeout=5.0,
        )
        _state(
            editor,
            lambda state: state["chorusingState"] == "stopped"
            and state["chorusingActiveStartMs"] == 1500
            and state["chorusingMarkersMs"] == [0, 500, 1000, 1250, 1500],
        )

        assert initial["chorusingCanPractice"] is True
        assert rail["hidden"] == "false"
        assert toolbar_panel["commands"] == [
            "aqe:chorusing-next",
            "aqe:chorusing-previous",
        ]
        assert inserted["chorusingActiveStartMs"] is None
        assert selected["selectionStartMs"] == 1500
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
        _click_chorusing_marker(editor, 0.4, expected_count=5)

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
            and value["markersMs"] == [0, 500, 1000, 1500],
            timeout=5.0,
        )

        assert "aqe-chorusing-marker" not in drag_state["targetClass"]
    finally:
        editor.set_note(None)
        parent.close()
