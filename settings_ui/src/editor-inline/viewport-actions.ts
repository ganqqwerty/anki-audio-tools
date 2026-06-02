import type { VisualizerElement } from "./types.js";
import {
  msVisibleInViewport,
  panTimeViewport,
  timeViewportSpan,
  type TimeViewport,
} from "./time-viewport.js";
import {
  renderCursor,
  renderCurrentSelectionFromState,
  renderProsodyTracks,
} from "./visualizer-renderer.js";
import {
  readVisualizerCursorMs,
  readVisualizerDurationMs,
  readVisualizerTimeViewport,
  writeVisualizerTimeViewport,
} from "./visualizer-state.js";

const PLAYBACK_FOLLOW_MARGIN_RATIO = 0.12;

export function applyVisualizerTimeViewport(visualizer: VisualizerElement, viewport: TimeViewport): void {
  writeVisualizerTimeViewport(visualizer, viewport);
  redrawVisualizerForCurrentViewport(visualizer);
}

export function redrawVisualizerForCurrentViewport(visualizer: VisualizerElement): void {
  if (visualizer.dataset.hasTrack === "true") {
    renderProsodyTracks(visualizer);
  }
  renderCurrentSelectionFromState(visualizer);
  renderCursor(
    visualizer,
    readVisualizerCursorMs(visualizer),
    readVisualizerDurationMs(visualizer),
  );
  visualizer.dispatchEvent(new CustomEvent("aqe-viewport-rendered", { bubbles: false }));
}

export function ensurePlaybackCursorVisible(visualizer: VisualizerElement, cursorMs: number): boolean {
  const viewport = readVisualizerTimeViewport(visualizer);
  const span = timeViewportSpan(viewport);
  if (viewport.durationMs <= 0 || span >= viewport.durationMs) return false;
  if (msVisibleInViewport(cursorMs, viewport)) {
    const marginMs = span * PLAYBACK_FOLLOW_MARGIN_RATIO;
    if (cursorMs >= viewport.startMs + marginMs && cursorMs <= viewport.endMs - marginMs) {
      return false;
    }
  }
  const targetStart = cursorMs - span * PLAYBACK_FOLLOW_MARGIN_RATIO;
  applyVisualizerTimeViewport(visualizer, panTimeViewport(viewport, targetStart - viewport.startMs));
  return true;
}
