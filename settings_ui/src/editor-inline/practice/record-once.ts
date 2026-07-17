import type {
  PracticeFact,
  ProgramTransition,
  RecordingSpec,
  RecordOnceProgramState,
} from "./model.js";

export function startRecordOnceProgram(
  countdownMs: number,
  spec: RecordingSpec,
): ProgramTransition<RecordOnceProgramState> {
  return {
    commands: [{ fieldOrd: spec.fieldOrd, type: "StopTransport" }],
    state: {
      countdownMs: Math.max(0, Math.round(countdownMs)),
      kind: "record_once",
      phase: "stopping_transport",
      spec,
    },
  };
}

export function reduceRecordOnceProgram(
  state: RecordOnceProgramState,
  fact: PracticeFact,
): ProgramTransition<RecordOnceProgramState> {
  if (state.phase === "cancelled" || state.phase === "completed" || state.phase === "failed") {
    return { commands: [], state };
  }
  switch (fact.type) {
    case "TransportStopped":
      if (state.phase !== "stopping_transport") return { commands: [], state };
      return state.countdownMs > 0
        ? {
          commands: [{ durationMs: state.countdownMs, purpose: "countdown", type: "Wait" }],
          state: { ...state, phase: "countdown" },
        }
        : startRecorder(state);
    case "WaitElapsed":
      return state.phase === "countdown" ? startRecorder(state) : { commands: [], state };
    case "RecorderStarted":
      return state.phase === "starting_recorder"
        ? { commands: [], state: { ...state, phase: "recording" } }
        : { commands: [], state };
    case "RecorderCompleted":
      return state.phase === "recording" || state.phase === "starting_recorder"
        ? { commands: [{ type: "Complete" }], state: { ...state, phase: "completed" } }
        : { commands: [], state };
    case "RecorderFailed":
      return {
        commands: [{ reason: { kind: "recorder_failed", message: fact.message }, type: "Fail" }],
        state: { ...state, phase: "failed" },
      };
    case "TransportFailed":
      return {
        commands: [{ reason: { kind: "transport_failed", message: fact.message }, type: "Fail" }],
        state: { ...state, phase: "failed" },
      };
    case "Cancelled":
    case "SelectionChanged":
    case "SourceChanged":
    case "Stopped":
      return { commands: [{ type: "Complete" }], state: { ...state, phase: "cancelled" } };
    default:
      return { commands: [], state };
  }
}

function startRecorder(state: RecordOnceProgramState): ProgramTransition<RecordOnceProgramState> {
  return {
    commands: [{ spec: state.spec, type: "StartRecording" }],
    state: { ...state, phase: "starting_recorder" },
  };
}
