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
import { readFieldState } from "./field-state-store.js";

function fieldOrd(v: VisualizerElement): number {
  return Number(v.dataset.aqeFieldOrd || "0");
}

const PLAYBACK_REVEAL_MARGIN_RATIO = 0.12;
const PLAYBACK_FOLLOW_CURSOR_RATIO = 1 - PLAYBACK_REVEAL_MARGIN_RATIO;

export function applyVisualizerTimeViewport(visualizer: VisualizerElement, viewport: TimeViewport): void {
  writeVisualizerTimeViewport(visualizer, viewport);
  redrawVisualizerForCurrentViewport(visualizer);
}

export function redrawVisualizerForCurrentViewport(visualizer: VisualizerElement): void {
  if (readFieldState(fieldOrd(visualizer)).graph.hasTrack) {
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

export function playbackFollowViewport(viewport: TimeViewport, cursorMs: number): TimeViewport | null {
  const span = timeViewportSpan(viewport);
  if (viewport.durationMs <= 0 || span >= viewport.durationMs) return null;
  if (
    msVisibleInViewport(cursorMs, viewport)
    && cursorMs <= viewport.startMs + span * PLAYBACK_FOLLOW_CURSOR_RATIO
  ) {
    return null;
  }
  const targetRatio = cursorMs < viewport.startMs
    ? PLAYBACK_REVEAL_MARGIN_RATIO
    : PLAYBACK_FOLLOW_CURSOR_RATIO;
  const targetStart = cursorMs - span * targetRatio;
  const nextViewport = panTimeViewport(viewport, targetStart - viewport.startMs);
  return sameTimeViewport(viewport, nextViewport) ? null : nextViewport;
}

export function ensurePlaybackCursorVisible(visualizer: VisualizerElement, cursorMs: number): boolean {
  const viewport = readVisualizerTimeViewport(visualizer);
  const nextViewport = playbackFollowViewport(viewport, cursorMs);
  if (!nextViewport) return false;
  applyVisualizerTimeViewport(visualizer, nextViewport);
  return true;
}

function sameTimeViewport(left: TimeViewport, right: TimeViewport): boolean {
  return left.durationMs === right.durationMs
    && left.endMs === right.endMs
    && left.startMs === right.startMs;
}
