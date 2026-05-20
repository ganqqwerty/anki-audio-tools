import { t } from "../lib/i18n.js";
import { focusAndSendCommandPayload } from "./bridge.js";
import { allControls, buttonFor, controlsForOrd, visualizerForOrd } from "./dom-selectors.js";
import { graphSettingsForField } from "./graph-split-state.js";
import type { LearnerRecordingStatePayload, LearnerRecordingStatus } from "./recording-state.js";
import { clearLearnerVisualizerTrack } from "./visualizer-renderer.js";

const RECORDING_BUSY_STATUSES = new Set<LearnerRecordingStatus>([
  "countdown",
  "recording",
  "stopping",
  "analyzing",
]);

export function startLearnerRecordingCountdown(node: HTMLElement, ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  const targetDurationMs = Number(visualizer?.dataset.durationMs || "0");
  if (!visualizer || visualizer.dataset.hasTrack !== "true" || targetDurationMs <= 0) return false;

  if (visualizer.__aqeRecordCountdownTimer) {
    window.clearTimeout(visualizer.__aqeRecordCountdownTimer);
  }
  clearLearnerVisualizerTrack(visualizer);
  setLearnerRecordingState({
    fieldOrd: ord,
    status: "countdown",
    targetDurationMs,
  });
  visualizer.__aqeRecordCountdownTimer = window.setTimeout(() => {
    visualizer.__aqeRecordCountdownTimer = null;
    if (!recordingTargetReady(ord)) return;
    if (typeof node.focus === "function") node.focus();
    window.__aqeActiveField = ord;
    focusAndSendCommandPayload(ord, {
      command: "aqe:record-voice",
      fieldOrd: ord,
      graphSettings: graphSettingsForField(ord),
    });
  }, 0);
  return true;
}

export function setLearnerRecordingState(payload: LearnerRecordingStatePayload): void {
  const ord = resolveFieldOrd(payload.fieldOrd);
  const controls = controlsForOrd(ord);
  if (!controls) return;
  const status = payload.status || "idle";
  controls.dataset.learnerRecordingStatus = status;
  controls.dataset.learnerRecordingGeneration = payload.generation == null ? "" : String(payload.generation);
  controls.dataset.learnerRecordingMediaFilename = payload.mediaFilename || "";
  controls.dataset.learnerRecordingTargetDurationMs = payload.targetDurationMs == null
    ? ""
    : String(payload.targetDurationMs);

  const visualizer = visualizerForOrd(ord);
  if (visualizer) {
    visualizer.dataset.learnerRecordingStatus = status;
  }

  const statusNode = controls.querySelector<HTMLElement>(".aqe-recording-status");
  if (statusNode) {
    statusNode.textContent = recordingStatusText(payload);
    statusNode.dataset.kind = status === "failed"
      ? "error"
      : isLearnerRecordingBusy(status)
        ? "processing"
        : "info";
    statusNode.title = payload.mediaFilename || "";
  }
  syncRecordingControls(ord);
}

export function resetLearnerRecordingState(ord: number): void {
  const visualizer = visualizerForOrd(ord);
  if (visualizer?.__aqeRecordCountdownTimer) {
    window.clearTimeout(visualizer.__aqeRecordCountdownTimer);
    visualizer.__aqeRecordCountdownTimer = null;
  }
  setLearnerRecordingState({
    fieldOrd: ord,
    status: "idle",
  });
}

export function syncAllRecordingControls(): void {
  allControls().forEach((controls) => {
    syncRecordingControls(Number(controls.dataset.aqeFieldOrd || "0"));
  });
}

export function syncRecordingControls(ord: number): void {
  const controls = controlsForOrd(ord);
  const recordButton = buttonFor(ord, "aqe:record-voice");
  const playButton = buttonFor(ord, "aqe:play-recording");
  const status = recordingStatusForControls(controls);
  const busy = document.body.dataset.aqeBusy === "true" || controls?.dataset.busy === "true";
  const recordingBusy = isLearnerRecordingBusy(status);
  if (recordButton) recordButton.disabled = busy || recordingBusy || !recordingTargetReady(ord);
  if (playButton) playButton.disabled = busy || recordingBusy || status !== "ready";
}

function recordingStatusText(payload: LearnerRecordingStatePayload): string {
  if (payload.status === "countdown") return t("editor.recording.countdown");
  if (payload.status === "recording") return t("editor.recording.recording");
  if (payload.status === "stopping") return t("editor.recording.stopping");
  if (payload.status === "analyzing") return t("editor.status.analyzing");
  if (payload.status === "ready") return t("editor.recording.ready");
  if (payload.status === "failed") return payload.failureMessage || t("editor.recording.failed");
  return "";
}

function recordingTargetReady(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  return !!visualizer && visualizer.dataset.hasTrack === "true" && Number(visualizer.dataset.durationMs || "0") > 0;
}

function recordingStatusForControls(controls: HTMLElement | null): LearnerRecordingStatus {
  const status = controls?.dataset.learnerRecordingStatus;
  if (
    status === "countdown"
    || status === "recording"
    || status === "stopping"
    || status === "analyzing"
    || status === "ready"
    || status === "failed"
  ) {
    return status;
  }
  return "idle";
}

function isLearnerRecordingBusy(status: LearnerRecordingStatus): boolean {
  return RECORDING_BUSY_STATUSES.has(status);
}

function resolveFieldOrd(fieldOrd: number | null | undefined): number {
  if (typeof fieldOrd === "number" && Number.isFinite(fieldOrd)) return fieldOrd;
  return Number(window.__aqeActiveField ?? 0);
}
