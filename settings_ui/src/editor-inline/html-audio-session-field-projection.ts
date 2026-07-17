import { clearPlaybackStatusForOrd, restoreStatusForOrd, setCommandButtonLabel } from "./control-actions.js";
import { visualizerForOrd } from "./dom-selectors.js";
import { readFieldState, setCachedProgressMs, updateFieldState } from "./field-state-store.js";
import { publishLearnerPlaybackState } from "./html-audio-session-learner-projection.js";
import { syncSelectionToolbar } from "./selection-toolbar-state.js";
import type { HtmlAudioSessionState, HtmlAudioStartRequest } from "./html-audio-session-types.js";
import { ensurePlaybackCursorVisible } from "./viewport-actions.js";
import { renderCursor } from "./visualizer-renderer.js";

type HtmlAudioPlaybackStatus = "stopped" | "playing" | "paused";

interface PublishPlaybackStateOptions {
  cursorMs: number | undefined;
  ord: number;
  request: HtmlAudioStartRequest | null;
  session: HtmlAudioSessionState;
  status: HtmlAudioPlaybackStatus;
}

export function publishPlaybackState(options: PublishPlaybackStateOptions): void {
  const { cursorMs, ord, request, session, status } = options;
  if (publishLearnerPlaybackState(ord, status, cursorMs, session)) {
    return;
  }
  updateFieldState(ord, (field) => ({
    ...field,
    cursor: cursorMs === undefined
      ? field.cursor
      : {
          ...field.cursor,
          ms: cursorMs,
          progressMs: cursorMs,
        },
    playback: {
      ...field.playback,
      clockMode: status === "playing" ? "audio" : "stopped",
      endMs: request?.endMs ?? field.playback.endMs,
      regionMode: request?.regionMode ?? field.playback.regionMode,
      state: status,
      startMs: request?.cursorMs ?? field.playback.startMs,
    },
  }));
  setCommandButtonLabel(ord, "aqe:play", status === "playing" ? "Pause" : "Play");
  const visualizer = visualizerForOrd(ord);
  if (visualizer) syncSelectionToolbar(visualizer);
}

export function publishRepeatWaitingState(
  ord: number,
  cursorMs: number,
  request: HtmlAudioStartRequest | null,
): void {
  setCachedProgressMs(ord, cursorMs, visualizerForOrd(ord));
  updateFieldState(ord, (field) => ({
    ...field,
    cursor: {
      ...field.cursor,
      ms: cursorMs,
      progressMs: cursorMs,
    },
    playback: {
      ...field.playback,
      clockMode: "stopped",
      endMs: request?.endMs ?? field.playback.endMs,
      regionMode: request?.regionMode ?? field.playback.regionMode,
      state: "playing",
      startMs: request?.cursorMs ?? field.playback.startMs,
    },
  }));
  setCommandButtonLabel(ord, "aqe:play", "Pause");
  const visualizer = visualizerForOrd(ord);
  if (visualizer) {
    ensurePlaybackCursorVisible(visualizer, cursorMs);
    syncSelectionToolbar(visualizer);
  }
}

export function completePlayback(ord: number, cursorMs: number, preserveStatus = false): void {
  const visualizer = visualizerForOrd(ord);
  updateFieldState(ord, (field) => ({
    ...field,
    cursor: {
      ...field.cursor,
      ms: cursorMs,
      progressMs: cursorMs,
    },
    playback: {
      ...field.playback,
      clockMode: "stopped",
      state: "stopped",
    },
  }));
  setCachedProgressMs(ord, cursorMs, visualizer);
  if (preserveStatus) {
    restoreStatusForOrd(ord);
  } else {
    clearPlaybackStatusForOrd(ord);
  }
  if (visualizer) {
    ensurePlaybackCursorVisible(visualizer, cursorMs);
    renderCursor(visualizer, cursorMs, readFieldState(ord).graph.durationMs);
  }
  setCommandButtonLabel(ord, "aqe:play", "Play");
  if (visualizer) syncSelectionToolbar(visualizer);
  window.__aqeActiveField = ord;
}
