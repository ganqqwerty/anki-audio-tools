import type { ProsodyPayload } from "../lib/generated/contracts.js";
import { t } from "../lib/i18n.js";
import { clearGraphCountdownOverlay, renderGraphCountdownOverlay } from "./graph-countdown-overlay.js";
import { controlsForOrd, visualizerForOrd } from "./dom-selectors.js";
import { ensurePlaybackCursorVisible } from "./viewport-actions.js";
import { clearLearnerVisualizerTrack, renderCursor, renderLearnerVisualizerTrack, renderProsodyTracks } from "./visualizer-renderer.js";
import { readVisualizerTargetDurationMs } from "./visualizer-state.js";
import type { LearnerPlaybackStatus, LearnerRecordingStatePayload, LearnerRecordingStatus } from "./recording-state.js";
import { normalizeTrack, type NormalizedProsodyTrack, type ProsodyPoint, type VisualizerElement } from "./types.js";

export const RECORDING_BLOCKING_STATUSES = new Set<LearnerRecordingStatus>([
  "countdown",
  "recording",
  "stopping",
  "analyzing",
]);

export function setLearnerRecordingState(payload: LearnerRecordingStatePayload): boolean {
  const ord = resolveFieldOrd(payload.fieldOrd);
  const controls = controlsForOrd(ord);
  if (!controls) return false;
  const status = payload.status || "idle";
  controls.dataset.learnerRecordingStatus = status;
  controls.dataset.learnerRecordingGeneration = payload.generation == null ? "" : String(payload.generation);
  controls.dataset.learnerRecordingMediaFilename = payload.mediaFilename || "";
  controls.dataset.learnerRecordingFailureMessage = payload.failureMessage || "";
  controls.dataset.learnerPlaybackStatus = playbackStatusForPayload(payload);
  if (payload.startCursorMs != null) {
    controls.dataset.learnerStartCursorMs = String(payload.startCursorMs);
  } else if (status === "idle") {
    controls.dataset.learnerStartCursorMs = "0";
  }

  const visualizer = visualizerForOrd(ord);
  if (visualizer) {
    visualizer.dataset.learnerRecordingStatus = status;
    visualizer.dataset.learnerPlaybackStatus = playbackStatusForPayload(payload);
    if (payload.targetDurationMs != null) {
      visualizer.dataset.targetDurationMs = String(payload.targetDurationMs);
    }
    if (payload.startCursorMs != null) {
      visualizer.dataset.learnerStartCursorMs = String(payload.startCursorMs);
    } else if (status === "idle") {
      visualizer.dataset.learnerStartCursorMs = "0";
    }
    if (payload.recordingDurationMs != null) {
      syncActiveRecordingTimeline(visualizer, payload.recordingDurationMs);
    }
    if (status === "recording") {
      startRecordingCursor(
        visualizer,
        learnerStartCursorMsForVisualizer(visualizer),
        payload.recordingDurationMs ?? 0,
      );
    } else {
      stopRecordingCursor(visualizer);
    }
    renderRecordingCountdownOverlay(visualizer, payload);
  }
  renderRecordingStatus(controls, payload);
  return true;
}

export function setLearnerVisualizer(ord: number, rawTrack: ProsodyPayload): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer || !rawTrack) return false;
  const track = normalizeTrack(rawTrack);
  renderLearnerVisualizerTrack(visualizer, offsetLearnerTrack(track, learnerStartCursorMsForVisualizer(visualizer)));
  return true;
}

export function resetLearnerRecordingState(ord: number, options: { clearOverlay?: boolean } = {}): boolean {
  const visualizer = visualizerForOrd(ord);
  if (visualizer?.__aqeRecordCountdownTimer) {
    window.clearTimeout(visualizer.__aqeRecordCountdownTimer);
    visualizer.__aqeRecordCountdownTimer = null;
  }
  if (visualizer) {
    stopRecordingCursor(visualizer);
    if (options.clearOverlay !== false) {
      clearLearnerVisualizerTrack(visualizer);
      delete visualizer.__aqeLearnerTrack;
      visualizer.dataset.learnerDurationMs = "0";
      visualizer.dataset.learnerStartCursorMs = "0";
    }
  }
  return setLearnerRecordingState({ fieldOrd: ord, status: "idle" });
}

export function recordingTargetReady(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  return targetDurationForRecording(visualizer) > 0;
}

export function targetDurationForRecording(visualizer: VisualizerElement | null): number {
  if (!visualizer || visualizer.dataset.hasTrack !== "true") return 0;
  return readVisualizerTargetDurationMs(visualizer);
}

export function recordingStartCursorMs(visualizer: VisualizerElement, targetDurationMs: number): number {
  return Math.max(0, Math.min(Number(visualizer.dataset.cursorMs || "0") || 0, targetDurationMs));
}

export function learnerStartCursorMsForVisualizer(visualizer: VisualizerElement): number {
  return Math.max(0, Number(visualizer.dataset.learnerStartCursorMs || "0") || 0);
}

export function offsetLearnerTrack(track: NormalizedProsodyTrack, startCursorMs: number): NormalizedProsodyTrack {
  if (startCursorMs <= 0) return track;
  return {
    ...track,
    durationMs: track.durationMs + startCursorMs,
    points: track.points.map((point): ProsodyPoint => [
      point[0] + startCursorMs,
      point[1],
      point[2],
      point[3],
    ]),
  };
}

export function learnerRecordingStatusForOrd(ord: number): LearnerRecordingStatus {
  return learnerRecordingStatusForControls(controlsForOrd(ord));
}

