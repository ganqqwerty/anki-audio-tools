import type { ProsodyPayload } from "../lib/generated/contracts.js";
import type { LearnerRecordingStatePayload } from "./recording-state.js";
import { setLearnerRecordingState as setLearnerRecordingStateImpl, setLearnerVisualizer as setLearnerVisualizerImpl, resetLearnerRecordingState as resetLearnerRecordingStateImpl, resolveFieldOrd } from "./recording-actions-state.js";
import { syncRecordingControls } from "./recording-actions-sync.js";

export { dispatchLearnerRecordingPrimary, startLearnerRecordingCountdown, stopLearnerRecording } from "./recording-actions-lifecycle.js";
export { syncRecordingControls, syncAllRecordingControls } from "./recording-actions-sync.js";

export function setLearnerRecordingState(payload: LearnerRecordingStatePayload): void {
  const shouldSync = setLearnerRecordingStateImpl(payload);
  if (shouldSync) {
    syncRecordingControls(resolveFieldOrd(payload.fieldOrd));
  }
}

export function setLearnerVisualizer(ord: number, rawTrack: ProsodyPayload): void {
  const shouldSync = setLearnerVisualizerImpl(ord, rawTrack);
  if (shouldSync) {
    syncRecordingControls(ord);
  }
}

export function resetLearnerRecordingState(ord: number, options: { clearOverlay?: boolean } = {}): void {
  const shouldSync = resetLearnerRecordingStateImpl(ord, options);
  if (shouldSync) {
    syncRecordingControls(ord);
  }
}
