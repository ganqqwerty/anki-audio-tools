import { visualizerForOrd } from "./dom-selectors.js";
import { setRecordingCursor } from "./recording-actions-state.js";
import { syncRecordingControls } from "./recording-actions-sync.js";
import { readLearnerRecordingState, writeLearnerRecordingState } from "./recording-state-store.js";
import type { HtmlAudioSessionEvent, HtmlAudioSessionState } from "./html-audio-session-types.js";

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
  const handleEnded = () => {
    const current = readState(ord);
    if (
      (current.kind !== "starting" && current.kind !== "playing") ||
      current.source.kind !== "learner_recording"
    ) {
      return;
    }
    dispatchEvent(ord, { cursorMs: 0, type: "BoundaryReached" });
    publishLearnerPlaybackState(ord, "stopped", 0, readState(ord));
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
