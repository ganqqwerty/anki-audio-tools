"""Shared graph and HTML-audio helpers for editor E2E tests."""

from __future__ import annotations

import json

from e2e.helpers import run_js, wait_for_js_condition, wait_for_selector


def _visualizer_js(ord_: int = 0) -> str:
    return """
    (() => {
      const ord = __ORD__;
      const buttonLabel = (button) => button?.querySelector('.aqe-button-label')?.textContent || button?.textContent || "";
      const graphButton = document.querySelector(`[data-testid="aqe-button-${ord}-graph"]`);
      const playButton = document.querySelector(`[data-testid="aqe-button-${ord}-play"]`);
      const deleteButton = document.querySelector(`[data-testid="aqe-button-${ord}-delete-selection"]`);
      const deleteRestButton = document.querySelector(`[data-testid="aqe-button-${ord}-delete-rest"]`);
      const visualizer = document.querySelector(`.aqe-visualizer[data-aqe-field-ord="${ord}"]`);
      if (!visualizer) return null;
      const toolbar = visualizer.querySelector('.aqe-selection-toolbar');
      const toolbarPlay = visualizer.querySelector('.aqe-selection-toolbar-play');
      const toolbarDelete = visualizer.querySelector('.aqe-delete-region-button');
      const toolbarDeleteRest = visualizer.querySelector('.aqe-delete-rest-button');
      const status = document.querySelector(`[data-testid="aqe-status-${ord}"]`);
      const labels = Array.from(visualizer.querySelectorAll('.aqe-hz-label')).map((node) => node.textContent);
      const flag = visualizer.querySelector('.aqe-css-cursor');
      const flagCurrent = visualizer.querySelector('.aqe-css-cursor-flag-current');
      const flagPitch = visualizer.querySelector('.aqe-css-cursor-flag-pitch');
      const cursorMatch = /translate3d\\((-?\\d+(?:\\.\\d+)?)px/.exec(flag?.style.transform || "");
      return {
        active: visualizer.dataset.graphActive === "true",
        busy: visualizer.dataset.graphBusy === "true",
        hidden: visualizer.hidden,
        hasTrack: visualizer.dataset.hasTrack === "true",
        durationMs: Number(visualizer.dataset.durationMs || "0"),
        sourceFilename: visualizer.dataset.sourceFilename || "",
        analyzerName: visualizer.dataset.analyzerName || "",
        anchorMs: Number(visualizer.dataset.anchorMs || "0"),
        cursorMs: Number(visualizer.dataset.cursorMs || "0"),
        progressMs: Number(visualizer.dataset.progressMs || "0"),
        resumeRequiresRestart: visualizer.dataset.resumeRequiresRestart === "true",
        audioClockSrc: document.querySelector(`[data-testid="aqe-audio-clock-${ord}"]`)?.getAttribute("src") || "",
        intensity: visualizer.querySelector('.aqe-intensity')?.getAttribute('d') || "",
        pitchPaths: visualizer.querySelectorAll('.aqe-pitch-path').length,
        xAxisLabels: Array.from(visualizer.querySelectorAll('.aqe-x-label')).map((node) => node.textContent),
        labels,
        cursorX: cursorMatch ? cursorMatch[1] : "",
        timecodeFlagVisible: flag?.style.display === 'block',
        timecodeFlagTransform: flag?.style.transform || "",
        timecodeFlagCurrent: flagCurrent?.textContent || "",
        timecodeFlagPitch: flagPitch?.textContent || "",
        status: status?.textContent || "",
        statusKind: status?.dataset.kind || "",
        graphButtonLabel: buttonLabel(graphButton),
        graphButtonState: graphButton?.dataset.aqeButtonState || "",
        playButtonLabel: buttonLabel(playButton),
        playButtonState: playButton?.dataset.aqeButtonState || "",
        playbackState: visualizer.dataset.playbackState || "stopped",
        playbackStartMs: Number(visualizer.dataset.playbackStartMs || "0"),
        playbackEndMs: Number(visualizer.dataset.playbackEndMs || "0"),
        playbackRegionMode: visualizer.dataset.playbackRegionMode || "full",
        selectionActive: visualizer.dataset.selectionActive === "true",
        selectionStartMs: visualizer.dataset.selectionStartMs ? Number(visualizer.dataset.selectionStartMs) : null,
        selectionEndMs: visualizer.dataset.selectionEndMs ? Number(visualizer.dataset.selectionEndMs) : null,
        selectionDraftActive: visualizer.dataset.selectionDraftActive === "true",
        selectionDraftStartMs: visualizer.dataset.selectionDraftStartMs ? Number(visualizer.dataset.selectionDraftStartMs) : null,
        selectionDraftEndMs: visualizer.dataset.selectionDraftEndMs ? Number(visualizer.dataset.selectionDraftEndMs) : null,
        repeatEnabled: visualizer.dataset.repeatEnabled === "true",
        selectionToolbarHidden: toolbar ? toolbar.hidden : true,
        selectionToolbarPreview: (
          visualizer.dataset.selectionToolbarPreview === "region"
          || visualizer.dataset.selectionToolbarPreview === "rest"
        ) ? visualizer.dataset.selectionToolbarPreview : "none",
        selectionToolbarPlayState: toolbarPlay?.dataset.aqeButtonState || "",
        selectionToolbarPlayAriaLabel: toolbarPlay?.getAttribute("aria-label") || "",
        selectionToolbarDeleteRegionDisabled: toolbarDelete ? toolbarDelete.disabled : true,
        selectionToolbarDeleteRegionHidden: toolbarDelete ? toolbarDelete.hidden : true,
        selectionToolbarDeleteRestDisabled: toolbarDeleteRest ? toolbarDeleteRest.disabled : true,
        selectionToolbarDeleteRestHidden: toolbarDeleteRest ? toolbarDeleteRest.hidden : true,
        regionDeleteButtonDisabled: (toolbarDelete || deleteButton) ? (toolbarDelete || deleteButton).disabled : true,
        regionDeleteButtonHidden: (toolbarDelete || deleteButton) ? (toolbarDelete || deleteButton).hidden : true,
        regionDeleteRestButtonDisabled: (toolbarDeleteRest || deleteRestButton) ? (toolbarDeleteRest || deleteRestButton).disabled : true,
        regionDeleteRestButtonHidden: (toolbarDeleteRest || deleteRestButton) ? (toolbarDeleteRest || deleteRestButton).hidden : true,
        allButtonsDisabled: Array.from(document.querySelectorAll('.aqe-button')).every((button) => button.disabled),
      };
    })()
    """.replace("__ORD__", json.dumps(ord_))


