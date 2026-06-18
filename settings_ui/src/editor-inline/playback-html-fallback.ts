import { readFieldState } from "./field-state-store.js";
import { selectionCoversFullDuration } from "./playback-model.js";
import type { PlaybackRequest, VisualizerElement } from "./types.js";

function fieldOrd(visualizer: VisualizerElement): number {
  return Number(visualizer.dataset.aqeFieldOrd || "0");
}

export function repeatFallbackRequiresBrowserAudio(visualizer: VisualizerElement, request: PlaybackRequest): boolean {
  if (!request.loop) return false;
  if (request.source === "post_edit") return true;
  if (request.regionMode !== "selection") return false;
  const state = readFieldState(fieldOrd(visualizer));
  const startMs = state.selection.active
    ? (state.selection.startMs ?? 0)
    : Number(request.cursorMs || "0");
  const endMs = state.selection.active
    ? (state.selection.endMs ?? request.endMs ?? state.graph.durationMs)
    : Number(request.endMs || state.graph.durationMs);
  return !selectionCoversFullDuration({ endMs, mode: "selection", startMs }, state.graph.durationMs);
}
