import type {
  LearnerPlaybackStatus,
  LearnerRecordingStatePayload,
  LearnerRecordingStatus,
} from "./recording-state.js";

export interface LearnerRecordingFieldState {
  attemptId: number | null;
  failureMessage: string;
  mediaFilename: string;
  playbackStatus: LearnerPlaybackStatus;
  recordingDurationMs: number;
  recordingStatus: LearnerRecordingStatus;
  startCursorMs: number;
  targetDurationMs: number;
}

const recordingStates: Map<number, LearnerRecordingFieldState> = new Map();

export function emptyLearnerRecordingState(): LearnerRecordingFieldState {
  return {
    attemptId: null,
    failureMessage: "",
    mediaFilename: "",
    playbackStatus: "stopped",
    recordingDurationMs: 0,
    recordingStatus: "idle",
    startCursorMs: 0,
    targetDurationMs: 0,
  };
}

function normalizeStartCursorMs(value: unknown, fallback: number): number {
  if (typeof value !== "number" || !Number.isFinite(value)) return fallback;
  return Math.max(0, Math.round(value));
}

function normalizeDurationMs(value: unknown, fallback: number): number {
  if (typeof value !== "number" || !Number.isFinite(value)) return fallback;
  return Math.max(0, Math.round(value));
}

export function readLearnerRecordingState(ord: number): LearnerRecordingFieldState {
  return recordingStates.get(ord) ?? emptyLearnerRecordingState();
}

export function writeLearnerRecordingState(
  ord: number,
  payload: LearnerRecordingStatePayload,
): LearnerRecordingFieldState {
  const previous = readLearnerRecordingState(ord);
  const status = payload.status || "idle";
  const next: LearnerRecordingFieldState = {
    attemptId: payload.attemptId == null ? null : payload.attemptId,
    failureMessage: payload.failureMessage || "",
    mediaFilename: payload.mediaFilename || "",
    playbackStatus: status === "ready" ? previous.playbackStatus : "stopped",
    recordingDurationMs: status === "idle" && payload.recordingDurationMs == null
      ? 0
      : normalizeDurationMs(payload.recordingDurationMs, previous.recordingDurationMs),
    recordingStatus: status,
    startCursorMs: status === "idle" && payload.startCursorMs == null
      ? 0
      : normalizeStartCursorMs(payload.startCursorMs, previous.startCursorMs),
    targetDurationMs: status === "idle" && payload.targetDurationMs == null
      ? 0
      : normalizeDurationMs(payload.targetDurationMs, previous.targetDurationMs),
  };
  recordingStates.set(ord, next);
  return next;
}

export function writeLearnerPlaybackStatus(
  ord: number,
  playbackStatus: LearnerPlaybackStatus,
): LearnerRecordingFieldState {
  const previous = readLearnerRecordingState(ord);
  const next = { ...previous, playbackStatus };
  recordingStates.set(ord, next);
  return next;
}

export function resetLearnerRecordingStateStore(ord: number): LearnerRecordingFieldState {
  const next = emptyLearnerRecordingState();
  recordingStates.set(ord, next);
  return next;
}

export function clearLearnerRecordingStateStore(): void {
  recordingStates.clear();
}

export function learnerRecordingStatusForOrdState(ord: number): LearnerRecordingStatus {
  return readLearnerRecordingState(ord).recordingStatus;
}

export function learnerPlaybackStatusForOrdState(ord: number): LearnerPlaybackStatus {
  return readLearnerRecordingState(ord).playbackStatus;
}

export function learnerStartCursorMsForOrdState(ord: number): number {
  return readLearnerRecordingState(ord).startCursorMs;
}