def _wait_for_visualizer_track(editor, predicate=lambda track: True, timeout: float = 10.0, ord_: int = 0):
    return wait_for_js_condition(
        editor.web,
        _visualizer_js(ord_),
        lambda track: track is not None
        and track["hasTrack"] is True
        and track["durationMs"] > 0
        and track["allButtonsDisabled"] is False
        and predicate(track),
        timeout=timeout,
    )


def _graph_state_js(ord_: int = 0) -> str:
    return f"window.__aqeGraphStateForTest ? window.__aqeGraphStateForTest({ord_}) : null"


def _graph_zoom_state_js(ord_: int = 0) -> str:
    return f"""
    (() => {{
      const state = window.__aqeGraphStateForTest?.({ord_});
      if (!state) return null;
      return {{
        cursorMs: state.cursorMs,
        durationMs: state.durationMs,
        selectionEndMs: state.selectionEndMs,
        selectionStartMs: state.selectionStartMs,
        viewportEndMs: state.viewportEndMs,
        viewportStartMs: state.viewportStartMs,
        xAxisLabels: state.xAxisLabels,
      }};
    }})()
    """


def _set_full_time_viewport(editor, ord_: int = 0) -> None:
    wait_for_js_condition(
        editor.web,
        f"""
        (() => {{
          const state = window.__aqeGraphStateForTest?.({ord_});
          if (!state || typeof window.__aqeSetTimeViewportForTest !== "function") return false;
          return window.__aqeSetTimeViewportForTest({ord_}, 0, state.durationMs);
        }})()
        """,
        lambda value: value is True,
        timeout=5.0,
    )


def _click_graph_and_wait(editor, predicate=lambda track: True, ord_: int = 0, timeout: float = 10.0):
    selector = f'[data-testid="aqe-button-{ord_}-graph"]'
    wait_for_selector(editor.web, selector, timeout=5.0)
    wait_for_js_condition(
        editor.web,
        f"""
        (() => {{
          const button = document.querySelector({json.dumps(selector)});
          if (!button) return null;
          button.click();
          return window.__aqeGraphStateForTest ? window.__aqeGraphStateForTest({ord_}) : null;
        }})()
        """,
        lambda state: state is not None and state["active"] is True,
        timeout=5.0,
    )
    return _wait_for_visualizer_track(editor, predicate, timeout=timeout, ord_=ord_)


def _drag_cursor_to_ratio(editor, ratio: float, ord_: int = 0) -> None:
    _set_full_time_viewport(editor, ord_)
    run_js(
        editor.web,
        """
        (() => {
          const ord = __ORD__;
          const ratio = __RATIO__;
          const svg = document.querySelector(`.aqe-visualizer[data-aqe-field-ord="${ord}"] .aqe-visualizer-svg`);
          const rect = svg?.getBoundingClientRect();
          const bounds = window.__aqeGraphPixelBoundsForTest?.(ord);
          if (!svg || !rect || !bounds) return;
          const x = bounds.left + bounds.width * ratio;
          const EventCtor = window.PointerEvent || window.MouseEvent;
          svg.dispatchEvent(new EventCtor('pointerdown', { clientX: x, clientY: rect.top + 40, bubbles: true }));
          window.dispatchEvent(new EventCtor('pointerup', { clientX: x, clientY: rect.top + 40, bubbles: true }));
        })()
        """.replace("__ORD__", json.dumps(ord_)).replace("__RATIO__", json.dumps(ratio)),
    )


