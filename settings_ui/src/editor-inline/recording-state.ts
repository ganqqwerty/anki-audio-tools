export type LearnerRecordingStatus =
  | "idle"
  | "countdown"
  | "recording"
  | "stopping"
  | "analyzing"
  | "ready"
  | "failed";

export type LearnerPlaybackStatus = "stopped" | "playing" | "paused";

export interface LearnerRecordingStatePayload {
  countdownSeconds?: number | null;
  failureMessage?: string | null;
  fieldOrd?: number | null;
  generation?: number | null;
  mediaFilename?: string | null;
  playbackStatus?: LearnerPlaybackStatus | null;
  recordingDurationMs?: number | null;
  startCursorMs?: number | null;
  status: LearnerRecordingStatus;
  targetDurationMs?: number | null;
}
