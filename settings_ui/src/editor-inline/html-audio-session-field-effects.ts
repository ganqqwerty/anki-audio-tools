import { focusAndSendCommand } from "./bridge.js";
import { clearStatus, restoreStatusForOrd, setCommandButtonLabel } from "./control-actions.js";
import { visualizerForOrd } from "./dom-selectors.js";
import { setCachedProgressMs, updateFieldState } from "./field-state-store.js";
import { audioForOrd } from "./html-audio-session-audio-element.js";
import {
  installLearnerAudioHandlers,
  publishLearnerPlaybackState,
} from "./html-audio-session-learner-effects.js";
import { syncSelectionToolbar } from "./selection-toolbar-state.js";
import type { HtmlAudioSessionEvent, HtmlAudioSessionState, HtmlAudioStartRequest } from "./html-audio-session-types.js";
import {
  preserveStatusOnPlaybackEndRuntime,
  setPreserveStatusOnPlaybackEndRuntime,
} from "./visualizer-runtime-state.js";
import { ensurePlaybackCursorVisible } from "./viewport-actions.js";

type HtmlAudioPlaybackStatus = "stopped" | "playing" | "paused";
type ReadHtmlAudioSessionState = (ord: number) => HtmlAudioSessionState;
type DispatchHtmlAudioSessionEvent = (ord: number, event: HtmlAudioSessionEvent) => void;

interface PublishPlaybackStateOptions {
  cursorMs: number | undefined;
  dispatchEvent: DispatchHtmlAudioSessionEvent;
  ord: number;
  readState: ReadHtmlAudioSessionState;
  request: HtmlAudioStartRequest | null;
  session: HtmlAudioSessionState;
  status: HtmlAudioPlaybackStatus;
}

export function publishPlaybackState(options: PublishPlaybackStateOptions): void {
  const { cursorMs, dispatchEvent, ord, readState, request, session, status } = options;
  if (publishLearnerPlaybackState(ord, status, cursorMs, session)) {
    const audio = audioForOrd(ord);
    if (audio) installLearnerAudioHandlers(ord, audio, readState, dispatchEvent);
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
