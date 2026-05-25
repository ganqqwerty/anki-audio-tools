import type { PlaybackRegion } from "./playback-state.js";
import {
  draftSelectionRegion,
  emptySelectionState,
  selectionRegion,
  setDraftSelectionRange,
  setSelectionRange,
} from "./selection-state.js";
import type { PlaybackState, VisualizerElement } from "./types.js";
import { renderSelection } from "./visualizer-renderer.js";
import {
  clearVisualizerSelection,
  clearVisualizerSelectionDraft,
  readVisualizerSelectionState,
  readVisualizerTargetDurationMs,
  setVisualizerPlaybackRegion,
  setVisualizerSelection,
  setVisualizerSelectionDraft,
} from "./visualizer-state.js";

export interface SelectionControllerDependencies {
  setCursor: (
    visualizer: VisualizerElement,
    ms: number,
    notifyPython: boolean,
    options?: {
      engine?: "html" | "native" | "";
      previousPlaybackState?: PlaybackState;
      restartPlayback?: boolean;
      updateAnchor?: boolean;
    },
  ) => void;
}

export function selectionForVisualizer(visualizer: VisualizerElement | null): PlaybackRegion | null {
  if (!visualizer) return null;
  return selectionRegion(readVisualizerSelectionState(visualizer), readVisualizerTargetDurationMs(visualizer));
}

export function draftSelectionForVisualizer(visualizer: VisualizerElement | null): PlaybackRegion | null {
  if (!visualizer) return null;
  return draftSelectionRegion(readVisualizerSelectionState(visualizer), readVisualizerTargetDurationMs(visualizer));
}

export function effectivePlaybackRegion(visualizer: VisualizerElement): PlaybackRegion {
  const selection = selectionForVisualizer(visualizer);
  if (selection) return selection;
  return {
    startMs: 0,
    endMs: readVisualizerTargetDurationMs(visualizer),
    mode: "full",
  };
}

export function clearSelectionDraft(
  visualizer: VisualizerElement,
  options: { redraw?: boolean } = {},
): void {
  clearVisualizerSelectionDraft(visualizer);
  if (options.redraw !== false) {
    drawSelection(visualizer);
  }
}

export function setSelectionDraft(
  visualizer: VisualizerElement,
  startMs: number,
  endMs: number,
  options: { redraw?: boolean } = {},
): boolean {
  const durationMs = readVisualizerTargetDurationMs(visualizer);
  const selection = setDraftSelectionRange(emptySelectionState(), startMs, endMs, durationMs);
  if (!selection.draftActive || selection.draftStartMs === null || selection.draftEndMs === null) {
    clearSelectionDraft(visualizer, options);
    return false;
  }
  setVisualizerSelectionDraft(visualizer, {
    startMs: selection.draftStartMs,
    endMs: selection.draftEndMs,
  });
  if (options.redraw !== false) {
    drawSelection(visualizer);
  }
  return true;
}

export function commitSelectionDraft(
  visualizer: VisualizerElement,
  deps: SelectionControllerDependencies,
  options: { updateCursor?: boolean } = {},
): boolean {
  const draft = draftSelectionForVisualizer(visualizer);
  if (!draft) {
    clearSelectionDraft(visualizer);
    return false;
  }
  clearSelectionDraft(visualizer, { redraw: false });
  return setSelection(visualizer, draft.startMs, draft.endMs, deps, options);
}

export function clearSelection(
  visualizer: VisualizerElement,
  options: { resetPlaybackRegion?: boolean } = {},
): void {
  clearVisualizerSelection(visualizer);
  clearSelectionDraft(visualizer, { redraw: false });
  drawSelection(visualizer);
  if (options.resetPlaybackRegion !== false) {
    setVisualizerPlaybackRegion(visualizer, effectivePlaybackRegion(visualizer));
  }
}

export function setSelection(
  visualizer: VisualizerElement,
  startMs: number,
  endMs: number,
  deps: SelectionControllerDependencies,
  options: { updateCursor?: boolean } = {},
): boolean {
  const durationMs = readVisualizerTargetDurationMs(visualizer);
  const selection = setSelectionRange(emptySelectionState(), startMs, endMs, durationMs);
  if (!selection.active || selection.startMs === null || selection.endMs === null) {
    clearSelection(visualizer);
    return false;
  }
  const committedRange = {
    startMs: selection.startMs,
    endMs: selection.endMs,
  };
  clearSelectionDraft(visualizer, { redraw: false });
  setVisualizerSelection(visualizer, committedRange);
  setVisualizerPlaybackRegion(visualizer, { ...committedRange, mode: "selection" });
  drawSelection(visualizer);
  if (options.updateCursor !== false) {
    deps.setCursor(visualizer, selection.startMs, false);
  }
  return true;
}

function drawSelection(visualizer: VisualizerElement): void {
  const draftSelection = draftSelectionForVisualizer(visualizer);
  const selection = draftSelection ?? selectionForVisualizer(visualizer);
  renderSelection(visualizer, selection, draftSelection);
}
