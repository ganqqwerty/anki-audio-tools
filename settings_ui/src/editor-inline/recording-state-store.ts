import type {
  LearnerPlaybackStatus,
  LearnerRecordingStatePayload,
  LearnerRecordingStatus,
} from "./recording-state.js";

export interface LearnerRecordingFieldState {
  failureMessage: string;
  generation: number | null;
  mediaFilename: string;
  playbackStatus: LearnerPlaybackStatus;
  recordingStatus: LearnerRecordingStatus;
  startCursorMs: number;
}

const recordingStates: Map<number, LearnerRecordingFieldState> = new Map();

export function emptyLearnerRecordingState(): LearnerRecordingFieldState {
  return {
    failureMessage: "",
    generation: null,
    mediaFilename: "",
    playbackStatus: "stopped",
    recordingStatus: "idle",
    startCursorMs: 0,
  };
}

function normalizePlaybackStatus(value: LearnerRecordingStatePayload["playbackStatus"]): LearnerPlaybackStatus {
  return value === "playing" || value === "paused" ? value : "stopped";
}

function normalizeStartCursorMs(value: unknown, fallback: number): number {
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
    failureMessage: payload.failureMessage || "",
    generation: payload.generation == null ? null : payload.generation,
    mediaFilename: payload.mediaFilename || "",
    playbackStatus: normalizePlaybackStatus(payload.playbackStatus),
    recordingStatus: status,
    startCursorMs: status === "idle" && payload.startCursorMs == null
      ? 0
      : normalizeStartCursorMs(payload.startCursorMs, previous.startCursorMs),
  };
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
