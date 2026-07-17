import { describe, expect, it, vi } from "vitest";

import { reduceChorusingProgram, startChorusingProgram } from "../src/editor-inline/practice/chorusing.js";
import type {
  PracticeCommand,
  PracticeFact,
  PracticePlaybackPass,
  ProgramRunId,
  RecordingSpec,
} from "../src/editor-inline/practice/model.js";
import { reduceOnceProgram, startOnceProgram } from "../src/editor-inline/practice/once.js";
import { reduceRecordOnceProgram, startRecordOnceProgram } from "../src/editor-inline/practice/record-once.js";
import { reduceRepeatProgram, startRepeatProgram } from "../src/editor-inline/practice/repeat.js";
import { PracticeRuntime, type PracticeRuntimePorts } from "../src/editor-inline/practice/runtime.js";
import type {
  EditorRuntimeId,
  FieldInstanceId,
  SourceInstanceId,
} from "../src/editor-inline/transport/identity.js";

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

describe("pure practice programs", () => {
  it("creates exact initial commands and states for every program", () => {
    expect(startOnceProgram(pass)).toEqual({
      commands: [{ pass, type: "Play" }],
      state: { kind: "once", pass, phase: "playing" },
    });
    expect(startRepeatProgram(pass, 12.6, 2.2)).toEqual({
      commands: [{ pass, type: "Play" }],
      state: {
        completedPasses: 0,
        count: 2,
        finishAfterCurrentPass: false,
        gapMs: 13,
        kind: "repeat",
        pass,
        phase: "playing",
      },
    });
    expect(startChorusingProgram(pass, { endMs: 1000, startMs: 200 }, [0, 100], 2, 13)).toEqual({
      commands: [{ pass, type: "Play" }],
      state: {
        completedPasses: 0,
        finishAfterCurrentPass: false,
        gapMs: 13,
        kind: "chorusing",
        markersMs: [0, 100],
        pass,
        phase: "playing",
        repeatCount: 2,
        selection: { endMs: 1000, startMs: 200 },
      },
    });
    expect(startRecordOnceProgram(13, recordingSpec)).toEqual({
      commands: [{ fieldOrd: 2, type: "StopTransport" }],
      state: {
        countdownMs: 13,
        kind: "record_once",
        phase: "stopping_transport",
        spec: recordingSpec,
      },
    });
  });

  it.each([
    [{ type: "PassCompleted" } as const, "completed", [{ type: "Complete" }]],
    [{ type: "Stopped" } as const, "cancelled", [{ type: "Complete" }]],
    [{ type: "SourceChanged" } as const, "cancelled", [{ type: "Complete" }]],
    [{ message: "decode", type: "TransportFailed" } as const, "failed", [
      { reason: { kind: "transport_failed", message: "decode" }, type: "Fail" },
    ]],
  ])("Once handles %o", (fact, phase, commands) => {
    const started = startOnceProgram(pass);
    expect(started.commands).toEqual([{ pass, type: "Play" }]);
    const result = reduceOnceProgram(started.state, fact);
    expect(result.state.phase).toBe(phase);
    expect(result.commands).toEqual(commands);
  });

  it("Repeat counts passes with zero and non-zero gaps", () => {
    const zeroGap = startRepeatProgram(pass, 0, 2);
    const secondPass = reduceRepeatProgram(zeroGap.state, { type: "PassCompleted" });
    expect(secondPass).toMatchObject({
      commands: [{ type: "Play" }],
      state: { completedPasses: 1, phase: "playing" },
    });
    expect(reduceRepeatProgram(secondPass.state, { type: "PassCompleted" })).toMatchObject({
      commands: [{ type: "Complete" }],
      state: { completedPasses: 2, phase: "completed" },
    });

    const gap = reduceRepeatProgram(startRepeatProgram(pass, 750, null).state, { type: "PassCompleted" });
    expect(gap).toMatchObject({
      commands: [{ durationMs: 750, purpose: "repeat_gap", type: "Wait" }],
      state: { phase: "waiting" },
    });
    expect(reduceRepeatProgram(gap.state, { type: "WaitElapsed" })).toMatchObject({
      commands: [{ type: "Play" }],
      state: { phase: "playing" },
    });
  });

  it("Repeat off lets the active pass finish but cancels a pending gap", () => {
    const playing = startRepeatProgram(pass, 500, null).state;
    const disarmed = reduceRepeatProgram(playing, { type: "RepeatDisabled" });
    expect(disarmed).toMatchObject({
      commands: [],
      state: { finishAfterCurrentPass: true, phase: "playing" },
    });
    expect(reduceRepeatProgram(disarmed.state, { type: "PassCompleted" })).toMatchObject({
      commands: [{ type: "Complete" }],
      state: { completedPasses: 1, phase: "completed" },
    });

    const waiting = reduceRepeatProgram(playing, { type: "PassCompleted" }).state;
    expect(reduceRepeatProgram(waiting, { type: "RepeatDisabled" })).toMatchObject({
      commands: [{ type: "Complete" }],
      state: { phase: "completed" },
    });
  });

  it.each([
    [{ type: "PauseRequested" } as const, "paused", []],
    [{ type: "Stopped" } as const, "cancelled", [{ type: "Complete" }]],
    [{ type: "SelectionChanged" } as const, "cancelled", [{ type: "Complete" }]],
  ])("Repeat handles %o during a wait", (fact, phase, commands) => {
    const waiting = reduceRepeatProgram(
      startRepeatProgram(pass, 500, null).state,
      { type: "PassCompleted" },
    ).state;
    expect(reduceRepeatProgram(waiting, fact)).toMatchObject({ commands, state: { phase } });
  });

  it("chorusing repeats each suffix, projects the next suffix, and completes", () => {
    let transition = startChorusingProgram(pass, { startMs: 200, endMs: 1000 }, [0, 100, 200], 2, 0);
    transition = reduceChorusingProgram(transition.state, { type: "PassCompleted" });
    expect(transition).toMatchObject({ commands: [{ type: "Play" }], state: { completedPasses: 1 } });
    transition = reduceChorusingProgram(transition.state, { type: "PassCompleted" });
    expect(transition.commands).toEqual([
      { fieldOrd: 2, range: { endMs: 1000, startMs: 100 }, type: "UpdateSelectionProjection" },
      { pass: { ...pass, resetCursorMs: 100, startMs: 100 }, type: "Play" },
    ]);
    transition = reduceChorusingProgram(transition.state, { type: "PassCompleted" });
    transition = reduceChorusingProgram(transition.state, { type: "PassCompleted" });
    expect(transition.state.selection.startMs).toBe(0);
    transition = reduceChorusingProgram(transition.state, { type: "PassCompleted" });
    transition = reduceChorusingProgram(transition.state, { type: "PassCompleted" });
    expect(transition).toMatchObject({ commands: [{ type: "Complete" }], state: { phase: "completed" } });
  });

  it("Repeat off lets the active chorusing pass finish without advancing the suffix", () => {
    const playing = startChorusingProgram(
      pass,
      { startMs: 200, endMs: 1000 },
      [0, 100, 200],
      2,
      500,
    ).state;
    const disarmed = reduceChorusingProgram(playing, { type: "RepeatDisabled" });
    expect(disarmed.state.finishAfterCurrentPass).toBe(true);
    expect(reduceChorusingProgram(disarmed.state, { type: "PassCompleted" })).toMatchObject({
      commands: [{ type: "Complete" }],
      state: { completedPasses: 1, phase: "completed", selection: { startMs: 200 } },
    });
  });

  it("chorusing rejects invalid marker updates and supports skip and stop", () => {
    const started = startChorusingProgram(pass, { startMs: 200, endMs: 1000 }, [0, 100, 200], 3, 0);
    expect(reduceChorusingProgram(started.state, { type: "Skip" })).toMatchObject({
      commands: [{ type: "UpdateSelectionProjection" }, { type: "Play" }],
      state: { selection: { startMs: 100 } },
    });
    expect(reduceChorusingProgram(started.state, { markersMs: [100, Number.NaN], type: "MarkersUpdated" })).toMatchObject({
      commands: [{ reason: { kind: "invalid_markers" }, type: "Fail" }],
      state: { phase: "failed" },
    });
    expect(reduceChorusingProgram(started.state, { type: "Stopped" })).toMatchObject({
      commands: [{ type: "Complete" }],
      state: { phase: "cancelled" },
    });
  });

  it.each([0, 3000])("RecordOnce with %d ms countdown stops transport then starts exactly once", (countdownMs) => {
    let transition = startRecordOnceProgram(countdownMs, recordingSpec);
    expect(transition.commands).toEqual([{ fieldOrd: 2, type: "StopTransport" }]);
    transition = reduceRecordOnceProgram(transition.state, { type: "TransportStopped" });
    if (countdownMs > 0) {
      expect(transition.commands).toEqual([{ durationMs: countdownMs, purpose: "countdown", type: "Wait" }]);
      transition = reduceRecordOnceProgram(transition.state, { type: "WaitElapsed" });
    }
    expect(transition.commands).toEqual([{ spec: recordingSpec, type: "StartRecording" }]);
    expect(reduceRecordOnceProgram(transition.state, { type: "WaitElapsed" }).commands).toEqual([]);
  });

  it.each([
    { type: "Cancelled" } as const,
    { type: "SourceChanged" } as const,
    { type: "Stopped" } as const,
  ])("RecordOnce cancels on %o before countdown expiry", (fact) => {
    const countdown = reduceRecordOnceProgram(
      startRecordOnceProgram(3000, recordingSpec).state,
      { type: "TransportStopped" },
    );
    expect(reduceRecordOnceProgram(countdown.state, fact)).toMatchObject({
      commands: [{ type: "Complete" }],
      state: { phase: "cancelled" },
    });
  });
});

