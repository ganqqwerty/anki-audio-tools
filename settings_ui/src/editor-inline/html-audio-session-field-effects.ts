import { focusAndSendCommand } from "./bridge.js";
import { clearStatus, restoreStatusForOrd, setCommandButtonLabel } from "./control-actions.js";
import { visualizerForOrd } from "./dom-selectors.js";
import { setCachedProgressMs, updateFieldState } from "./field-state-store.js";
import type { HtmlAudioStartRequest } from "./html-audio-session-machine.js";
import { syncSelectionToolbar } from "./selection-toolbar-state.js";
import {
  preserveStatusOnPlaybackEndRuntime,
  setPreserveStatusOnPlaybackEndRuntime,
} from "./visualizer-runtime-state.js";
import { ensurePlaybackCursorVisible } from "./viewport-actions.js";

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

export function completePlayback(ord: number, cursorMs: number): void {
  const visualizer = visualizerForOrd(ord);
  const preserveStatus = visualizer ? preserveStatusOnPlaybackEndRuntime(visualizer) : false;
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
    clearStatus(ord);
  }
  if (visualizer) {
    setPreserveStatusOnPlaybackEndRuntime(visualizer, false);
  }
  setCommandButtonLabel(ord, "aqe:play", "Play");
  if (visualizer) syncSelectionToolbar(visualizer);
  window.__aqeActiveField = ord;
  focusAndSendCommand(ord, "aqe:play-ended");
}
