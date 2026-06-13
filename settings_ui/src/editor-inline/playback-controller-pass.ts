import { planPlaybackPass } from "./playback-model.js";
import type {
  PlaybackPass,
  PlaybackRegion,
  PlaybackRegionMode,
  PlaybackSnapshot,
  PlaybackEngine,
} from "./playback-model.js";
import type { PlaybackState, VisualizerElement } from "./types.js";
import type { PlaybackControllerDependencies } from "./playback-controller.js";
import { liveProgressMs } from "./playback-plan-state.js";
import { readFieldState, writeFieldState } from "./field-state-store.js";
import type { EditorFieldState } from "./field-state.js";

function fieldState(visualizer: VisualizerElement): EditorFieldState {
  return readFieldState(Number(visualizer.dataset.aqeFieldOrd || "0"));
}

export function setPlaybackPass(
  visualizer: VisualizerElement,
  startMs: number,
  deps: PlaybackControllerDependencies,
  region: PlaybackRegion = deps.effectivePlaybackRegion(visualizer),
): PlaybackPass {
  const pass = planPlaybackPass(playbackSnapshotForPass(visualizer, deps, region), startMs);
  writePlaybackPass(visualizer, pass);
  return pass;
}

export function playbackEndMs(visualizer: VisualizerElement, deps: PlaybackControllerDependencies): number {
  return activePlaybackPass(visualizer, deps).endMs;
}

export function plannedPlaybackPass(
  visualizer: VisualizerElement,
  startMs: number,
  deps: PlaybackControllerDependencies,
  region: PlaybackRegion = deps.effectivePlaybackRegion(visualizer),
): PlaybackPass {
  return planPlaybackPass(playbackSnapshotForPass(visualizer, deps, region), startMs);
}

function playbackSnapshotForPass(
  visualizer: VisualizerElement,
  deps: PlaybackControllerDependencies,
  region: PlaybackRegion,
): PlaybackSnapshot {
  const s = fieldState(visualizer);
  return {
    anchorMs: s.cursor.anchorMs,
    currentProgressMs: currentProgressMs(visualizer),
    cursorMs: s.cursor.ms,
    durationMs: s.graph.durationMs,
    engine: playbackEngineForDataset(s.playback.engine),
    ord: s.ord,
    playbackState: playbackStateForDataset(s.playback.state),
    region,
    repeat: deps.repeatEnabledFor(visualizer),
    resumeRequiresRestart: s.playback.resumeRequiresRestart,
  };
}

export function activePlaybackPass(visualizer: VisualizerElement, deps: PlaybackControllerDependencies): PlaybackPass {
  const region = deps.effectivePlaybackRegion(visualizer);
  const s = fieldState(visualizer);
  const regionMode = playbackRegionModeForDataset(s.playback.regionMode);
  const fallbackResetCursorMs = regionMode === "selection"
    ? region.startMs
    : s.cursor.anchorMs;
  const rawEndMs = s.playback.endMs ?? region.endMs; // ?? is dead (store ms are non-nullable), kept as safety
  const endMs = s.graph.durationMs > 0 ? Math.min(rawEndMs, s.graph.durationMs) : rawEndMs;
  return {
    endMs: Math.round(Math.max(0, endMs)),
    loop: visualizer.dataset.playbackLoop === "true",
    regionMode,
    resetCursorMs: Math.round(readDomStoredMs(visualizer.dataset.playbackResetCursorMs, fallbackResetCursorMs)),
    startMs: Math.round(s.playback.startMs ?? region.startMs), // ?? is dead (store ms are non-nullable), kept as safety
  };
}

export function writePlaybackPass(visualizer: VisualizerElement, pass: PlaybackPass): void {
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  writeFieldState(ord, {
    ...readFieldState(ord),
    playback: {
      ...readFieldState(ord).playback,
      endMs: Math.round(pass.endMs),
      regionMode: pass.regionMode,
      startMs: Math.round(pass.startMs),
    },
  });
  visualizer.dataset.playbackResetCursorMs = String(Math.round(pass.resetCursorMs));
  visualizer.dataset.playbackLoop = pass.loop ? "true" : "false";
}

function playbackStateForDataset(value: string | undefined): PlaybackState {
  if (value === "playing" || value === "paused") return value;
  return "stopped";
}

function playbackEngineForDataset(value: string | undefined): PlaybackEngine {
  return value === "html" || value === "native" ? value : "";
}

function playbackRegionModeForDataset(value: string | undefined): PlaybackRegionMode {
  return value === "selection" ? "selection" : "full";
}

function readDomStoredMs(rawValue: string | undefined, fallbackMs: number): number {
  if (!rawValue) return fallbackMs;
  const value = Number(rawValue);
  return Number.isFinite(value) ? value : fallbackMs;
}

function currentProgressMs(visualizer: VisualizerElement): number | null {
  const planned = liveProgressMs(visualizer);
  if (planned !== null) return planned;
  const s = fieldState(visualizer);
  return s.cursor.progressMs || s.cursor.ms;
}
