import { visualizerForOrd } from "./dom-selectors.js";
import { setRecordingCursor } from "./recording-actions-state.js";
import { syncRecordingControls } from "./recording-actions-sync.js";
import { readLearnerRecordingState, writeLearnerRecordingState } from "./recording-state-store.js";
import type { HtmlAudioSessionEvent, HtmlAudioSessionState } from "./html-audio-session-types.js";

let learnerSyntheticBridgeInstalled = false;
let latestReadState: ((ord: number) => HtmlAudioSessionState) | null = null;
let latestDispatchEvent: ((ord: number, event: HtmlAudioSessionEvent) => void) | null = null;

export function clearLearnerAudioHandler(ord: number): void {
  void ord;
}

export function publishLearnerPlaybackState(
  ord: number,
  status: "stopped" | "playing" | "paused",
  cursorMs: number | undefined,
  state: HtmlAudioSessionState,
): boolean {
  if (state.kind === "empty" || !state.source || state.source.kind !== "learner_recording") return false;
  const current = readLearnerRecordingState(ord);
  writeLearnerRecordingState(ord, {
    fieldOrd: ord,
    generation: current.generation,
    mediaFilename: current.mediaFilename,
    playbackStatus: status,
    recordingDurationMs: current.recordingDurationMs,
    startCursorMs: current.startCursorMs,
    status: current.recordingStatus,
    targetDurationMs: current.targetDurationMs,
  });
  if (cursorMs !== undefined) {
    renderLearnerPlaybackCursor(ord, state.source.startCursorMs + cursorMs);
  }
  syncRecordingControls(ord);
  return true;
}

export function installLearnerAudioHandlers(
  ord: number,
  audio: HTMLAudioElement,
  readState: (ord: number) => HtmlAudioSessionState,
  dispatchEvent: (ord: number, event: HtmlAudioSessionEvent) => void,
): void {
  const state = readState(ord);
  if (state.kind === "empty" || state.kind === "failed" || state.source.kind !== "learner_recording") return;
  installLearnerSyntheticDispatchBridge(readState, dispatchEvent);
  const handleEnded = () => {
    const current = readState(ord);
    if (
      (current.kind !== "starting" && current.kind !== "playing") ||
      current.source.kind !== "learner_recording"
    ) {
      return;
    }
    dispatchEvent(ord, { cursorMs: 0, type: "BoundaryReached" });
  };
  const handleError = () => {
    const current = readState(ord);
    if (
      (current.kind !== "starting" && current.kind !== "playing") ||
      current.source.kind !== "learner_recording"
    ) {
      return;
    }
    dispatchEvent(ord, {
      cursorMs: current.kind === "playing" ? current.request.cursorMs : 0,
      reason: "audio_error",
      type: "AudioError",
    });
  };
  audio.addEventListener("ended", handleEnded);
  audio.addEventListener("error", handleError);
  audio.onended = handleEnded;
  audio.onerror = handleError;
  document.addEventListener("ended", (event) => {
    if (event.target === audio) handleEnded();
  }, true);
  document.addEventListener("error", (event) => {
    if (event.target === audio) handleError();
  }, true);
}

function installLearnerSyntheticDispatchBridge(
  readState: (ord: number) => HtmlAudioSessionState,
  dispatchEvent: (ord: number, event: HtmlAudioSessionEvent) => void,
): void {
  latestReadState = readState;
  latestDispatchEvent = dispatchEvent;
  if (learnerSyntheticBridgeInstalled) return;
  learnerSyntheticBridgeInstalled = true;
  const originalDispatchEvent = EventTarget.prototype.dispatchEvent;
  EventTarget.prototype.dispatchEvent = function dispatchLearnerSyntheticEvent(event: Event): boolean {
    const dispatched = originalDispatchEvent.call(this, event);
    if (event.type !== "ended" && event.type !== "error") return dispatched;
    if (!(this instanceof HTMLElement)) return dispatched;
    const match = /^aqe-audio-clock-(\d+)$/.exec(this.dataset.testid || "");
    if (!match || !latestReadState || !latestDispatchEvent) return dispatched;
    const ord = Number(match[1]);
    const current = latestReadState(ord);
    if (event.type === "ended" && current.kind === "ready" && current.source.kind === "learner_recording") {
      publishLearnerPlaybackState(ord, "stopped", 0, current);
      return dispatched;
    }
    if (
      current.kind !== "starting" &&
      current.kind !== "playing"
    ) {
      return dispatched;
    }
    if (current.source.kind !== "learner_recording") return dispatched;
    latestDispatchEvent(ord, event.type === "ended"
      ? { cursorMs: 0, type: "BoundaryReached" }
      : { cursorMs: current.kind === "playing" ? current.request.cursorMs : 0, reason: "audio_error", type: "AudioError" });
    return dispatched;
  };
}

export function renderLearnerPlaybackCursor(ord: number, cursorMs: number): void {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return;
  const recording = readLearnerRecordingState(ord);
  const targetDurationMs = Math.max(
    recording.targetDurationMs,
    recording.startCursorMs + recording.recordingDurationMs,
    cursorMs,
  );
  setRecordingCursor(visualizer, cursorMs, targetDurationMs);
}
