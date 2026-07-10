import type { SelectionRange } from "./selection-state.js";

export type SelectionAutoAdvanceAction = "advance" | "complete" | "ignore" | "repeat";

export interface SelectionAutoAdvanceInput {
  autoAdvance: boolean;
  markersMs: readonly number[];
  repeatCount: number;
  repeatPassesCompleted: number;
  selection: SelectionRange | null;
}

export interface SelectionAutoAdvanceDecision {
  action: SelectionAutoAdvanceAction;
  nextRepeatPassesCompleted: number;
  nextSelection: SelectionRange | null;
}

export function resolveSelectionAutoAdvanceBoundary(
  input: SelectionAutoAdvanceInput,
): SelectionAutoAdvanceDecision {
  if (!input.autoAdvance || !input.selection) {
    return {
      action: "ignore",
      nextRepeatPassesCompleted: input.repeatPassesCompleted,
      nextSelection: null,
    };
  }
  const repeatCount = Math.max(1, Math.round(input.repeatCount));
  const completed = input.repeatPassesCompleted + 1;
  if (completed < repeatCount) {
    return {
      action: "repeat",
      nextRepeatPassesCompleted: completed,
      nextSelection: null,
    };
  }
  const currentStart = Math.round(input.selection.startMs);
  const nextStart = nearestMarkerLeftOf(input.markersMs, currentStart);
  if (nextStart === null) {
    return {
      action: "complete",
      nextRepeatPassesCompleted: 0,
      nextSelection: null,
    };
  }
  return {
    action: "advance",
    nextRepeatPassesCompleted: 0,
    nextSelection: {
      endMs: input.selection.endMs,
      startMs: nextStart,
    },
  };
}

function nearestMarkerLeftOf(markersMs: readonly number[], startMs: number): number | null {
  for (let index = markersMs.length - 1; index >= 0; index -= 1) {
    const marker = markersMs[index];
    if (typeof marker === "number" && Number.isFinite(marker) && Math.round(marker) < startMs) {
      return Math.round(marker);
    }
  }
  return null;
}
