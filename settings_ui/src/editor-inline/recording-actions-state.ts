import type { ProsodyPayload } from "../lib/generated/contracts.js";
import { t } from "../lib/i18n.js";
import { clearGraphCountdownOverlay, renderGraphCountdownOverlay } from "./graph-countdown-overlay.js";
import { controlsForOrd, visualizerForOrd } from "./dom-selectors.js";
import { ensurePlaybackCursorVisible } from "./viewport-actions.js";
import { clearLearnerVisualizerTrack, renderCursor, renderLearnerVisualizerTrack, renderProsodyTracks } from "./visualizer-renderer.js";
import { readVisualizerTargetDurationMs } from "./visualizer-state.js";
import type { LearnerPlaybackStatus, LearnerRecordingStatePayload, LearnerRecordingStatus } from "./recording-state.js";
import { normalizeTrack, type NormalizedProsodyTrack, type ProsodyPoint, type VisualizerElement } from "./types.js";
import { readFieldState, updateFieldState } from "./field-state-store.js";
import {
  learnerPlaybackStatusForOrdState,
  learnerRecordingStatusForOrdState,
  learnerStartCursorMsForOrdState,
  resetLearnerRecordingStateStore,
  writeLearnerRecordingState,
  type LearnerRecordingFieldState,
} from "./recording-state-store.js";
import {
  fieldOrdForVisualizer,
  setLearnerDurationMsForVisualizer,
  setTargetDurationMsForVisualizer,
} from "./visualizer-runtime-state.js";
import { stableStatusState } from "./editor-control-state.js";
import { isUserFacingError } from "../lib/user-facing-error.js";

interface RecordingCursorProjection {
  readonly startedAt: number;
  frame: number | null;
}

class RecordingProjectionRuntime {
  readonly cursors = new Map<VisualizerElement, RecordingCursorProjection>();

  dispose(): void {
    for (const cursor of this.cursors.values()) {
      if (cursor.frame !== null) window.cancelAnimationFrame(cursor.frame);
    }
    this.cursors.clear();
  }
}

let activeProjectionRuntime: RecordingProjectionRuntime | null = null;

function projectionRuntime(): RecordingProjectionRuntime {
  activeProjectionRuntime ??= new RecordingProjectionRuntime();
  return activeProjectionRuntime;
}

export const RECORDING_BLOCKING_STATUSES = new Set<LearnerRecordingStatus>([
  "countdown",
  "starting",
  "recording",
  "stopping",
  "finalizing",
  "analyzing",
]);

