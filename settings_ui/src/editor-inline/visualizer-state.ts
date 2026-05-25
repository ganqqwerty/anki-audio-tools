import type { PlaybackRegion } from "./playback-state.js";
import type { SelectionRange, SelectionState } from "./selection-state.js";
import type { VisualizerElement } from "./types.js";

export function readVisualizerDurationMs(visualizer: VisualizerElement): number {
  return Number(visualizer.dataset.durationMs || "0") || 0;
}

export function readVisualizerTargetDurationMs(visualizer: VisualizerElement): number {
  const targetDurationMs = Number(visualizer.dataset.targetDurationMs || "0") || 0;
  if (targetDurationMs > 0) return targetDurationMs;
  return readVisualizerDurationMs(visualizer);
}

export function readVisualizerCursorMs(visualizer: VisualizerElement): number {
  return Number(visualizer.dataset.cursorMs || "0") || 0;
}

export function readVisualizerRepeatEnabled(visualizer: VisualizerElement): boolean {
  return visualizer.dataset.repeatEnabled === "true";
}

export function setVisualizerResumeRequiresRestart(visualizer: VisualizerElement, required: boolean): void {
  visualizer.dataset.resumeRequiresRestart = required ? "true" : "false";
}

export function readVisualizerSelectionState(visualizer: VisualizerElement): SelectionState {
  return {
    active: visualizer.dataset.selectionActive === "true",
    draftActive: visualizer.dataset.selectionDraftActive === "true",
    draftEndMs: readOptionalMs(visualizer.dataset.selectionDraftEndMs),
    draftStartMs: readOptionalMs(visualizer.dataset.selectionDraftStartMs),
    endMs: readOptionalMs(visualizer.dataset.selectionEndMs),
    startMs: readOptionalMs(visualizer.dataset.selectionStartMs),
  };
}

export function clearVisualizerSelectionDraft(visualizer: VisualizerElement): void {
  visualizer.dataset.selectionDraftActive = "false";
  visualizer.dataset.selectionDraftStartMs = "";
  visualizer.dataset.selectionDraftEndMs = "";
}

export function setVisualizerSelectionDraft(visualizer: VisualizerElement, range: SelectionRange): void {
  visualizer.dataset.selectionDraftActive = "true";
  visualizer.dataset.selectionDraftStartMs = String(range.startMs);
  visualizer.dataset.selectionDraftEndMs = String(range.endMs);
}

export function clearVisualizerSelection(visualizer: VisualizerElement): void {
  visualizer.dataset.selectionActive = "false";
  visualizer.dataset.selectionStartMs = "";
  visualizer.dataset.selectionEndMs = "";
}

export function setVisualizerSelection(visualizer: VisualizerElement, range: SelectionRange): void {
  visualizer.dataset.selectionActive = "true";
  visualizer.dataset.selectionStartMs = String(range.startMs);
  visualizer.dataset.selectionEndMs = String(range.endMs);
}

export function setVisualizerPlaybackRegion(visualizer: VisualizerElement, region: PlaybackRegion): void {
  visualizer.dataset.playbackStartMs = String(Math.round(region.startMs));
  visualizer.dataset.playbackEndMs = String(Math.round(region.endMs));
  visualizer.dataset.playbackRegionMode = region.mode;
}

function readOptionalMs(rawValue: string | undefined): number | null {
  if (!rawValue) return null;
  const value = Number(rawValue);
  return Number.isFinite(value) ? value : null;
}
