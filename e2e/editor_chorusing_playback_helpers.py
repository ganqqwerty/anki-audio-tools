"""Shared helpers for marker-guided selected repeat playback e2e tests."""

from __future__ import annotations

from e2e.editor_region_loop_helpers import _state
from e2e.helpers import run_js, wait_for_js_condition


def _configure_play_repeat(editor, *, pause_seconds: float) -> None:
    wait_for_js_condition(
        editor.web,
        f"""
        (() => {{
          const menu = document.querySelector('[data-testid="aqe-split-0-play-menu"]');
          if (!menu) return null;
          if (menu.getAttribute("aria-expanded") !== "true") menu.click();
          const repeat = document.querySelector('[data-testid="aqe-repeat-0"]');
          const pause = document.querySelector('[data-testid="aqe-split-0-repeat-value"]');
          if (!repeat || !pause) return null;
          if (repeat.getAttribute("aria-pressed") !== "true") repeat.click();
          pause.value = "{pause_seconds}";
          pause.dispatchEvent(new Event("input", {{ bubbles: true }}));
          return window.__aqeGraphStateForTest?.(0) || null;
        }})()
        """,
        lambda state: state is not None
        and state["repeatEnabled"] is True
        and state["repeatPauseSeconds"] == pause_seconds,
        timeout=5.0,
    )


def _configure_play_auto_advance(editor, *, pause_seconds: float, repeat_count: int) -> None:
    wait_for_js_condition(
        editor.web,
        f"""
        (() => {{
          const menu = document.querySelector('[data-testid="aqe-split-0-play-menu"]');
          if (!menu) return null;
          if (menu.getAttribute("aria-expanded") !== "true") menu.click();
          const repeat = document.querySelector('[data-testid="aqe-repeat-0"]');
          const pause = document.querySelector('[data-testid="aqe-split-0-repeat-value"]');
          const autoAdvance = document.querySelector('[data-testid="aqe-split-0-play-auto-advance"]');
          const repeatCount = document.querySelector('[data-testid="aqe-split-0-play-auto-advance-repeats"]');
          if (!repeat || !pause || !autoAdvance || !repeatCount) return null;
          if (repeat.getAttribute("aria-pressed") !== "true") repeat.click();
          pause.value = "{pause_seconds}";
          pause.dispatchEvent(new Event("input", {{ bubbles: true }}));
          if (!autoAdvance.checked) autoAdvance.click();
          repeatCount.value = "{repeat_count}";
          repeatCount.dispatchEvent(new Event("input", {{ bubbles: true }}));
          return window.__aqeGraphStateForTest?.(0) || null;
        }})()
        """,
        lambda state: state is not None
        and state["repeatEnabled"] is True
        and state["repeatPauseSeconds"] == pause_seconds
        and state["chorusingAutoAdvance"] is True
        and state["chorusingRepeatCount"] == repeat_count,
        timeout=5.0,
    )


def _click_play(editor) -> None:
    run_js(
        editor.web,
        """
        (() => {
          const button = document.querySelector('[data-testid="aqe-button-0-play"]');
          if (!button || button.disabled) return false;
          button.click();
          return true;
        })()
        """,
    )
    _state(editor, lambda state: state["playbackState"] == "playing", timeout=5.0)


def _click_play_from_split_menu(editor) -> None:
    run_js(
        editor.web,
        """
        (() => {
          const button = document.querySelector('[data-testid="aqe-split-0-play-run"]');
          if (!button || button.disabled) return false;
          button.click();
          return true;
        })()
        """,
    )
    _state(editor, lambda state: state["playbackState"] == "playing", timeout=5.0)


def _click_pause(editor) -> None:
    run_js(
        editor.web,
        """
        (() => {
          const button = document.querySelector('[data-testid="aqe-button-0-play"]');
          if (!button || button.disabled) return false;
          button.click();
          return true;
        })()
        """,
    )
    _state(editor, lambda state: state["playbackState"] == "paused", timeout=5.0)
