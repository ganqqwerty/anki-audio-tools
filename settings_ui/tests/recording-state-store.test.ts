import { afterEach, describe, expect, it } from "vitest";

import {
  clearLearnerRecordingStateStore,
  emptyLearnerRecordingState,
  learnerPlaybackStatusForOrdState,
  learnerRecordingStatusForOrdState,
  learnerStartCursorMsForOrdState,
  readLearnerRecordingState,
  resetLearnerRecordingStateStore,
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
      fieldOrd: 0,
      generation: 5,
      mediaFilename: "voice.wav",
      playbackStatus: "playing",
      startCursorMs: 123.6,
      status: "ready",
    });

    expect(readLearnerRecordingState(0)).toEqual({
      failureMessage: "",
      generation: 5,
      mediaFilename: "voice.wav",
      playbackStatus: "playing",
      recordingStatus: "ready",
      startCursorMs: 124,
    });
    expect(readLearnerRecordingState(1)).toEqual(emptyLearnerRecordingState());
  });

  it("falls back invalid playback status to stopped", () => {
    writeLearnerRecordingState(0, {
      playbackStatus: "bad" as never,
      status: "ready",
    });

    expect(learnerPlaybackStatusForOrdState(0)).toBe("stopped");
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