export function learnerRecordingStatusForControls(controls: HTMLElement | null): LearnerRecordingStatus {
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

export function playbackStatusForPayload(payload: LearnerRecordingStatePayload): LearnerPlaybackStatus {
  if (payload.playbackStatus === "playing" || payload.playbackStatus === "paused") {
    return payload.playbackStatus;
  }
  return "stopped";
}

export function learnerPlaybackStatusForControls(controls: HTMLElement | null): LearnerPlaybackStatus {
  const status = controls?.dataset.learnerPlaybackStatus;
  if (status === "playing" || status === "paused") return status;
  return "stopped";
}

export function resolveFieldOrd(fieldOrd: number | null | undefined): number {
  if (typeof fieldOrd === "number" && Number.isFinite(fieldOrd)) return fieldOrd;
  return Number(window.__aqeActiveField ?? 0);
}

export function setRecordingCursor(visualizer: VisualizerElement, ms: number, targetDurationMs: number): void {
  const clamped = Math.max(0, Math.min(Number(ms) || 0, targetDurationMs || 0));
  visualizer.dataset.cursorMs = String(Math.round(clamped));
  visualizer.dataset.progressMs = String(Math.round(clamped));
  ensurePlaybackCursorVisible(visualizer, clamped);
  renderCursor(visualizer, clamped, Number(visualizer.dataset.durationMs || targetDurationMs || "0"));
}

function startRecordingCursor(visualizer: VisualizerElement, startCursorMs: number, initialRecordingDurationMs: number): void {
  stopRecordingCursor(visualizer);
  const startMs = Math.max(0, Number(startCursorMs) || 0);
  const initialDurationMs = Math.max(0, Number(initialRecordingDurationMs) || 0);
  visualizer.__aqeRecordingStartedAt = performance.now() - initialDurationMs;
  const tick = (): void => {
    const startedAt = visualizer.__aqeRecordingStartedAt ?? performance.now();
    const recordingDurationMs = Math.max(0, performance.now() - startedAt);
    const durationMs = syncActiveRecordingTimeline(visualizer, recordingDurationMs);
    setRecordingCursor(visualizer, startMs + recordingDurationMs, durationMs);
    visualizer.__aqeRecordingCursorFrame = window.requestAnimationFrame(tick);
  };
  tick();
}

function stopRecordingCursor(visualizer: VisualizerElement): void {
  if (visualizer.__aqeRecordingCursorFrame) {
    window.cancelAnimationFrame(visualizer.__aqeRecordingCursorFrame);
  }
  visualizer.__aqeRecordingCursorFrame = null;
  visualizer.__aqeRecordingStartedAt = null;
}

function syncActiveRecordingTimeline(visualizer: VisualizerElement, recordingDurationMs: number): number {
  const effectiveLearnerDurationMs = activeRecordingLearnerDurationMs(visualizer, recordingDurationMs);
  const targetDurationMs = targetDurationForRecording(visualizer);
  visualizer.dataset.learnerDurationMs = String(Math.round(effectiveLearnerDurationMs));
  if (visualizer.dataset.hasTrack === "true" && visualizer.__aqeTrack) {
    renderProsodyTracks(visualizer);
  } else {
    visualizer.dataset.durationMs = String(Math.round(Math.max(targetDurationMs, effectiveLearnerDurationMs)));
  }
  return Number(visualizer.dataset.durationMs || "0") || 0;
}

function activeRecordingLearnerDurationMs(visualizer: VisualizerElement, recordingDurationMs: number): number {
  const startCursorMs = learnerStartCursorMsForVisualizer(visualizer);
  return Math.max(0, startCursorMs + (Number(recordingDurationMs) || 0));
}

function renderRecordingStatus(controls: HTMLElement, payload: LearnerRecordingStatePayload): void {
  const statusNode = controls.querySelector<HTMLElement>(".aqe-status");
  if (!statusNode) return;
  const status = payload.status || "idle";
  const message = recordingStatusText(payload);
  if (status === "idle" && !message) {
    statusNode.textContent = statusNode.dataset.stableMessage || "";
    statusNode.dataset.kind = statusNode.dataset.stableKind || "info";
    return;
  }
  statusNode.textContent = message;
  statusNode.dataset.kind = status === "failed"
    ? "error"
    : RECORDING_BLOCKING_STATUSES.has(status)
      ? "processing"
      : "info";
}

function recordingStatusText(payload: LearnerRecordingStatePayload): string {
  if (payload.status === "countdown") {
    return t("editor.recording.countdown", { seconds: payload.countdownSeconds ?? 0 });
  }
  if (payload.status === "recording") return t("editor.recording.recording");
  if (payload.status === "stopping") return t("editor.recording.stopping");
  if (payload.status === "analyzing") return t("editor.status.analyzing");
  if (payload.status === "ready") return t("editor.recording.ready");
  if (payload.status === "failed") return payload.failureMessage || t("editor.recording.failed");
  return "";
}

function renderRecordingCountdownOverlay(
  visualizer: VisualizerElement,
  payload: LearnerRecordingStatePayload,
): void {
  const seconds = countdownOverlaySeconds(payload);
  if (seconds == null) {
    clearGraphCountdownOverlay(visualizer);
    return;
  }
  const message = t("editor.recording.countdown", { seconds });
  renderGraphCountdownOverlay(visualizer, seconds, message);
}

function countdownOverlaySeconds(payload: LearnerRecordingStatePayload): number | null {
  if (payload.status !== "countdown") return null;
  const seconds = Number(payload.countdownSeconds);
  if (!Number.isFinite(seconds) || seconds <= 0) return null;
  return Math.round(seconds);
}
