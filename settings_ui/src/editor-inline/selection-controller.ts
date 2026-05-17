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
  if (!visualizer || visualizer.dataset.selectionActive !== "true") return null;
  return selectionRegion({
    active: visualizer.dataset.selectionActive === "true",
    startMs: Number(visualizer.dataset.selectionStartMs || "0"),
    endMs: Number(visualizer.dataset.selectionEndMs || "0"),
  }, Number(visualizer.dataset.durationMs || "0"));
}

export function draftSelectionForVisualizer(visualizer: VisualizerElement | null): PlaybackRegion | null {
  if (!visualizer || visualizer.dataset.selectionDraftActive !== "true") return null;
  return draftSelectionRegion({
    draftActive: visualizer.dataset.selectionDraftActive === "true",
    draftStartMs: Number(visualizer.dataset.selectionDraftStartMs || "0"),
    draftEndMs: Number(visualizer.dataset.selectionDraftEndMs || "0"),
  }, Number(visualizer.dataset.durationMs || "0"));
}

export function effectivePlaybackRegion(visualizer: VisualizerElement): PlaybackRegion {
  const selection = selectionForVisualizer(visualizer);
  if (selection) return selection;
  return {
    startMs: 0,
    endMs: Number(visualizer.dataset.durationMs || "0") || 0,
    mode: "full",
  };
}

export function clearSelectionDraft(
  visualizer: VisualizerElement,
  options: { redraw?: boolean } = {},
): void {
  visualizer.dataset.selectionDraftActive = "false";
  visualizer.dataset.selectionDraftStartMs = "";
  visualizer.dataset.selectionDraftEndMs = "";
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
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  const selection = setDraftSelectionRange(emptySelectionState(), startMs, endMs, durationMs);
  if (!selection.draftActive || selection.draftStartMs === null || selection.draftEndMs === null) {
    clearSelectionDraft(visualizer, options);
    return false;
  }
  visualizer.dataset.selectionDraftActive = "true";
  visualizer.dataset.selectionDraftStartMs = String(selection.draftStartMs);
  visualizer.dataset.selectionDraftEndMs = String(selection.draftEndMs);
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
  visualizer.dataset.selectionActive = "false";
  visualizer.dataset.selectionStartMs = "";
  visualizer.dataset.selectionEndMs = "";
  clearSelectionDraft(visualizer, { redraw: false });
  drawSelection(visualizer);
  if (options.resetPlaybackRegion !== false) {
    const region = effectivePlaybackRegion(visualizer);
    visualizer.dataset.playbackStartMs = String(Math.round(region.startMs));
    visualizer.dataset.playbackEndMs = String(Math.round(region.endMs));
    visualizer.dataset.playbackRegionMode = region.mode;
  }
}

export function setSelection(
  visualizer: VisualizerElement,
  startMs: number,
  endMs: number,
  deps: SelectionControllerDependencies,
  options: { updateCursor?: boolean } = {},
): boolean {
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  const selection = setSelectionRange(emptySelectionState(), startMs, endMs, durationMs);
  if (!selection.active || selection.startMs === null || selection.endMs === null) {
    clearSelection(visualizer);
    return false;
  }
  clearSelectionDraft(visualizer, { redraw: false });
  visualizer.dataset.selectionActive = "true";
  visualizer.dataset.selectionStartMs = String(selection.startMs);
  visualizer.dataset.selectionEndMs = String(selection.endMs);
  visualizer.dataset.playbackStartMs = String(selection.startMs);
  visualizer.dataset.playbackEndMs = String(selection.endMs);
  visualizer.dataset.playbackRegionMode = "selection";
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
