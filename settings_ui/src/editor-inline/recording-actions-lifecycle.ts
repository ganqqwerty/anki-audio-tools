import { RecorderCommandKind, type RecorderCommand } from "../lib/generated/contracts.js";
import { sendBridgeEnvelope } from "../lib/bridge-transport.js";
import { visualizerForOrd } from "./dom-selectors.js";
import { clearLearnerVisualizerTrack } from "./visualizer-renderer.js";
import { getSplitButtonState } from "./split-button-state.js";
import {
  learnerRecordingStatusForOrd,
  recordingStartCursorMs,
  resetLearnerRecordingState,
  setLearnerRecordingState,
  setRecordingCursor,
  targetDurationForRecording,
} from "./recording-actions-state.js";
import { setLearnerDurationMsForVisualizer } from "./visualizer-runtime-state.js";
import { startEditorRecordOnce } from "./editor-practice-controller.js";

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
  if (startEditorRecordOnce(
    node,
    ord,
    countdownSeconds * 1000,
    startCursorMs,
    targetDurationMs,
  )) return true;
  resetLearnerRecordingState(ord);
  return false;
}

export function stopLearnerRecording(node: HTMLElement, ord: number): boolean {
  if (typeof node.focus === "function") node.focus();
  window.__aqeActiveField = ord;
  const command: RecorderCommand = {
    fieldOrd: ord,
    kind: RecorderCommandKind.Stop,
    schemaVersion: 1,
  };
  sendBridgeEnvelope("editor.recorder-command", command);
  return true;
}
