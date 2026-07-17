import type { OnceProgramState, PracticeFact, ProgramTransition, PracticePlaybackPass } from "./model.js";

export function startOnceProgram(pass: PracticePlaybackPass): ProgramTransition<OnceProgramState> {
  return {
    commands: [{ pass, type: "Play" }],
    state: { kind: "once", pass, phase: "playing" },
  };
}

export function reduceOnceProgram(
  state: OnceProgramState,
  fact: PracticeFact,
): ProgramTransition<OnceProgramState> {
  if (state.phase === "cancelled" || state.phase === "completed" || state.phase === "failed") {
    return { commands: [], state };
  }
  switch (fact.type) {
    case "PassCompleted":
      return { commands: [{ type: "Complete" }], state: { ...state, phase: "completed" } };
    case "PauseRequested":
      return { commands: [], state: { ...state, phase: "paused" } };
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
