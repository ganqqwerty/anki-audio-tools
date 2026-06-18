"""E2E tests for inline editor graph horizontal zoom - advanced operations."""

from __future__ import annotations

from e2e.editor_graph_helpers import (
    _install_html_audio_test_driver,
    _wait_for_html_playback,
)
from e2e.editor_graph_zoom_helpers import _open_zoom_graph_editor
from e2e.editor_note_helpers import _button_selector
from e2e.editor_playback_helpers import _record_fake_playback
from e2e.editor_region_loop_helpers import (
    _drag_resize_handle,
    _force_audio_boundary,
    _shift_drag_region,
    _state,
)
from e2e.helpers import (
    click_selector,
    run_js,
    wait_for_js_condition,
)


def test_editor_graph_zoom_to_selection_fits_active_region(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, editor, parent, _track = _open_zoom_graph_editor(
        anki_mw,
        ffmpeg_config,
        "editor_graph_zoom_selection.wav",
    )
    try:
        selected_zoom = wait_for_js_condition(
            editor.web,
            """
            (() => {
              const svg = document.querySelector('[data-testid="aqe-graph-svg-0"]');
              const rect = svg?.getBoundingClientRect();
              const bounds = window.__aqeGraphPixelBoundsForTest?.(0);
              if (!svg || !rect || !bounds) return null;
              const EventCtor = window.PointerEvent || window.MouseEvent;
              svg.dispatchEvent(new EventCtor('pointerdown', {
                bubbles: true,
                clientX: bounds.left + bounds.width * 0.25,
                clientY: rect.top + 40,
                shiftKey: true,
              }));
              window.dispatchEvent(new EventCtor('pointermove', {
                bubbles: true,
                clientX: bounds.left + bounds.width * 0.75,
                clientY: rect.top + 40,
                shiftKey: true,
              }));
              window.dispatchEvent(new EventCtor('pointerup', {
                bubbles: true,
                clientX: bounds.left + bounds.width * 0.75,
                clientY: rect.top + 40,
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
    finally:
        editor.set_note(None)
        parent.close()


def test_editor_graph_zoom_scroll_hides_and_restores_stopped_cursor(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, editor, parent, _track = _open_zoom_graph_editor(
        anki_mw,
        ffmpeg_config,
        "editor_graph_zoom_cursor_scroll.wav",
    )
    try:
        visible = wait_for_js_condition(
            editor.web,
            """
            (() => {
              const state = window.__aqeGraphStateForTest?.(0);
              if (!state) return null;
              window.__aqeSetTimeViewportForTest?.(0, 0, state.durationMs / 2);
              window.__aqeSetCursorForTest?.(0, state.durationMs / 4, false);
              const next = window.__aqeGraphStateForTest?.(0);
              const svg = document.querySelector('[data-testid="aqe-graph-svg-0"]');
              const width = svg?.viewBox?.baseVal?.width || 0;
              return next && width ? { ...next, expectedCenterX: width / 2 } : null;
            })()
            """,
            lambda value: value is not None
            and value["cursorMs"] == 1000
            and value["timecodeFlagVisible"] is True
            and value["viewportStartMs"] == 0
            and value["viewportEndMs"] == 2000,
            timeout=5.0,
        )
        assert abs(visible["cursorX"] - visible["expectedCenterX"]) <= 2

        hidden = wait_for_js_condition(
            editor.web,
            """
            (() => {
              const scroller = document.querySelector('[data-testid="aqe-time-scrollbar-scroll-0"]');
              if (!scroller) return null;
              scroller.scrollLeft = scroller.scrollWidth - scroller.clientWidth;
              scroller.dispatchEvent(new Event('scroll'));
              return window.__aqeGraphStateForTest?.(0) || null;
            })()
            """,
            lambda value: value is not None
            and value["cursorMs"] == 1000
            and value["timecodeFlagVisible"] is False
            and value["viewportStartMs"] > 0,
            timeout=5.0,
        )
        assert hidden["viewportEndMs"] == hidden["durationMs"]

        restored = wait_for_js_condition(
            editor.web,
            """
            (() => {
              const scroller = document.querySelector('[data-testid="aqe-time-scrollbar-scroll-0"]');
              if (!scroller) return null;
              scroller.scrollLeft = 0;
              scroller.dispatchEvent(new Event('scroll'));
              const state = window.__aqeGraphStateForTest?.(0);
              const svg = document.querySelector('[data-testid="aqe-graph-svg-0"]');
              const width = svg?.viewBox?.baseVal?.width || 0;
              return state && width ? { ...state, expectedCenterX: width / 2 } : null;
            })()
            """,
            lambda value: value is not None
            and value["cursorMs"] == 1000
            and value["timecodeFlagVisible"] is True
            and value["viewportStartMs"] == 0,
            timeout=5.0,
        )
        assert abs(restored["cursorX"] - restored["expectedCenterX"]) <= 2
    finally:
        editor.set_note(None)
        parent.close()


def test_editor_graph_zoom_selection_handles_follow_true_visible_edges(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, editor, parent, _track = _open_zoom_graph_editor(
        anki_mw,
        ffmpeg_config,
        "editor_graph_zoom_selection_edges.wav",
    )
    try:
        run_js(editor.web, "window.__aqeSetTimeViewportForTest?.(0, 0, 4000)")
        _shift_drag_region(editor, 0.25, 0.75)
        selected = _state(
            editor,
            lambda state: state["selectionStartMs"] == 1000
            and state["selectionEndMs"] == 3000,
        )
        assert selected["cursorMs"] == 1000

        left_view = wait_for_js_condition(
            editor.web,
            """
            (() => {
              window.__aqeSetTimeViewportForTest?.(0, 0, 2000);
              return window.__aqeGraphStateForTest?.(0) || null;
            })()
            """,
            lambda state: state is not None
            and state["selectionStartHandleVisible"] is True
            and state["selectionEndHandleVisible"] is False,
            timeout=5.0,
        )
        assert left_view["viewportEndMs"] == 2000

        _drag_resize_handle(editor, "start", 0.5, 0.25)
        resized_start = _state(
            editor,
            lambda state: state["selectionStartMs"] == 500
            and state["selectionEndMs"] == 3000
            and state["cursorMs"] == 500,
        )
        assert resized_start["selectionStartHandleVisible"] is True

        right_view = wait_for_js_condition(
            editor.web,
            """
            (() => {
              window.__aqeSetTimeViewportForTest?.(0, 2000, 4000);
              return window.__aqeGraphStateForTest?.(0) || null;
            })()
            """,
            lambda state: state is not None
            and state["selectionStartHandleVisible"] is False
            and state["selectionEndHandleVisible"] is True,
            timeout=5.0,
        )
        assert right_view["timecodeFlagVisible"] is False

        _drag_resize_handle(editor, "end", 0.5, 0.75)
        resized_end = _state(
            editor,
            lambda state: state["selectionStartMs"] == 500
            and state["selectionEndMs"] == 3500
            and state["cursorMs"] == 500,
        )
        assert resized_end["selectionEndHandleVisible"] is True
    finally:
        editor.set_note(None)
        parent.close()


def test_editor_graph_zoom_playback_follow_and_completion_restore_cursor(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir, source, editor, parent, track = _open_zoom_graph_editor(
        anki_mw,
        ffmpeg_config,
        "editor_graph_zoom_playback_cursor.wav",
    )
    try:
        _install_html_audio_test_driver(editor)
        run_js(editor.web, "window.__aqeSetTimeViewportForTest?.(0, 0, 4000)")
        _shift_drag_region(editor, 0.25, 0.75)
        wait_for_js_condition(
            editor.web,
            """
            (() => {
              window.__aqeSetTimeViewportForTest?.(0, 1000, 2000);
              return window.__aqeGraphStateForTest?.(0) || null;
            })()
            """,
            lambda state: state is not None
            and state["selectionStartMs"] == 1000
            and state["selectionEndMs"] == 3000
            and state["viewportStartMs"] == 1000,
            timeout=5.0,
        )

        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            followed = _wait_for_html_playback(
                editor,
                lambda state: 1900 <= state["progressMs"] <= 2500
                and state["viewportStartMs"] > 1000
                and (state["progressMs"] - state["viewportStartMs"]) >= 750,
                timeout=5.0,
            )
            _force_audio_boundary(editor)
            finished = _state(
                editor,
                lambda state: all(
                    (
                        state["playbackState"] == "stopped",
                        state["cursorMs"] == 1000,
                        state["timecodeFlagVisible"] is True,
                        state["viewportStartMs"] <= 1000,
                        state["viewportEndMs"] >= 1000,
                    ),
                ),
                timeout=5.0,
            )

        assert playback.attempts == []
        assert followed["playButtonLabel"] == "Pause"
        assert followed["progressMs"] - followed["viewportStartMs"] >= 750
        assert finished["playButtonLabel"] == "Play"
    finally:
        editor.set_note(None)
        parent.close()
