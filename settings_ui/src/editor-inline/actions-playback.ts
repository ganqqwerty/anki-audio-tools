import { visualizerForOrd } from "./dom-selectors.js";
import { seekAudioElementForCursorPreview as seekAudioElementForCursorPreviewElement } from "./audio-clock.js";
import type {
  PlaybackRequest,
  VisualizerElement,
} from "./types.js";
import { syncSelectionToolbar } from "./selection-toolbar-state.js";
import { repeatDefaultFromConfig } from "./control-actions.js";
import { clearPlaybackFrame as clearPlaybackFrameFromController } from "./playback-controller-frame.js";
import {
  clampProgressMs,
  setRepeatEnabled,
} from "./actions-audio-clock.js";
import {
  clearSelection as clearSelectionFromController,
  effectivePlaybackRegion as effectivePlaybackRegionFromController,
} from "./selection-controller.js";
import { readVisualizerTargetDurationMs } from "./visualizer-state.js";
import { notifySelectionChanged } from "./selection-events.js";
import { readFieldState, writeFieldState } from "./field-state-store.js";
import { repeatEnabledFor } from "./repeat-control-projection.js";
import {
  setPlaybackPassRuntime,
  setRepeatPauseSecondsRuntime,
} from "./visualizer-runtime-state.js";

export { setCursor } from "./cursor-actions.js";
export { playbackControllerDependencies } from "./playback-controller-dependencies.js";

function fieldOrd(v: VisualizerElement): number {
  return Number(v.dataset.aqeFieldOrd || "0");
}

export function clearPlaybackFrame(visualizer: VisualizerElement): void {
  clearPlaybackFrameFromController(visualizer);
}

export function setRepeatEnabledForOrd(ord: number, enabled: boolean): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  setRepeatEnabled(visualizer, enabled);
  return true;
}

export function setRepeatPauseSeconds(visualizer: VisualizerElement, seconds: number): void {
  setRepeatPauseSecondsRuntime(visualizer, seconds);
}

export function setRepeatPauseSecondsForOrd(ord: number, seconds: number): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  setRepeatPauseSeconds(visualizer, seconds);
  return true;
}

export function playbackRequestForStart(
  visualizer: VisualizerElement,
  ord: number,
  startMs: number,
): PlaybackRequest {
  const region = effectivePlaybackRegionFromController(visualizer);
  return {
    ord,
    action: "start",
    cursorMs: Math.round(clampProgressMs(visualizer, startMs)),
    endMs: Math.round(region.endMs),
    engine: "html",
    loop: repeatEnabledFor(visualizer),
    regionMode: region.mode,
  };
}

export function seekAudioElementForCursorPreview(visualizer: VisualizerElement, ms: number): boolean {
  return seekAudioElementForCursorPreviewElement(visualizer, ms, readVisualizerTargetDurationMs(visualizer));
}

export function initializePlaybackRegionState(visualizer: VisualizerElement): void {
  const s = readFieldState(fieldOrd(visualizer));
  writeFieldState(s.ord, {
    ...s,
    playback: {
      ...s.playback,
      endMs: s.graph.durationMs || 0,
      regionMode: "full",
      startMs: 0,
    },
  });
  setPlaybackPassRuntime(visualizer, {
    endMs: s.graph.durationMs || 0,
    loop: repeatDefaultFromConfig(),
    regionMode: "full",
    resetCursorMs: 0,
    startMs: 0,
  });
  setRepeatEnabled(visualizer, repeatDefaultFromConfig());
  clearSelectionFromController(visualizer, { resetPlaybackRegion: false });
  notifySelectionChanged(visualizer, "system");
  syncSelectionToolbar(visualizer);
}
