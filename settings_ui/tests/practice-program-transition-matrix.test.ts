import { describe, expect, it } from "vitest";

import { reduceChorusingProgram, startChorusingProgram } from "../src/editor-inline/practice/chorusing.js";
import type {
  ChorusingProgramState,
  OnceProgramState,
  PracticePlaybackPass,
  PracticeProgramState,
  RecordOnceProgramState,
  RecordingSpec,
  RepeatProgramState,
} from "../src/editor-inline/practice/model.js";
import { reduceOnceProgram, startOnceProgram } from "../src/editor-inline/practice/once.js";
import { reduceRecordOnceProgram, startRecordOnceProgram } from "../src/editor-inline/practice/record-once.js";
import { reducePracticeProgram } from "../src/editor-inline/practice/reducer.js";
import { reduceRepeatProgram, startRepeatProgram } from "../src/editor-inline/practice/repeat.js";
import type { EditorRuntimeId, FieldInstanceId, SourceInstanceId } from "../src/editor-inline/transport/identity.js";

const pass: PracticePlaybackPass = {
  endMs: 1000,
  loop: false,
  ord: 2,
  regionMode: "selection",
  resetCursorMs: 200,
  source: "user",
  startMs: 200,
};

const recordingSpec: RecordingSpec = {
  fieldOrd: 2,
  sourceIdentity: {
    fieldInstanceId: 2 as FieldInstanceId,
    runtimeId: 1 as EditorRuntimeId,
    sourceInstanceId: 3 as SourceInstanceId,
  },
  startCursorMs: 200,
};

