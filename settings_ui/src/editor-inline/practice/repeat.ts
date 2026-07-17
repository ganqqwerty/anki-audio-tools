import type {
  PracticeFact,
  PracticePlaybackPass,
  ProgramTransition,
  RepeatProgramState,
} from "./model.js";

export function startRepeatProgram(
  pass: PracticePlaybackPass,
  gapMs: number,
  count: number | null,
): ProgramTransition<RepeatProgramState> {
  const normalizedCount = count === null ? null : Math.max(1, Math.round(count));
  return {
    commands: [{ pass, type: "Play" }],
    state: {
      completedPasses: 0,
      count: normalizedCount,
      finishAfterCurrentPass: false,
      gapMs: Math.max(0, Math.round(gapMs)),
      kind: "repeat",
      pass,
      phase: "playing",
    },
  };
}

export function reduceRepeatProgram(
  state: RepeatProgramState,
  fact: PracticeFact,
): ProgramTransition<RepeatProgramState> {
  if (state.phase === "cancelled" || state.phase === "completed" || state.phase === "failed") {
    return { commands: [], state };
  }
  switch (fact.type) {
    case "PassCompleted": {
      if (state.phase !== "playing") return { commands: [], state };
      const completedPasses = state.completedPasses + 1;
      if (state.finishAfterCurrentPass || (state.count !== null && completedPasses >= state.count)) {
        return {
          commands: [{ type: "Complete" }],
          state: { ...state, completedPasses, phase: "completed" },
        };
      }
      return state.gapMs > 0
        ? {
          commands: [{ durationMs: state.gapMs, purpose: "repeat_gap", type: "Wait" }],
          state: { ...state, completedPasses, phase: "waiting" },
        }
        : {
          commands: [{ pass: state.pass, type: "Play" }],
          state: { ...state, completedPasses, phase: "playing" },
        };
    }
    case "RepeatDisabled":
      if (state.phase === "waiting") {
        return {
          commands: [{ type: "Complete" }],
          state: { ...state, phase: "completed" },
        };
      }
      return state.phase === "playing" || state.phase === "paused"
        ? { commands: [], state: { ...state, finishAfterCurrentPass: true } }
        : { commands: [], state };
    case "WaitElapsed":
      return state.phase === "waiting"
        ? { commands: [{ pass: state.pass, type: "Play" }], state: { ...state, phase: "playing" } }
        : { commands: [], state };
    case "PauseRequested":
      return state.phase === "waiting" || state.phase === "playing"
        ? { commands: [], state: { ...state, phase: "paused" } }
        : { commands: [], state };
    case "ResumeRequested":
      return state.phase === "paused"
        ? { commands: [{ pass: state.pass, type: "Play" }], state: { ...state, phase: "playing" } }
        : { commands: [], state };
    case "TransportResumed":
      return state.phase === "paused"
        ? { commands: [], state: { ...state, phase: "playing" } }
        : { commands: [], state };
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
