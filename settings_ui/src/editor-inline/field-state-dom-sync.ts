import type { EditorFieldState } from "./field-state.js";
import { visualizerForOrd } from "./dom-selectors.js";

export function syncFieldStateToDom(ord: number, state: EditorFieldState): void {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return;

  visualizer.dataset.graphActive = String(state.graph.active);
  visualizer.dataset.graphBusy = String(state.graph.busy);
  visualizer.dataset.hasTrack = String(state.graph.hasTrack);
  visualizer.dataset.durationMs = String(state.graph.durationMs);
  visualizer.dataset.sourceFilename = state.sourceFilename;
  visualizer.dataset.analyzerName = state.graph.analyzerName;
  visualizer.dataset.anchorMs = String(Math.round(state.cursor.anchorMs));
  visualizer.dataset.cursorMs = String(Math.round(state.cursor.ms));
  visualizer.dataset.progressMs = String(Math.round(state.cursor.progressMs));
  visualizer.dataset.playbackState = state.playback.state;
  visualizer.dataset.playbackEngine = state.playback.engine;
  visualizer.dataset.playbackStartMs = String(Math.round(state.playback.startMs));
  visualizer.dataset.playbackEndMs = String(Math.round(state.playback.endMs));
  visualizer.dataset.playbackRegionMode = state.playback.regionMode;
  visualizer.dataset.resumeRequiresRestart = String(state.playback.resumeRequiresRestart);
  visualizer.dataset.repeatEnabled = String(state.playback.repeat);
  visualizer.dataset.progressClockMode = state.playback.clockMode;

  visualizer.dataset.selectionActive = String(state.selection.active);
  visualizer.dataset.selectionDraftActive = String(state.selection.draftActive);
  if (state.selection.startMs !== null) {
    visualizer.dataset.selectionStartMs = String(state.selection.startMs);
  } else {
    delete visualizer.dataset.selectionStartMs;
  }
  if (state.selection.endMs !== null) {
    visualizer.dataset.selectionEndMs = String(state.selection.endMs);
  } else {
    delete visualizer.dataset.selectionEndMs;
  }
  if (state.selection.draftStartMs !== null) {
    visualizer.dataset.selectionDraftStartMs = String(state.selection.draftStartMs);
  } else {
    delete visualizer.dataset.selectionDraftStartMs;
  }
  if (state.selection.draftEndMs !== null) {
    visualizer.dataset.selectionDraftEndMs = String(state.selection.draftEndMs);
  } else {
    delete visualizer.dataset.selectionDraftEndMs;
  }
}
