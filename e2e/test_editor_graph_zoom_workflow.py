"""E2E tests for inline editor graph horizontal zoom."""

from __future__ import annotations

from pathlib import Path

from e2e.editor_graph_helpers import _click_graph_and_wait, _graph_zoom_state_js
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
)
from e2e.helpers import generate_tone, wait_for_js_condition, wait_for_selector


def test_editor_graph_horizontal_zoom_controls_preserve_time_selection(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_graph_zoom_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=4.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:analyze"), timeout=10.0)
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)

        zoomed = wait_for_js_condition(
            editor.web,
            """
            (() => {
              const state = window.__aqeGraphStateForTest?.(0);
              if (!state) return null;
              window.__aqeSetCursorForTest?.(0, state.durationMs / 2, false);
              document.querySelector('[data-testid="aqe-zoom-in-0"]')?.click();
              return window.__aqeGraphStateForTest?.(0) || null;
            })()
            """,
            lambda value: value is not None
            and value["viewportStartMs"] > 0
            and value["viewportEndMs"] < value["durationMs"],
            timeout=5.0,
        )
        assert zoomed["viewportEndMs"] - zoomed["viewportStartMs"] < zoomed["durationMs"]

        scrolled = wait_for_js_condition(
            editor.web,
            """
            (() => {
              const scrollbar = document.querySelector('[data-testid="aqe-time-scrollbar-0"]');
              const scroller = document.querySelector('[data-testid="aqe-time-scrollbar-scroll-0"]');
              if (!scrollbar || !scroller || scrollbar.hidden) return null;
              scroller.scrollLeft = scroller.scrollWidth - scroller.clientWidth;
              scroller.dispatchEvent(new Event('scroll'));
              return window.__aqeGraphStateForTest?.(0) || null;
            })()
            """,
            lambda value: value is not None
            and value["viewportStartMs"] > zoomed["viewportStartMs"]
            and value["viewportEndMs"] == value["durationMs"],
            timeout=5.0,
        )
        assert scrolled["viewportStartMs"] > zoomed["viewportStartMs"]

        wait_for_js_condition(
            editor.web,
            """
            (() => {
              document.querySelector('[data-testid="aqe-zoom-fit-0"]')?.click();
              return window.__aqeGraphStateForTest?.(0) || null;
            })()
            """,
            lambda value: value is not None
            and value["viewportStartMs"] == 0
            and value["viewportEndMs"] == value["durationMs"],
            timeout=5.0,
        )

        selected_zoom = wait_for_js_condition(
            editor.web,
            """
            (() => {
              const svg = document.querySelector('[data-testid="aqe-graph-svg-0"]');
              if (!svg) return null;
              const rect = svg.getBoundingClientRect();
              const plotLeft = rect.left + (44 / 620) * rect.width;
              const plotWidth = ((620 - 44 - 10) / 620) * rect.width;
              const EventCtor = window.PointerEvent || window.MouseEvent;
              svg.dispatchEvent(new EventCtor('pointerdown', {
                bubbles: true,
                clientX: plotLeft + plotWidth * 0.25,
                clientY: rect.top + 20,
                shiftKey: true,
              }));
              window.dispatchEvent(new EventCtor('pointermove', {
                bubbles: true,
                clientX: plotLeft + plotWidth * 0.75,
                clientY: rect.top + 20,
                shiftKey: true,
              }));
              window.dispatchEvent(new EventCtor('pointerup', {
                bubbles: true,
                clientX: plotLeft + plotWidth * 0.75,
                clientY: rect.top + 20,
                shiftKey: true,
              }));
              document.querySelector('[data-testid="aqe-zoom-selection-0"]')?.click();
              return window.__aqeGraphStateForTest?.(0) || null;
            })()
            """,
            lambda value: value is not None
            and value["selectionActive"] is True
            and value["viewportStartMs"] <= value["selectionStartMs"]
            and value["viewportEndMs"] >= value["selectionEndMs"],
            timeout=5.0,
        )
        assert selected_zoom["selectionEndMs"] > selected_zoom["selectionStartMs"]

        fit = wait_for_js_condition(
            editor.web,
            """
            (() => {
              document.querySelector('[data-testid="aqe-zoom-fit-0"]')?.click();
              return window.__aqeGraphStateForTest?.(0) || null;
            })()
            """,
            lambda value: value is not None
            and value["viewportStartMs"] == 0
            and value["viewportEndMs"] == value["durationMs"],
            timeout=5.0,
        )
        fit_zoom_state = wait_for_js_condition(
            editor.web,
            _graph_zoom_state_js(),
            lambda value: value is not None
            and value["viewportStartMs"] == 0
            and value["viewportEndMs"] == fit["durationMs"],
            timeout=5.0,
        )
        assert fit_zoom_state["viewportStartMs"] == 0
    finally:
        editor.set_note(None)
        parent.close()
