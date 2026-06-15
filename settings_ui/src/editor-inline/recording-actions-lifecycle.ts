import { graphSettingsForField } from "./graph-split-state.js";
import { focusAndSendCommand, focusAndSendCommandPayload } from "./bridge.js";
import { visualizerForOrd } from "./dom-selectors.js";
import { clearLearnerVisualizerTrack } from "./visualizer-renderer.js";
import { getSplitButtonState } from "./split-button-state.js";
import {
  learnerRecordingStatusForOrd,
  recordingStartCursorMs,
  recordingTargetReady,
  resetLearnerRecordingState,
  setLearnerRecordingState,
  setRecordingCursor,
  targetDurationForRecording,
} from "./recording-actions-state.js";
import { clearGraphCountdownOverlay } from "./graph-countdown-overlay.js";
import { setLearnerDurationMsForVisualizer } from "./visualizer-runtime-state.js";

export function dispatchLearnerRecordingPrimary(node: HTMLElement, ord: number): boolean {
  const status = learnerRecordingStatusForOrd(ord);
  if (status === "recording") {
    return stopLearnerRecording(node, ord);
  }
  if (status === "countdown" || status === "stopping" || status === "analyzing") {
    return false;
  }
  return startLearnerRecordingCountdown(node, ord);
}

export function startLearnerRecordingCountdown(node: HTMLElement, ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  const targetDurationMs = targetDurationForRecording(visualizer);
  if (!visualizer || targetDurationMs <= 0) return false;

  window.__aqeStopEditorPlayback?.(ord);
  clearLearnerVisualizerTrack(visualizer);
  delete visualizer.__aqeLearnerTrack;
  const startCursorMs = recordingStartCursorMs(visualizer, targetDurationMs);
  setLearnerDurationMsForVisualizer(visualizer, 0);
  setLearnerRecordingState({
    fieldOrd: ord,
    startCursorMs,
    status: "idle",
    targetDurationMs,
  });
  setRecordingCursor(visualizer, startCursorMs, targetDurationMs);

  const countdownSeconds = getSplitButtonState(ord).voiceRecordingCountdownSeconds;
  if (visualizer.__aqeRecordCountdownTimer) {
    window.clearTimeout(visualizer.__aqeRecordCountdownTimer);
    visualizer.__aqeRecordCountdownTimer = null;
  }
  const dispatch = (): void => {
    visualizer.__aqeRecordCountdownTimer = null;
    if (!recordingTargetReady(ord)) {
      resetLearnerRecordingState(ord);
      return;
    }
    clearRecordingCountdownOverlay(visualizer);
    if (typeof node.focus === "function") node.focus();
    window.__aqeActiveField = ord;
    focusAndSendCommandPayload(ord, {
      command: "aqe:record-voice",
      fieldOrd: ord,
      graphSettings: graphSettingsForField(ord),
      startCursorMs,
    });
  };
  if (countdownSeconds <= 0) {
    dispatch();
    return true;
  }
  let remaining = countdownSeconds;
  const tick = (): void => {
    if (remaining <= 0) {
      dispatch();
      return;
    }
    setLearnerRecordingState({
      fieldOrd: ord,
      status: "countdown",
      countdownSeconds: remaining,
      startCursorMs,
      targetDurationMs,
    });
    remaining -= 1;
    visualizer.__aqeRecordCountdownTimer = window.setTimeout(tick, 1000);
  };
  tick();
  return true;
}

export function stopLearnerRecording(node: HTMLElement, ord: number): boolean {
  if (typeof node.focus === "function") node.focus();
  window.__aqeActiveField = ord;
  focusAndSendCommand(ord, "aqe:stop-recording");
  return true;
}

function clearRecordingCountdownOverlay(visualizer: HTMLElement): void {
  clearGraphCountdownOverlay(visualizer);
}