describe("practice program transition matrix", () => {
  it.each(["cancelled", "completed", "failed"] as const)("Once ignores facts after %s", (phase) => {
    const state: OnceProgramState = { ...startOnceProgram(pass).state, phase };
    expect(reduceOnceProgram(state, { message: "late", type: "TransportFailed" })).toEqual({ commands: [], state });
  });

  it("Once covers pause, resume, transport resume, and irrelevant facts", () => {
    const playing = startOnceProgram(pass).state;
    const paused = reduceOnceProgram(playing, { type: "PauseRequested" }).state;
    expect(reduceOnceProgram(playing, { type: "PauseRequested" })).toEqual({
      commands: [], state: { ...playing, phase: "paused" },
    });
    expect(reduceOnceProgram(paused, { type: "ResumeRequested" })).toMatchObject({
      commands: [{ type: "Play" }], state: { phase: "playing" },
    });
    expect(reduceOnceProgram(playing, { type: "ResumeRequested" }).commands).toEqual([]);
    expect(reduceOnceProgram(paused, { type: "TransportResumed" }).state.phase).toBe("playing");
    expect(reduceOnceProgram(playing, { type: "TransportResumed" })).toEqual({ commands: [], state: playing });
    expect(reduceOnceProgram(playing, { type: "WaitElapsed" }).commands).toEqual([]);
  });

  it("Repeat normalizes inputs and ignores completed facts outside playing", () => {
    expect(startRepeatProgram(pass, -1.4, 0.2).state).toMatchObject({ count: 1, gapMs: 0 });
    expect(startRepeatProgram(pass, 1.6, null).state).toMatchObject({ count: null, gapMs: 2 });
    const waiting: RepeatProgramState = { ...startRepeatProgram(pass, 5, null).state, phase: "waiting" };
    expect(reduceRepeatProgram(waiting, { type: "PassCompleted" })).toEqual({ commands: [], state: waiting });
  });

  it.each(["cancelled", "completed", "failed"] as const)("Repeat ignores facts after %s", (phase) => {
    const state: RepeatProgramState = { ...startRepeatProgram(pass, 0, null).state, phase };
    expect(reduceRepeatProgram(state, { message: "late", type: "TransportFailed" })).toEqual({ commands: [], state });
  });

  it("Repeat covers pause and resume facts in every meaningful phase", () => {
    const playing = startRepeatProgram(pass, 0, null).state;
    const waiting: RepeatProgramState = { ...playing, phase: "waiting" };
    const paused = reduceRepeatProgram(playing, { type: "PauseRequested" }).state;
    expect(paused.phase).toBe("paused");
    expect(reduceRepeatProgram(waiting, { type: "PauseRequested" }).state.phase).toBe("paused");
    expect(reduceRepeatProgram(paused, { type: "PauseRequested" })).toEqual({ commands: [], state: paused });
    expect(reduceRepeatProgram(paused, { type: "ResumeRequested" })).toMatchObject({
      commands: [{ type: "Play" }], state: { phase: "playing" },
    });
    expect(reduceRepeatProgram(playing, { type: "ResumeRequested" }).commands).toEqual([]);
    expect(reduceRepeatProgram(paused, { type: "TransportResumed" }).state.phase).toBe("playing");
    expect(reduceRepeatProgram(playing, { type: "TransportResumed" })).toEqual({ commands: [], state: playing });
    expect(reduceRepeatProgram(playing, { type: "WaitElapsed" }).commands).toEqual([]);
  });

  it("Repeat fails on transport errors and ignores unrelated facts", () => {
    const state = startRepeatProgram(pass, 0, null).state;
    expect(reduceRepeatProgram(state, { message: "decode", type: "TransportFailed" })).toMatchObject({
      commands: [{ reason: { kind: "transport_failed", message: "decode" }, type: "Fail" }],
      state: { phase: "failed" },
    });
    expect(reduceRepeatProgram(state, { type: "RecorderStarted" }).commands).toEqual([]);
  });

  it.each([
    [[0, -1], "negative"],
    [[0, Number.POSITIVE_INFINITY], "non-finite"],
    [[0.1, 0.2], "duplicate after rounding"],
  ] as const)("Chorusing rejects markers: %s", (markers, _description) => {
    expect(startChorusingProgram(pass, { endMs: 1000, startMs: 200 }, markers, 0.2, -3)).toMatchObject({
      commands: [{ reason: { kind: "invalid_markers" }, type: "Fail" }],
      state: { gapMs: 0, markersMs: [], phase: "failed", repeatCount: 1 },
    });
  });

  it("Chorusing normalizes markers and covers gap scheduling", () => {
    let transition = startChorusingProgram(pass, { endMs: 1000, startMs: 200 }, [99.6, 0.2], 2.2, 99.6);
    expect(transition.state).toMatchObject({ gapMs: 100, markersMs: [0, 100], repeatCount: 2 });
    transition = reduceChorusingProgram(transition.state, { type: "PassCompleted" });
    expect(transition).toMatchObject({ commands: [{ purpose: "repeat_gap", type: "Wait" }], state: { phase: "waiting" } });
    expect(reduceChorusingProgram(transition.state, { type: "WaitElapsed" })).toMatchObject({
      commands: [{ type: "Play" }], state: { phase: "playing" },
    });
  });

  it.each(["cancelled", "completed", "failed"] as const)("Chorusing ignores facts after %s", (phase) => {
    const state: ChorusingProgramState = {
      ...startChorusingProgram(pass, { endMs: 1000, startMs: 200 }, [0, 100], 1, 0).state,
      phase,
    };
    expect(reduceChorusingProgram(state, { message: "late", type: "TransportFailed" })).toEqual({ commands: [], state });
  });

  it("Chorusing covers no-op, pause, resume, marker, completion, and failure paths", () => {
    const playing = startChorusingProgram(pass, { endMs: 1000, startMs: 0 }, [0, 100], 1, 0).state;
    const waiting: ChorusingProgramState = { ...playing, phase: "waiting" };
    const paused = reduceChorusingProgram(playing, { type: "PauseRequested" }).state;
    expect(reduceChorusingProgram(waiting, { type: "PassCompleted" }).commands).toEqual([]);
    expect(reduceChorusingProgram(waiting, { type: "PauseRequested" }).state.phase).toBe("paused");
    expect(reduceChorusingProgram(paused, { type: "PauseRequested" })).toEqual({ commands: [], state: paused });
    expect(reduceChorusingProgram(paused, { type: "ResumeRequested" }).commands).toMatchObject([{ type: "Play" }]);
    expect(reduceChorusingProgram(playing, { type: "ResumeRequested" }).commands).toEqual([]);
    expect(reduceChorusingProgram(paused, { type: "TransportResumed" }).state.phase).toBe("playing");
    expect(reduceChorusingProgram(playing, { type: "TransportResumed" })).toEqual({ commands: [], state: playing });
    expect(reduceChorusingProgram(playing, { type: "WaitElapsed" }).commands).toEqual([]);
    expect(reduceChorusingProgram(playing, { markersMs: [150, 25], type: "MarkersUpdated" }).state.markersMs).toEqual([25, 150]);
    expect(reduceChorusingProgram(playing, { type: "Skip" })).toMatchObject({
      commands: [{ type: "Complete" }], state: { phase: "completed" },
    });
    expect(reduceChorusingProgram(playing, { message: "decode", type: "TransportFailed" })).toMatchObject({
      commands: [{ reason: { kind: "transport_failed" }, type: "Fail" }], state: { phase: "failed" },
    });
    expect(reduceChorusingProgram(playing, { type: "RecorderStarted" }).commands).toEqual([]);
  });

  it.each(["cancelled", "completed", "failed"] as const)("RecordOnce ignores facts after %s", (phase) => {
    const state: RecordOnceProgramState = { ...startRecordOnceProgram(0, recordingSpec).state, phase };
    expect(reduceRecordOnceProgram(state, { message: "late", type: "RecorderFailed" })).toEqual({ commands: [], state });
  });

  it("RecordOnce normalizes countdown and covers recorder lifecycle paths", () => {
    expect(startRecordOnceProgram(-1.4, recordingSpec).state.countdownMs).toBe(0);
    expect(startRecordOnceProgram(1.6, recordingSpec).state.countdownMs).toBe(2);
    const stopping = startRecordOnceProgram(0, recordingSpec).state;
    const starting = reduceRecordOnceProgram(stopping, { type: "TransportStopped" }).state;
    const recording = reduceRecordOnceProgram(starting, { type: "RecorderStarted" }).state;
    expect(reduceRecordOnceProgram(starting, { type: "TransportStopped" }).commands).toEqual([]);
    expect(reduceRecordOnceProgram(stopping, { type: "RecorderStarted" })).toEqual({ commands: [], state: stopping });
    expect(recording.phase).toBe("recording");
    expect(reduceRecordOnceProgram(starting, { type: "RecorderCompleted" })).toEqual({
      commands: [{ type: "Complete" }], state: { ...starting, phase: "completed" },
    });
    expect(reduceRecordOnceProgram(recording, { type: "RecorderCompleted" })).toEqual({
      commands: [{ type: "Complete" }], state: { ...recording, phase: "completed" },
    });
    expect(reduceRecordOnceProgram(stopping, { type: "RecorderCompleted" }).commands).toEqual([]);
    expect(reduceRecordOnceProgram(stopping, { message: "permission", type: "RecorderFailed" })).toMatchObject({
      commands: [{ reason: { kind: "recorder_failed" }, type: "Fail" }], state: { phase: "failed" },
    });
    expect(reduceRecordOnceProgram(stopping, { message: "stop", type: "TransportFailed" })).toMatchObject({
      commands: [{ reason: { kind: "transport_failed" }, type: "Fail" }], state: { phase: "failed" },
    });
    expect(reduceRecordOnceProgram(stopping, { type: "PassCompleted" }).commands).toEqual([]);
  });

  it("routes every practice kind through its distinct reducer", () => {
    const once = startOnceProgram(pass).state;
    expect(reducePracticeProgram(once, { type: "PassCompleted" }))
      .toEqual(reduceOnceProgram(once, { type: "PassCompleted" }));

    const repeat = startRepeatProgram(pass, 40, 3).state;
    expect(reducePracticeProgram(repeat, { type: "PassCompleted" }))
      .toEqual(reduceRepeatProgram(repeat, { type: "PassCompleted" }));

    const chorusing = startChorusingProgram(
      pass,
      { endMs: 1000, startMs: 200 },
      [0, 100],
      1,
      0,
    ).state;
    expect(reducePracticeProgram(chorusing, { type: "Skip" }))
      .toEqual(reduceChorusingProgram(chorusing, { type: "Skip" }));

    const recordOnce = startRecordOnceProgram(0, recordingSpec).state;
    expect(reducePracticeProgram(recordOnce, { type: "TransportStopped" }))
      .toEqual(reduceRecordOnceProgram(recordOnce, { type: "TransportStopped" }));
  });

  it("fails closed for an unknown practice kind", () => {
    const invalid = { kind: "future_program", phase: "playing" } as unknown as PracticeProgramState;
    expect(() => reducePracticeProgram(invalid, { type: "Cancelled" })).toThrow("Unhandled practice program");
  });
});
