import { afterEach, describe, expect, it } from "vitest";

import {
  clearLearnerRecordingStateStore,
  emptyLearnerRecordingState,
  learnerPlaybackStatusForOrdState,
  learnerRecordingStatusForOrdState,
  learnerStartCursorMsForOrdState,
  readLearnerRecordingState,
  resetLearnerRecordingStateStore,
  writeLearnerPlaybackStatus,
  writeLearnerRecordingState,
} from "../src/editor-inline/recording-state-store.js";

describe("recording state store", () => {
  afterEach(() => {
    clearLearnerRecordingStateStore();
  });

  it("returns an idle default for unknown fields", () => {
    expect(readLearnerRecordingState(99)).toEqual(emptyLearnerRecordingState());
  });

  it("normalizes payloads and stores per-field recording state", () => {
    writeLearnerRecordingState(0, {
      attemptId: 5,
      fieldOrd: 0,
      mediaFilename: "voice.wav",
      recordingDurationMs: 543.2,
      startCursorMs: 123.6,
      status: "ready",
      targetDurationMs: 1000.4,
    });
    writeLearnerPlaybackStatus(0, "playing");

    expect(readLearnerRecordingState(0)).toEqual({
      failureMessage: "",
      attemptId: 5,
      mediaFilename: "voice.wav",
      playbackStatus: "playing",
      recordingDurationMs: 543,
      recordingStatus: "ready",
      startCursorMs: 124,
      targetDurationMs: 1000,
    });
    expect(readLearnerRecordingState(1)).toEqual(emptyLearnerRecordingState());
  });

  it("resets playback status when recording state is not ready", () => {
    writeLearnerRecordingState(0, {
      mediaFilename: "voice.wav",
      recordingDurationMs: 500,
      status: "ready",
      targetDurationMs: 1000,
    });
    writeLearnerPlaybackStatus(0, "playing");
    writeLearnerRecordingState(0, {
      status: "failed",
    });

    expect(readLearnerRecordingState(0)).toMatchObject({
      playbackStatus: "stopped",
      recordingDurationMs: 500,
      recordingStatus: "failed",
      targetDurationMs: 1000,
    });
  });

  it("keeps the previous start cursor when payload omits it except on idle", () => {
    writeLearnerRecordingState(0, {
      startCursorMs: 400,
      status: "recording",
    });
    writeLearnerRecordingState(0, {
      status: "ready",
    });

    expect(learnerStartCursorMsForOrdState(0)).toBe(400);

    writeLearnerRecordingState(0, {
      status: "idle",
    });

    expect(learnerStartCursorMsForOrdState(0)).toBe(0);
  });

  it("stores failed state details and exposes status helpers", () => {
    writeLearnerRecordingState(2, {
      failureMessage: "Recorder failed.",
      status: "failed",
    });

    expect(learnerRecordingStatusForOrdState(2)).toBe("failed");
    expect(readLearnerRecordingState(2).failureMessage).toBe("Recorder failed.");
  });

  it("resets one field without touching others", () => {
    writeLearnerRecordingState(0, { status: "ready", mediaFilename: "a.wav" });
    writeLearnerRecordingState(1, { status: "recording" });

    resetLearnerRecordingStateStore(0);

    expect(readLearnerRecordingState(0)).toEqual(emptyLearnerRecordingState());
    expect(learnerRecordingStatusForOrdState(1)).toBe("recording");
  });
});
