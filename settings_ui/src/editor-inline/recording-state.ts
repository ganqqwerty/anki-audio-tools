import { Status, type RecorderSnapshot } from "../lib/generated/contracts.js";

export type LearnerRecordingStatus = `${Status}`;

export type LearnerPlaybackStatus = "stopped" | "playing" | "paused";

export interface LearnerRecordingStatePayload extends Partial<Omit<RecorderSnapshot, "status">> {
  countdownSeconds?: number | null;
  status: LearnerRecordingStatus;
}
