export type LearnerRecordingStatus =
  | "idle"
  | "countdown"
  | "recording"
  | "stopping"
  | "analyzing"
  | "ready"
  | "failed";

export interface LearnerRecordingStatePayload {
  countdownSeconds?: number | null;
  failureMessage?: string | null;
  fieldOrd?: number | null;
  generation?: number | null;
  mediaFilename?: string | null;
  recordingDurationMs?: number | null;
  status: LearnerRecordingStatus;
  targetDurationMs?: number | null;
}
