import type {
  ChorusingProgramState,
  PracticeCommand,
  PracticeFact,
  PracticePlaybackPass,
  PracticeRange,
  ProgramTransition,
} from "./model.js";

export function startChorusingProgram(
  pass: PracticePlaybackPass,
  selection: PracticeRange,
  markersMs: readonly number[],
  repeatCount: number,
  gapMs: number,
): ProgramTransition<ChorusingProgramState> {
  const normalizedMarkers = normalizeMarkers(markersMs);
  if (!normalizedMarkers) {
    return {
      commands: [{ reason: { kind: "invalid_markers" }, type: "Fail" }],
      state: {
        completedPasses: 0,
        finishAfterCurrentPass: false,
        gapMs: Math.max(0, Math.round(gapMs)),
        kind: "chorusing",
        markersMs: [],
        pass,
        phase: "failed",
        repeatCount: Math.max(1, Math.round(repeatCount)),
        selection,
      },
    };
  }
  return {
    commands: [{ pass, type: "Play" }],
    state: {
      completedPasses: 0,
      finishAfterCurrentPass: false,
      gapMs: Math.max(0, Math.round(gapMs)),
      kind: "chorusing",
      markersMs: normalizedMarkers,
      pass,
      phase: "playing",
      repeatCount: Math.max(1, Math.round(repeatCount)),
      selection,
    },
  };
}

export function reduceChorusingProgram(
  state: ChorusingProgramState,
  fact: PracticeFact,
): ProgramTransition<ChorusingProgramState> {
  if (state.phase === "cancelled" || state.phase === "completed" || state.phase === "failed") {
    return { commands: [], state };
  }
  switch (fact.type) {
    case "PassCompleted":
      return advanceAfterPass(state);
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
      return state.phase === "playing" || state.phase === "waiting"
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
    case "Skip":
      return advanceSuffix(state);
    case "MarkersUpdated": {
      const markersMs = normalizeMarkers(fact.markersMs);
      return markersMs
        ? { commands: [], state: { ...state, markersMs } }
        : {
          commands: [{ reason: { kind: "invalid_markers" }, type: "Fail" }],
          state: { ...state, phase: "failed" },
        };
    }
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

function advanceAfterPass(state: ChorusingProgramState): ProgramTransition<ChorusingProgramState> {
  if (state.phase !== "playing") return { commands: [], state };
  const completedPasses = state.completedPasses + 1;
  if (state.finishAfterCurrentPass) {
    return {
      commands: [{ type: "Complete" }],
      state: { ...state, completedPasses, phase: "completed" },
    };
  }
  if (completedPasses < state.repeatCount) {
    return schedulePass({ ...state, completedPasses });
  }
  return advanceSuffix({ ...state, completedPasses: 0 });
}

function advanceSuffix(state: ChorusingProgramState): ProgramTransition<ChorusingProgramState> {
  const startMs = nearestMarkerLeftOf(state.markersMs, state.selection.startMs);
  if (startMs === null) {
    return { commands: [{ type: "Complete" }], state: { ...state, phase: "completed" } };
  }
  const selection = { endMs: state.selection.endMs, startMs };
  const pass = { ...state.pass, resetCursorMs: startMs, startMs };
  const next = { ...state, completedPasses: 0, pass, selection };
  const selectionCommand: PracticeCommand = {
    fieldOrd: pass.ord,
    range: selection,
    type: "UpdateSelectionProjection",
  };
  const scheduled = schedulePass(next);
  return { commands: [selectionCommand, ...scheduled.commands], state: scheduled.state };
}

function schedulePass(state: ChorusingProgramState): ProgramTransition<ChorusingProgramState> {
  return state.gapMs > 0
    ? {
      commands: [{ durationMs: state.gapMs, purpose: "repeat_gap", type: "Wait" }],
      state: { ...state, phase: "waiting" },
    }
    : {
      commands: [{ pass: state.pass, type: "Play" }],
      state: { ...state, phase: "playing" },
    };
}

function nearestMarkerLeftOf(markersMs: readonly number[], startMs: number): number | null {
  for (let index = markersMs.length - 1; index >= 0; index -= 1) {
    const marker = markersMs[index];
    if (marker !== undefined && marker < Math.round(startMs)) return marker;
  }
  return null;
}

function normalizeMarkers(markersMs: readonly number[]): readonly number[] | null {
  if (markersMs.some((marker) => !Number.isFinite(marker) || marker < 0)) return null;
  const normalized = [...new Set(markersMs.map(Math.round))].sort((left, right) => left - right);
  return normalized.length === markersMs.length ? normalized : null;
}
