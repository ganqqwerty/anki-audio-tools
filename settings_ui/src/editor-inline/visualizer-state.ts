import type { PlaybackRegion } from "./playback-state.js";
import type { SelectionRange, SelectionState } from "./selection-state.js";
import {
  clearDraftSelectionState,
  clearSelectionState,
  setDraftSelectionRange,
  setSelectionRange,
} from "./selection-state.js";
import {
  fullTimeViewport,
  type TimeViewport,
} from "./time-viewport.js";
import type { VisualizerElement } from "./types.js";
import {
  readFieldState,
  updateFieldState,
  writeFieldState,
} from "./field-state-store.js";
import {
  readRuntimeTimeViewport,
  readTargetDurationMsForVisualizer,
  writeRuntimeTimeViewport,
} from "./visualizer-runtime-state.js";

function fieldOrd(visualizer: VisualizerElement): number {
  return Number(visualizer.dataset.aqeFieldOrd || "0");
}

export function readVisualizerDurationMs(visualizer: VisualizerElement): number {
  return readFieldState(fieldOrd(visualizer)).graph.durationMs;
}

export function readVisualizerTargetDurationMs(visualizer: VisualizerElement): number {
  return readTargetDurationMsForVisualizer(
    visualizer,
    readFieldState(fieldOrd(visualizer)).graph.durationMs,
  );
}

export function readVisualizerTimeViewport(visualizer: VisualizerElement): TimeViewport {
  const durationMs = readVisualizerDurationMs(visualizer);
  return readRuntimeTimeViewport(visualizer, durationMs);
}

export function resetVisualizerTimeViewport(
  visualizer: VisualizerElement,
  durationMs = readVisualizerDurationMs(visualizer),
): void {
  writeVisualizerTimeViewport(visualizer, fullTimeViewport(durationMs));
}

export function writeVisualizerTimeViewport(visualizer: VisualizerElement, viewport: TimeViewport): void {
  writeRuntimeTimeViewport(visualizer, viewport);
}

export function readVisualizerCursorMs(visualizer: VisualizerElement): number {
  return readFieldState(fieldOrd(visualizer)).cursor.ms;
}

export function readVisualizerRepeatEnabled(visualizer: VisualizerElement): boolean {
  return readFieldState(fieldOrd(visualizer)).playback.repeat;
}

export function setVisualizerResumeRequiresRestart(visualizer: VisualizerElement, required: boolean): void {
  const ord = fieldOrd(visualizer);
  const state = readFieldState(ord);
  writeFieldState(ord, {
    ...state,
    playback: { ...state.playback, resumeRequiresRestart: required },
  });
}

export function readVisualizerSelectionState(visualizer: VisualizerElement): SelectionState {
  return readFieldState(fieldOrd(visualizer)).selection;
}

export function clearVisualizerSelectionDraft(visualizer: VisualizerElement): void {
  const ord = fieldOrd(visualizer);
  updateFieldState(ord, (state) => ({
    ...state,
    selection: clearDraftSelectionState(state.selection),
  }));
}

export function setVisualizerSelectionDraft(visualizer: VisualizerElement, range: SelectionRange): void {
  const ord = fieldOrd(visualizer);
  updateFieldState(ord, (state) => ({
    ...state,
    selection: setDraftSelectionRange(state.selection, range.startMs, range.endMs, state.graph.durationMs),
  }));
}

export function clearVisualizerSelection(visualizer: VisualizerElement): void {
  const ord = fieldOrd(visualizer);
  updateFieldState(ord, (state) => ({
    ...state,
    selection: clearSelectionState(state.selection),
  }));
}

export function setVisualizerSelection(visualizer: VisualizerElement, range: SelectionRange): void {
  const ord = fieldOrd(visualizer);
  updateFieldState(ord, (state) => ({
    ...state,
    selection: setSelectionRange(state.selection, range.startMs, range.endMs, state.graph.durationMs),
  }));
}

export function setVisualizerPlaybackRegion(visualizer: VisualizerElement, region: PlaybackRegion): void {
  const ord = fieldOrd(visualizer);
  const state = readFieldState(ord);
  writeFieldState(ord, {
    ...state,
    playback: {
      ...state.playback,
      endMs: Math.round(region.endMs),
      regionMode: region.mode,
      startMs: Math.round(region.startMs),
    },
  });
}
