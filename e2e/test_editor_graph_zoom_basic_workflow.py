"""E2E tests for inline editor graph horizontal zoom - basic zoom operations."""

from __future__ import annotations

from pathlib import Path

from e2e.editor_graph_helpers import (
    _click_graph_and_wait,
    _graph_zoom_state_js,
)
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
)
from e2e.helpers import (
    generate_tone,
    run_js,
    wait_for_js_condition,
    wait_for_selector,
)


def _open_zoom_graph_editor(anki_mw, ffmpeg_config, filename: str, duration_s: float = 4.0):
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / filename
    generate_tone(ffmpeg_config, source, duration_s=duration_s)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)
    editor, parent = _open_editor(anki_mw, note)
    wait_for_selector(editor.web, _button_selector("aqe:analyze"), timeout=10.0)
    track = _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
    return media_dir, source, editor, parent, track


def test_editor_graph_short_clip_initial_viewport_uses_canonical_pixel_scale(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, editor, parent, _track = _open_zoom_graph_editor(
        anki_mw,
        ffmpeg_config,
        "editor_graph_zoom_short_canonical.wav",
        duration_s=0.5,
    )
    try:
        state = wait_for_js_condition(
            editor.web,
            """
            (() => {
              const state = window.__aqeGraphStateForTest?.(0);
              const bounds = window.__aqeGraphPixelBoundsForTest?.(0);
              if (!state || !bounds) return null;
              const span = state.viewportEndMs - state.viewportStartMs;
              return {
                ...state,
                audioWidthPx: span > 0 ? bounds.width * state.durationMs / span : 0,
              };
            })()
            """,
            lambda value: value is not None
            and value["viewportStartMs"] == 0
            and value["viewportEndMs"] > value["durationMs"]
            and abs(value["audioWidthPx"] - 160) <= 12,
            timeout=5.0,
        )

        assert state["durationMs"] <= 700
    finally:
        editor.set_note(None)
        parent.close()


def test_editor_graph_long_clip_initial_viewport_is_not_full_fit(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, editor, parent, _track = _open_zoom_graph_editor(
        anki_mw,
        ffmpeg_config,
        "editor_graph_zoom_long_canonical.wav",
        duration_s=4.0,
    )
    try:
        state = wait_for_js_condition(
            editor.web,
            _graph_zoom_state_js(),
            lambda value: value is not None
            and value["viewportStartMs"] == 0
            and value["viewportEndMs"] < value["durationMs"],
            timeout=5.0,
        )

        assert state["viewportEndMs"] > 1000
    finally:
        editor.set_note(None)
        parent.close()


def test_editor_graph_zoom_in_narrows_viewport_around_cursor(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, editor, parent, _track = _open_zoom_graph_editor(
        anki_mw,
        ffmpeg_config,
        "editor_graph_zoom_in_cursor.wav",
    )
    try:
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
    finally:
        editor.set_note(None)
        parent.close()


def test_editor_graph_zoom_scroll_to_end_snaps_viewport(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, editor, parent, _track = _open_zoom_graph_editor(
        anki_mw,
        ffmpeg_config,
        "editor_graph_zoom_scroll_end.wav",
    )
    try:
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
            and value["viewportEndMs"] == value["durationMs"],
            timeout=5.0,
        )
        assert scrolled["viewportStartMs"] > 0
    finally:
        editor.set_note(None)
        parent.close()


def test_editor_graph_zoom_fit_restores_full_viewport(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, editor, parent, _track = _open_zoom_graph_editor(
        anki_mw,
        ffmpeg_config,
        "editor_graph_zoom_fit.wav",
    )
    try:
        run_js(
            editor.web,
            """
            (() => {
              const state = window.__aqeGraphStateForTest?.(0);
              if (!state) return false;
              window.__aqeSetCursorForTest?.(0, state.durationMs / 2, false);
              document.querySelector('[data-testid="aqe-zoom-in-0"]')?.click();
              return true;
            })()
            """,
        )
        wait_for_js_condition(
            editor.web,
            _graph_zoom_state_js(),
            lambda value: value is not None and value["viewportStartMs"] > 0,
            timeout=5.0,
        )
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
        assert fit["viewportStartMs"] == 0
    finally:
        editor.set_note(None)
        parent.close()