describe("practice effect runtime", () => {
  it("cancels an old run timer and ignores its stale callback", () => {
    const scheduled: Array<() => void> = [];
    const commands: PracticeCommand[] = [];
    const ports: PracticeRuntimePorts = {
      complete: () => commands.push({ type: "Complete" }),
      fail: (_runId, command) => commands.push(command),
      requestPlay: (_runId, nextPass) => commands.push({ pass: nextPass, type: "Play" }),
      projectSelection: (fieldOrd, range) => commands.push({ fieldOrd, range, type: "UpdateSelectionProjection" }),
      projectWait: vi.fn(),
      startRecording: (_runId, spec) => commands.push({ spec, type: "StartRecording" }),
      stopTransport: (_runId, fieldOrd) => commands.push({ fieldOrd, type: "StopTransport" }),
    };
    const runtime = new PracticeRuntime(ports, {
      clear: vi.fn(),
      schedule: (callback) => {
        scheduled.push(callback);
        return callback;
      },
    });
    const firstRun = runtime.startRepeat(pass, 500, null);
    runtime.dispatch(firstRun, { type: "PassCompleted" });
    const secondRun = runtime.startOnce(pass);
    scheduled[0]?.();

    expect(runtime.readSnapshot()?.runId).toBe(secondRun);
    expect(commands.filter((command) => command.type === "Play")).toHaveLength(2);
    expect(runtime.dispatch(firstRun, { type: "WaitElapsed" })).toBe(false);
  });

  it("cancels active programs from playing, paused, and waiting phases", () => {
    const ports = runtimePorts();
    const runtime = new PracticeRuntime(ports, {
      clear: vi.fn(),
      schedule: vi.fn(() => 1),
    });
    const playing = runtime.startOnce(pass);
    runtime.cancel();
    expect(runtime.readSnapshot()).toBeNull();
    const paused = runtime.startOnce(pass);
    runtime.dispatch(paused, { type: "PauseRequested" });
    runtime.cancel();
    const waiting = runtime.startRepeat(pass, 500, null);
    runtime.dispatch(waiting, { type: "PassCompleted" });
    runtime.cancel();
    expect(runtime.readSnapshot()).toBeNull();
    expect(ports.complete).toHaveBeenCalledTimes(3);
  });
});

function runtimePorts(): PracticeRuntimePorts & { complete: ReturnType<typeof vi.fn> } {
  return {
    complete: vi.fn(),
    fail: vi.fn(),
    requestPlay: vi.fn(),
    projectSelection: vi.fn(),
    projectWait: vi.fn(),
    startRecording: vi.fn(),
    stopTransport: vi.fn(),
  };
}
