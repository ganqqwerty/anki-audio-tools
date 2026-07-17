import { visualizerForOrd } from "./dom-selectors.js";
import { setRecordingCursor } from "./recording-actions-state.js";
import { syncRecordingControls } from "./recording-actions-sync.js";
import { readLearnerRecordingState, writeLearnerPlaybackStatus } from "./recording-state-store.js";
import type { HtmlAudioSessionState } from "./html-audio-session-types.js";

export function publishLearnerPlaybackState(
  ord: number,
  status: "stopped" | "playing" | "paused",
  cursorMs: number | undefined,
  state: HtmlAudioSessionState,
): boolean {
  if (state.kind === "empty" || !state.source || state.source.kind !== "learner_recording") return false;
  writeLearnerPlaybackStatus(ord, status);
  if (cursorMs !== undefined) {
    renderLearnerPlaybackCursor(ord, state.source.startCursorMs + cursorMs);
  }
  syncRecordingControls(ord);
  return true;
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
