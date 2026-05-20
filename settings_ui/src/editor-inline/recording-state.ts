export type LearnerRecordingStatus =
  | "idle"
  | "countdown"
  | "recording"
  | "stopping"
  | "analyzing"
  | "ready"
  | "failed";

export interface LearnerRecordingStatePayload {
  failureMessage?: string | null;
  fieldOrd?: number | null;
  generation?: number | null;
  mediaFilename?: string | null;
  status: LearnerRecordingStatus;
  targetDurationMs?: number | null;
}