export function setLearnerRecordingState(payload: LearnerRecordingStatePayload): boolean {
  const ord = resolveFieldOrd(payload.fieldOrd);
  const controls = controlsForOrd(ord);
  if (!controls) return false;
  const state = writeLearnerRecordingState(ord, payload);
  projectLearnerRecordingControls(controls, state);

  const visualizer = visualizerForOrd(ord);
  if (visualizer) {
    projectLearnerRecordingVisualizer(visualizer, state);
    if (payload.targetDurationMs != null) {
      setTargetDurationMsForVisualizer(visualizer, payload.targetDurationMs);
    }
    if (payload.recordingDurationMs != null) {
      syncActiveRecordingTimeline(visualizer, payload.recordingDurationMs);
    }
    if (state.recordingStatus === "recording") {
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
  resetLearnerRecordingStateStore(ord);
  const visualizer = visualizerForOrd(ord);
  if (visualizer) {
    stopRecordingCursor(visualizer);
    if (options.clearOverlay !== false) {
      clearLearnerVisualizerTrack(visualizer);
      delete visualizer.__aqeLearnerTrack;
      setLearnerDurationMsForVisualizer(visualizer, 0);
    }
  }
  return setLearnerRecordingState({ fieldOrd: ord, status: "idle" });
}

export function recordingTargetReady(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  return targetDurationForRecording(visualizer) > 0;
}

export function targetDurationForRecording(visualizer: VisualizerElement | null): number {
  if (!visualizer || !readFieldState(Number(visualizer.dataset.aqeFieldOrd || "0")).graph.hasTrack) return 0;
  return readVisualizerTargetDurationMs(visualizer);
}

export function recordingStartCursorMs(visualizer: VisualizerElement, targetDurationMs: number): number {
  return Math.max(0, Math.min(readFieldState(Number(visualizer.dataset.aqeFieldOrd || "0")).cursor.ms, targetDurationMs));
}

export function learnerStartCursorMsForVisualizer(visualizer: VisualizerElement): number {
  return learnerStartCursorMsForOrdState(fieldOrdForVisualizer(visualizer));
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
  if (!controls) return "idle";
  return learnerRecordingStatusForOrdState(Number(controls.dataset.aqeFieldOrd || "0"));
}

export function learnerPlaybackStatusForControls(controls: HTMLElement | null): LearnerPlaybackStatus {
  if (!controls) return "stopped";
  return learnerPlaybackStatusForOrdState(Number(controls.dataset.aqeFieldOrd || "0"));
}

export function resolveFieldOrd(fieldOrd: number | null | undefined): number {
  if (typeof fieldOrd === "number" && Number.isFinite(fieldOrd)) return fieldOrd;
  return Number(window.__aqeActiveField ?? 0);
}

export function setRecordingCursor(visualizer: VisualizerElement, ms: number, targetDurationMs: number): void {
  const clamped = Math.max(0, Math.min(Number(ms) || 0, targetDurationMs || 0));
  const state = updateFieldState(Number(visualizer.dataset.aqeFieldOrd || "0"), (fieldState) => ({
    ...fieldState,
    cursor: {
      ...fieldState.cursor,
      ms: Math.round(clamped),
      progressMs: Math.round(clamped),
    },
  }));
  ensurePlaybackCursorVisible(visualizer, clamped);
  renderCursor(visualizer, clamped, state.graph.durationMs || targetDurationMs);
}

function startRecordingCursor(visualizer: VisualizerElement, startCursorMs: number, initialRecordingDurationMs: number): void {
  stopRecordingCursor(visualizer);
  const startMs = Math.max(0, Number(startCursorMs) || 0);
  const initialDurationMs = Math.max(0, Number(initialRecordingDurationMs) || 0);
  const cursor: RecordingCursorProjection = {
    frame: null,
    startedAt: performance.now() - initialDurationMs,
  };
  projectionRuntime().cursors.set(visualizer, cursor);
  const tick = (): void => {
    if (projectionRuntime().cursors.get(visualizer) !== cursor) return;
    const recordingDurationMs = Math.max(0, performance.now() - cursor.startedAt);
    const durationMs = syncActiveRecordingTimeline(visualizer, recordingDurationMs);
    setRecordingCursor(visualizer, startMs + recordingDurationMs, durationMs);
    cursor.frame = window.requestAnimationFrame(tick);
  };
  tick();
}

function stopRecordingCursor(visualizer: VisualizerElement): void {
  const cursor = projectionRuntime().cursors.get(visualizer);
  if (cursor?.frame !== null && cursor?.frame !== undefined) window.cancelAnimationFrame(cursor.frame);
  projectionRuntime().cursors.delete(visualizer);
}

export function disposeRecordingProjections(): void {
  activeProjectionRuntime?.dispose();
  activeProjectionRuntime = null;
}

function syncActiveRecordingTimeline(visualizer: VisualizerElement, recordingDurationMs: number): number {
  const effectiveLearnerDurationMs = activeRecordingLearnerDurationMs(visualizer, recordingDurationMs);
  const targetDurationMs = targetDurationForRecording(visualizer);
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  setLearnerDurationMsForVisualizer(visualizer, effectiveLearnerDurationMs);
  if (readFieldState(ord).graph.hasTrack && visualizer.__aqeTrack) {
    renderProsodyTracks(visualizer);
    return readFieldState(ord).graph.durationMs;
  } else {
    const durationMs = Math.round(Math.max(targetDurationMs, effectiveLearnerDurationMs));
    const state = updateFieldState(ord, (fieldState) => ({
      ...fieldState,
      graph: { ...fieldState.graph, durationMs },
    }));
    return state.graph.durationMs;
  }
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
    const stable = stableStatusState(Number(controls.dataset.aqeFieldOrd || "0"));
    statusNode.textContent = isUserFacingError(stable.message) ? stable.message.message : stable.message;
    statusNode.dataset.kind = stable.kind || "info";
    return;
  }
  statusNode.textContent = message;
  statusNode.dataset.kind = status === "failed"
    ? "error"
    : RECORDING_BLOCKING_STATUSES.has(status)
      ? "processing"
      : "info";
}

function projectLearnerRecordingControls(
  controls: HTMLElement,
  state: LearnerRecordingFieldState,
): void {
  controls.dataset.learnerRecordingStatus = state.recordingStatus;
  controls.dataset.learnerRecordingAttemptId = state.attemptId == null ? "" : String(state.attemptId);
  controls.dataset.learnerRecordingMediaFilename = state.mediaFilename;
  controls.dataset.learnerRecordingFailureMessage = state.failureMessage;
  controls.dataset.learnerPlaybackStatus = state.playbackStatus;
  controls.dataset.learnerStartCursorMs = String(state.startCursorMs);
}

function projectLearnerRecordingVisualizer(
  visualizer: VisualizerElement,
  state: LearnerRecordingFieldState,
): void {
  visualizer.dataset.learnerRecordingStatus = state.recordingStatus;
  visualizer.dataset.learnerPlaybackStatus = state.playbackStatus;
  visualizer.dataset.learnerStartCursorMs = String(state.startCursorMs);
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
