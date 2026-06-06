"""E2E tests for selection marker shift edge buttons."""

from __future__ import annotations

from e2e.editor_region_loop_helpers import (
    _open_tone_editor,
    _shift_drag_region,
    _state,
)
from e2e.helpers import click_selector, run_js, wait_for_js_condition


def test_selection_marker_shift_buttons_track_marker_changes_and_hide_inner_pair(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, _note, editor, parent, _track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_selection_marker_shift_markers.wav",
        2.0,
        selection_marker_shift_buttons_enabled=True,
    )
    try:
        _shift_drag_region(editor, 0.0, 1 / 3)
        _state(
            editor,
            lambda state: state["selectionStartMs"] == 0
            and abs(state["selectionEndMs"] - 667) <= 8,
        )

        disabled = _button_state(editor, "end", "previous")
        assert disabled["hidden"] is False
        assert disabled["disabled"] is True
        assert "That marker would cross the other selection edge." in disabled["tooltip"]

        _click_chorusing_marker(editor, 1 / 6, expected_count=4)
        enabled = wait_for_js_condition(
            editor.web,
            _button_state_js("end", "previous"),
            lambda value: value is not None and value["disabled"] is False,
            timeout=5.0,
        )
        assert enabled["tooltip"] == "Move selection end to previous marker"

        _click_chorusing_marker(editor, 1 / 6, expected_count=3)
        disabled_again = wait_for_js_condition(
            editor.web,
            _button_state_js("end", "previous"),
            lambda value: value is not None and value["disabled"] is True,
            timeout=5.0,
        )
        assert "That marker would cross the other selection edge." in disabled_again["tooltip"]

        _click_chorusing_marker(editor, 0.475, expected_count=4)
        _click_chorusing_marker(editor, 0.5, expected_count=5)
        _shift_drag_region(editor, 0.475, 0.5)
        _state(
            editor,
            lambda state: abs(state["selectionStartMs"] - 950) <= 8
            and abs(state["selectionEndMs"] - 1000) <= 8,
        )
        start_previous = _button_state(editor, "start", "previous")
        start_next = _button_state(editor, "start", "next")
        end_previous = _button_state(editor, "end", "previous")
        end_next = _button_state(editor, "end", "next")
        assert start_previous["hidden"] is False
        assert start_next["hidden"] is True
        assert end_previous["hidden"] is True
        assert end_next["hidden"] is False
    finally:
        editor.set_note(None)
        parent.close()


def test_selection_marker_shift_click_moves_edge_and_keeps_html_playback_running(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, _note, editor, parent, _track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_selection_marker_shift_playback.wav",
        2.0,
        selection_marker_shift_buttons_enabled=True,
    )
    try:
        _shift_drag_region(editor, 0.0, 1 / 3)
        _state(
            editor,
            lambda state: state["selectionStartMs"] == 0 and abs(state["selectionEndMs"] - 667) <= 8,
        )

        click_selector(editor.web, '[data-testid="aqe-button-0-play"]', timeout=5.0)
        _state(
            editor,
            lambda state: state["playbackState"] == "playing"
            and state["selectionStartMs"] == 0
            and abs(state["selectionEndMs"] - 667) <= 8
            and state["playbackStartMs"] == 0
            and abs(state["playbackEndMs"] - 667) <= 8,
        )

        click_selector(editor.web, '[data-testid="aqe-selection-shift-end-next-0"]', timeout=5.0)
        click_selector(editor.web, '[data-testid="aqe-selection-shift-end-next-0"]', timeout=5.0)
        shifted = _state(
            editor,
            lambda state: state["playbackState"] == "playing"
            and state["selectionStartMs"] == 0
            and abs(state["selectionEndMs"] - 1333) <= 8
            and state["playbackStartMs"] == 0
            and abs(state["playbackEndMs"] - 1333) <= 8,
        )
        assert shifted["cursorMs"] == 0
    finally:
        editor.set_note(None)
        parent.close()


def _click_chorusing_marker(editor, ratio: float, *, expected_count: int):
    run_js(
        editor.web,
        f"""
        (() => {{
          const row = document.querySelector('[data-testid="aqe-chorusing-marker-row-0"]');
          const hitbox = document.querySelector('.aqe-chorusing-marker-hitbox');
          const target = row?.getAttribute('aria-hidden') === 'true' ? hitbox : row;
          const svg = document.querySelector('[data-testid="aqe-graph-svg-0"]');
          if (!target || !svg) return false;
          const rect = svg.getBoundingClientRect();
          const plot = {{ width: 620, left: 44, right: 10 }};
          const plotLeft = rect.left + (plot.left / plot.width) * rect.width;
          const plotWidth = ((plot.width - plot.left - plot.right) / plot.width) * rect.width;
          const x = plotLeft + plotWidth * {ratio};
          const EventCtor = window.PointerEvent || window.MouseEvent;
          target.dispatchEvent(new EventCtor('pointerdown', {{ bubbles: true, clientX: x, clientY: rect.top + 8 }}));
          window.dispatchEvent(new EventCtor('pointerup', {{ bubbles: true, clientX: x, clientY: rect.top + 8 }}));
          return true;
        }})()
        """,
    )
    return _state(
        editor,
        lambda state: len(state["chorusingMarkersMs"]) == expected_count,
    )


def _button_state(editor, edge: str, direction: str):
    return wait_for_js_condition(
        editor.web,
        _button_state_js(edge, direction),
        lambda value: value is not None,
        timeout=5.0,
    )


def _button_state_js(edge: str, direction: str) -> str:
    return f"""
    (() => {{
      const button = document.querySelector('[data-testid="aqe-selection-shift-{edge}-{direction}-0"]');
      if (!button) return null;
      const tooltip = button.getAttribute('data-aqe-tooltip-content')
        || button.closest('.aqe-tooltip-target')?.getAttribute('data-aqe-tooltip-content')
        || '';
      return {{
        disabled: button.disabled,
        hidden: button.hidden,
        tooltip,
      }};
    }})()
    """
