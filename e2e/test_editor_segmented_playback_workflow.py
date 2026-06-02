"""E2E tests for segmented graph playback practice."""

from __future__ import annotations

from e2e.editor_region_loop_helpers import (
    _force_repeat_wrap,
    _open_tone_editor,
    _shift_drag_region,
    _state,
)
from e2e.helpers import run_js, wait_for_js_condition


def test_segmented_playback_practice_loops_suffixes_and_pauses_for_normal_play(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, _note, editor, parent, _track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_segmented_practice.wav",
        2.0,
    )
    try:
        _shift_drag_region(editor, 0.2, 0.8)
        _enable_segment_editing(editor)
        _click_segment_marker(editor, 0.4, expected_count=1)
        _click_segment_marker(editor, 0.7, expected_count=2)
        markers = _state(
            editor,
            lambda state: state["segmentMarkersMs"] == [800, 1400]
            and state["segmentCanPractice"] is True,
        )

        _click_segment_practice(editor)
        playing = _state(
            editor,
            lambda state: state["segmentPracticeState"] == "playing"
            and state["selectionStartMs"] == 1400
            and state["selectionEndMs"] == 1600
            and state["playbackStartMs"] == 1400
            and state["playbackEndMs"] == 1600
            and state["repeatEnabled"] is True,
        )
        wrapped = _force_repeat_wrap(editor, 1400)

        _click_segment_next(editor)
        longer = _state(
            editor,
            lambda state: state["segmentActiveMarkerIndex"] == 0
            and state["selectionStartMs"] == 800
            and state["selectionEndMs"] == 1600,
        )

        run_js(editor.web, "document.querySelector('[data-testid=\"aqe-button-0-play\"]')?.click()")
        paused = _state(
            editor,
            lambda state: state["segmentPracticeState"] == "paused"
            and state["repeatEnabled"] is False,
        )

        assert markers["segmentBaseStartMs"] == 400
        assert playing["segmentActiveStartMs"] == 1400
        assert wrapped["segmentActiveMarkerIndex"] == 1
        assert longer["segmentActiveStartMs"] == 800
        assert paused["selectionStartMs"] == 800
    finally:
        editor.set_note(None)
        parent.close()


def test_segmented_playback_marker_placement_uses_zoomed_viewport(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, _note, editor, parent, _track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_segmented_zoomed_marker.wav",
        2.0,
    )
    try:
        _shift_drag_region(editor, 0.2, 0.8)
        _enable_segment_editing(editor)
        run_js(editor.web, "window.__aqeSetTimeViewportForTest?.(0, 400, 1600)")
        _click_segment_marker(editor, 0.5, expected_count=1)

        state = _state(
            editor,
            lambda value: value["viewportStartMs"] == 400
            and value["viewportEndMs"] == 1600
            and value["segmentMarkersMs"] == [1000],
        )

        assert state["segmentMarkerVisibleXs"]
    finally:
        editor.set_note(None)
        parent.close()


def _enable_segment_editing(editor) -> None:
    wait_for_js_condition(
        editor.web,
        """
        (() => {
          const splitMenu = document.querySelector('[data-testid="aqe-split-0-play-menu"]');
          if (splitMenu && splitMenu.getAttribute("aria-expanded") !== "true") splitMenu.click();
          const popover = document.querySelector('[data-testid="aqe-split-0-play-popover"]');
          if (popover?.querySelector('[data-testid="aqe-segment-0-edit"]')) return null;
          const entry = document.querySelector('[data-testid="aqe-selection-toolbar-practice-segments-0"]');
          if (!entry) return null;
          if (window.__aqeGraphStateForTest?.(0)?.segmentEditing !== true) entry.click();
          return window.__aqeGraphStateForTest?.(0) || null;
        })()
        """,
        lambda state: state is not None
        and state["segmentEditing"] is True
        and state["segmentPanelOpen"] is True
        and state["segmentBaseStartMs"] == 400,
        timeout=5.0,
    )


def _click_segment_marker(editor, ratio: float, *, expected_count: int) -> None:
    wait_for_js_condition(
        editor.web,
        f"""
        (() => {{
          const row = document.querySelector('[data-testid="aqe-segment-marker-row-0"]');
          const svg = document.querySelector('[data-testid="aqe-graph-svg-0"]');
          if (!row || !svg || row.hidden) return null;
          const rect = svg.getBoundingClientRect();
          const plot = {{ width: 620, left: 44, right: 10 }};
          const plotLeft = rect.left + (plot.left / plot.width) * rect.width;
          const plotWidth = ((plot.width - plot.left - plot.right) / plot.width) * rect.width;
          const EventCtor = window.PointerEvent || window.MouseEvent;
          row.dispatchEvent(new EventCtor('pointerdown', {{
            bubbles: true,
            clientX: plotLeft + plotWidth * {ratio},
            clientY: rect.bottom + 4,
          }}));
          return window.__aqeGraphStateForTest?.(0) || null;
        }})()
        """,
        lambda state: state is not None and len(state["segmentMarkersMs"]) == expected_count,
        timeout=5.0,
    )


def _click_segment_practice(editor) -> None:
    wait_for_js_condition(
        editor.web,
        """
        (() => {
          const panel = document.querySelector('[data-testid="aqe-segment-0-panel"]');
          if (!panel) return null;
          const button = document.querySelector('[data-testid="aqe-segment-0-practice"]');
          if (!button || button.disabled) return null;
          button.click();
          return window.__aqeGraphStateForTest?.(0) || null;
        })()
        """,
        lambda state: state is not None and state["segmentPracticeState"] == "playing",
        timeout=5.0,
    )


def _click_segment_next(editor) -> None:
    wait_for_js_condition(
        editor.web,
        """
        (() => {
          const panel = document.querySelector('[data-testid="aqe-segment-0-panel"]');
          if (!panel) return null;
          const button = document.querySelector('[data-testid="aqe-segment-0-next"]');
          if (!button || button.disabled) return null;
          button.click();
          return window.__aqeGraphStateForTest?.(0) || null;
        })()
        """,
        lambda state: state is not None and state["segmentActiveMarkerIndex"] == 0,
        timeout=5.0,
    )
