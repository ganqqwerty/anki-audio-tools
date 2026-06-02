import type { PlaybackRegion } from "./playback-state.js";
import type { SelectionRange, SelectionState } from "./selection-state.js";
import { fullTimeViewport, normalizeTimeViewport, type TimeViewport } from "./time-viewport.js";
import type { VisualizerElement } from "./types.js";

export function readVisualizerDurationMs(visualizer: VisualizerElement): number {
  return Number(visualizer.dataset.durationMs || "0") || 0;
}

export function readVisualizerTargetDurationMs(visualizer: VisualizerElement): number {
  const targetDurationMs = Number(visualizer.dataset.targetDurationMs || "0") || 0;
  if (targetDurationMs > 0) return targetDurationMs;
  return readVisualizerDurationMs(visualizer);
}

export function readVisualizerTimeViewport(visualizer: VisualizerElement): TimeViewport {
  const durationMs = readVisualizerDurationMs(visualizer);
  const startMs = Number(visualizer.dataset.viewportStartMs || "0") || 0;
  const endMs = Number(visualizer.dataset.viewportEndMs || String(durationMs)) || durationMs;
  return normalizeTimeViewport(startMs, endMs, durationMs);
}

export function resetVisualizerTimeViewport(
  visualizer: VisualizerElement,
  durationMs = readVisualizerDurationMs(visualizer),
): void {
  writeVisualizerTimeViewport(visualizer, fullTimeViewport(durationMs));
}

export function writeVisualizerTimeViewport(visualizer: VisualizerElement, viewport: TimeViewport): void {
  const normalized = normalizeTimeViewport(viewport.startMs, viewport.endMs, viewport.durationMs);
  visualizer.dataset.viewportStartMs = String(Math.round(normalized.startMs));
  visualizer.dataset.viewportEndMs = String(Math.round(normalized.endMs));
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
  visualizer.dataset.playbackResetCursorMs = String(Math.round(
    region.mode === "selection"
      ? region.startMs
      : Number(visualizer.dataset.anchorMs || visualizer.dataset.cursorMs || "0"),
  ));
}

function readOptionalMs(rawValue: string | undefined): number | null {
  if (!rawValue) return null;
  const value = Number(rawValue);
  return Number.isFinite(value) ? value : null;
}
