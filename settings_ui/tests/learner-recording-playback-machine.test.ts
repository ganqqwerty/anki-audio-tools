import { describe, expect, it } from "vitest";

import {
  initialLearnerRecordingPlaybackState,
  transitionLearnerRecordingPlayback,
  type LearnerRecordingPlaybackEffect,
  type LearnerRecordingPlaybackState,
} from "../src/editor-inline/learner-recording-playback-machine.js";

function effectTypes(effects: LearnerRecordingPlaybackEffect[]): LearnerRecordingPlaybackEffect["type"][] {
  return effects.map((effect) => effect.type);
}

function ready(overrides: Partial<Extract<LearnerRecordingPlaybackState, { kind: "ready" }>> = {}): LearnerRecordingPlaybackState {
  return {
    cursorMs: 0,
    durationMs: 1000,
    generation: 1,
    kind: "ready",
    mediaFilename: "learner.wav",
    startCursorMs: 0,
    ...overrides,
  };
}

function starting(): LearnerRecordingPlaybackState {
  return {
    cursorMs: 0,
    durationMs: 1000,
    generation: 1,
    kind: "starting",
    mediaFilename: "learner.wav",
    startCursorMs: 0,
  };
}

function playing(
  overrides: Partial<Extract<LearnerRecordingPlaybackState, { kind: "playing" }>> = {},
): LearnerRecordingPlaybackState {
  return {
    durationMs: 1000,
    generation: 1,
    kind: "playing",
    mediaFilename: "learner.wav",
    startedAtMs: 10,
    startCursorMs: 0,
    ...overrides,
  };
}

describe("learner recording playback machine", () => {
  it("stays unavailable when play is clicked before a ready recording exists", () => {
    const result = transitionLearnerRecordingPlayback(initialLearnerRecordingPlaybackState(), {
      type: "PlayButtonClicked",
    });

    expect(result.state).toEqual({ kind: "unavailable", reason: "not_ready" });
    expect(effectTypes(result.effects)).toEqual(["ShowPlaybackStatus", "LogPlaybackTelemetry"]);
  });

  it("moves to ready when Python publishes a ready recording with a media filename and duration", () => {
    const result = transitionLearnerRecordingPlayback(initialLearnerRecordingPlaybackState(), {
      generation: 7,
      mediaFilename: "voice recording.wav",
      recordingDurationMs: 1234.4,
      startCursorMs: 88.6,
      status: "ready",
      targetDurationMs: 2000,
      type: "RecordingStatePublished",
    });

    expect(result.state).toEqual({
      cursorMs: 0,
      durationMs: 1234,
      generation: 7,
      kind: "ready",
      mediaFilename: "voice recording.wav",
      startCursorMs: 89,
    });
    expect(result.effects).toContainEqual({
      mediaFilename: "voice recording.wav",
      type: "ConfigureLearnerAudioSource",
    });
    expect(result.effects).toContainEqual({
      status: "stopped",
      type: "PublishLearnerPlaybackState",
    });
  });

  it("preserves the learner start cursor offset from the recording payload", () => {
    const result = transitionLearnerRecordingPlayback(initialLearnerRecordingPlaybackState(), {
      generation: 1,
      mediaFilename: "learner.wav",
      startCursorMs: 321.6,
      status: "ready",
      targetDurationMs: 900,
      type: "RecordingStatePublished",
    });

    expect(result.state).toMatchObject({
      durationMs: 900,
      kind: "ready",
      startCursorMs: 322,
    });
  });

  it("moves ready to starting when play is clicked", () => {
    const result = transitionLearnerRecordingPlayback(ready({ cursorMs: 40 }), {
      type: "PlayButtonClicked",
    });

    expect(result.state).toMatchObject({ cursorMs: 40, kind: "starting" });
    expect(effectTypes(result.effects)).toEqual([
      "SeekLearnerAudio",
      "PlayLearnerAudio",
      "PublishLearnerPlaybackState",
    ]);
  });

  it("moves starting to playing when browser play resolves", () => {
    const result = transitionLearnerRecordingPlayback(starting(), {
      nowMs: 5000,
      type: "PlayResolved",
    });

    expect(result.state).toMatchObject({ kind: "playing", startedAtMs: 5000 });
    expect(effectTypes(result.effects)).toEqual([
      "PublishLearnerPlaybackState",
      "StartLearnerProgressFrame",
    ]);
  });

  it("moves starting to failed without bridge fallback when browser play rejects", () => {
    const result = transitionLearnerRecordingPlayback(starting(), {
      reason: "audio_play_rejected",
      type: "PlayRejected",
    });

    expect(result.state).toEqual({
      generation: 1,
      kind: "failed",
      mediaFilename: "learner.wav",
      reason: "audio_play_rejected",
    });
    expect(effectTypes(result.effects)).toEqual([
      "StopLearnerAudio",
      "ClearLearnerProgressFrame",
      "PublishLearnerPlaybackState",
      "ShowPlaybackStatus",
      "LogPlaybackTelemetry",
    ]);
  });

  it("pauses playing audio through a play button click", () => {
    const result = transitionLearnerRecordingPlayback(playing(), {
      type: "PlayButtonClicked",
    });

    expect(result.state).toMatchObject({ cursorMs: 0, kind: "paused" });
    expect(effectTypes(result.effects)).toEqual([
      "PauseLearnerAudio",
      "ClearLearnerProgressFrame",
      "PublishLearnerPlaybackState",
    ]);
  });

  it("resumes paused audio through a play button click", () => {
    const result = transitionLearnerRecordingPlayback({
      cursorMs: 350,
      durationMs: 1000,
      generation: 1,
      kind: "paused",
      mediaFilename: "learner.wav",
      startCursorMs: 20,
    }, {
      type: "PlayButtonClicked",
    });

    expect(result.state).toMatchObject({ cursorMs: 350, kind: "starting" });
    expect(result.effects).toContainEqual({ cursorMs: 350, type: "SeekLearnerAudio" });
    expect(effectTypes(result.effects)).toContain("PlayLearnerAudio");
  });

  it("returns to ready when audio ends", () => {
    const result = transitionLearnerRecordingPlayback(playing({ startCursorMs: 200 }), {
      type: "AudioEnded",
    });

    expect(result.state).toMatchObject({ cursorMs: 0, kind: "ready", startCursorMs: 200 });
    expect(effectTypes(result.effects)).toEqual([
      "ClearLearnerProgressFrame",
      "PublishLearnerPlaybackState",
      "RenderLearnerPlaybackCursor",
    ]);
  });

  it("stops current playback when a new recording generation is published", () => {
    const result = transitionLearnerRecordingPlayback(playing(), {
      generation: 2,
      mediaFilename: "new.wav",
      recordingDurationMs: 1500,
      status: "ready",
      type: "RecordingStatePublished",
    });

    expect(result.state).toMatchObject({
      durationMs: 1500,
      generation: 2,
      kind: "ready",
      mediaFilename: "new.wav",
    });
    expect(effectTypes(result.effects)).toEqual([
      "StopLearnerAudio",
      "ClearLearnerProgressFrame",
      "ConfigureLearnerAudioSource",
      "PublishLearnerPlaybackState",
    ]);
  });

  it("stops audio on runtime dispose", () => {
    const result = transitionLearnerRecordingPlayback(playing(), {
      type: "RuntimeDisposed",
    });

    expect(result.state).toEqual({ kind: "unavailable", reason: "media_missing" });
    expect(effectTypes(result.effects)).toEqual([
      "StopLearnerAudio",
      "ClearLearnerProgressFrame",
      "PublishLearnerPlaybackState",
    ]);
  });
});