def _wait_for_html_playback(editor, predicate=lambda state: True, timeout: float = 5.0, ord_: int = 0):
    return wait_for_js_condition(
        editor.web,
        _graph_state_js(ord_),
        lambda state: state is not None
        and state["playbackState"] == "playing"
        and state["playbackEngine"] == "html"
        and state["progressClockMode"] == "audio"
        and state["audioPlaybackTestDriver"] is True
        and predicate(state),
        timeout=timeout,
    )


def _install_html_audio_test_driver(editor, ord_: int = 0) -> None:
    wait_for_js_condition(
        editor.web,
        f"window.__aqeInstallAudioPlaybackTestDriverForTest"
        f" && window.__aqeInstallAudioPlaybackTestDriverForTest({ord_})",
        lambda value: value is True,
        timeout=5.0,
    )


def _visualizer_ready_js(ord_: int = 0) -> str:
    return f"""
    (() => {{
      const v = document.querySelector(`.aqe-visualizer[data-aqe-field-ord="{ord_}"]`);
      if (!v) return null;
      if (v.dataset.hasTrack !== "true") return null;
      if (!Number(v.dataset.durationMs)) return null;
      if (Array.from(document.querySelectorAll('.aqe-button')).every((b) => b.disabled)) return null;
      return {{ ord: {ord_} }};
    }})()
    """


def _wait_for_visualizer_ready(editor, timeout: float = 10.0, ord_: int = 0):
    return wait_for_js_condition(
        editor.web,
        _visualizer_ready_js(ord_),
        lambda state: state is not None,
        timeout=timeout,
    )


def _visualizer_source_js(ord_: int = 0) -> str:
    return f"""
    (() => {{
      const v = document.querySelector(`.aqe-visualizer[data-aqe-field-ord="{ord_}"]`);
      if (!v || v.dataset.hasTrack !== "true") return null;
      return {{ sourceFilename: v.dataset.sourceFilename || "" }};
    }})()
    """


def _visualizer_cursor_js(ord_: int = 0) -> str:
    return f"""
    (() => {{
      const v = document.querySelector(`.aqe-visualizer[data-aqe-field-ord="{ord_}"]`);
      if (!v || v.dataset.hasTrack !== "true") return null;
      return {{
        cursorMs: Number(v.dataset.cursorMs || "0"),
        durationMs: Number(v.dataset.durationMs || "0"),
      }};
    }})()
    """


def _visualizer_selection_js(ord_: int = 0) -> str:
    return f"""
    (() => {{
      const v = document.querySelector(`.aqe-visualizer[data-aqe-field-ord="{ord_}"]`);
      if (!v || v.dataset.hasTrack !== "true") return null;
      return {{
        selectionActive: v.dataset.selectionActive === "true",
        selectionStartMs: v.dataset.selectionStartMs ? Number(v.dataset.selectionStartMs) : null,
        selectionEndMs: v.dataset.selectionEndMs ? Number(v.dataset.selectionEndMs) : null,
      }};
    }})()
    """


def _visualizer_playback_js(ord_: int = 0) -> str:
    return f"""
    (() => {{
      const v = document.querySelector(`.aqe-visualizer[data-aqe-field-ord="{ord_}"]`);
      if (!v || v.dataset.hasTrack !== "true") return null;
      return {{
        playbackState: v.dataset.playbackState || "stopped",
        playbackStartMs: Number(v.dataset.playbackStartMs || "0"),
        playbackEndMs: Number(v.dataset.playbackEndMs || "0"),
        playbackRegionMode: v.dataset.playbackRegionMode || "full",
        repeatEnabled: v.dataset.repeatEnabled === "true",
        resumeRequiresRestart: v.dataset.resumeRequiresRestart === "true",
      }};
    }})()
    """


def _visualizer_buttons_js(ord_: int = 0) -> str:
    return f"""
    (() => {{
      const graph = document.querySelector(`[data-testid="aqe-button-{ord_}-graph"]`);
      const play = document.querySelector(`[data-testid="aqe-button-{ord_}-play"]`);
      const deleteBtn = document.querySelector(`[data-testid="aqe-button-{ord_}-delete-selection"]`);
      const deleteRest = document.querySelector(`[data-testid="aqe-button-{ord_}-delete-rest"]`);
      const allDisabled = Array.from(document.querySelectorAll('.aqe-button')).every((b) => b.disabled);
      return {{
        graphButtonState: graph?.dataset.aqeButtonState || "",
        playButtonState: play?.dataset.aqeButtonState || "",
        regionDeleteButtonDisabled: deleteBtn ? deleteBtn.disabled : true,
        regionDeleteRestButtonDisabled: deleteRest ? deleteRest.disabled : true,
        allButtonsDisabled: allDisabled,
      }};
    }})()
    """
