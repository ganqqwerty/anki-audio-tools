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
  return {
    anchorMs: Number(visualizer.dataset.anchorMs || visualizer.dataset.cursorMs || "0"),
    currentProgressMs: currentProgressMs(visualizer),
    cursorMs: Number(visualizer.dataset.cursorMs || "0"),
    durationMs: Number(visualizer.dataset.durationMs || "0") || 0,
    engine: playbackEngineForDataset(visualizer.dataset.playbackEngine),
    ord: Number(visualizer.dataset.aqeFieldOrd || "0"),
    playbackState: playbackStateForDataset(visualizer.dataset.playbackState),
    region,
    repeat: deps.repeatEnabledFor(visualizer),
    resumeRequiresRestart: visualizer.dataset.resumeRequiresRestart === "true",
  };
}

export function activePlaybackPass(visualizer: VisualizerElement, deps: PlaybackControllerDependencies): PlaybackPass {
  const region = deps.effectivePlaybackRegion(visualizer);
  const durationMs = Number(visualizer.dataset.durationMs || "0") || 0;
  const regionMode = playbackRegionModeForDataset(visualizer.dataset.playbackRegionMode);
  const fallbackResetCursorMs = regionMode === "selection"
    ? region.startMs
    : Number(visualizer.dataset.anchorMs || visualizer.dataset.cursorMs || "0");
  const rawEndMs = readStoredMs(visualizer.dataset.playbackEndMs, region.endMs);
  const endMs = durationMs > 0 ? Math.min(rawEndMs, durationMs) : rawEndMs;
  return {
    endMs: Math.round(Math.max(0, endMs)),
    loop: visualizer.dataset.playbackLoop === "true",
    regionMode,
    resetCursorMs: Math.round(readStoredMs(visualizer.dataset.playbackResetCursorMs, fallbackResetCursorMs)),
    startMs: Math.round(readStoredMs(visualizer.dataset.playbackStartMs, region.startMs)),
  };
}

export function writePlaybackPass(visualizer: VisualizerElement, pass: PlaybackPass): void {
  visualizer.dataset.playbackStartMs = String(Math.round(pass.startMs));
  visualizer.dataset.playbackEndMs = String(Math.round(pass.endMs));
  visualizer.dataset.playbackRegionMode = pass.regionMode;
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

function readStoredMs(rawValue: string | undefined, fallbackMs: number): number {
  if (!rawValue) return fallbackMs;
  const value = Number(rawValue);
  return Number.isFinite(value) ? value : fallbackMs;
}

function currentProgressMs(visualizer: VisualizerElement): number | null {
  const planned = liveProgressMs(visualizer);
  return planned !== null ? planned : Number(visualizer.dataset.progressMs || visualizer.dataset.cursorMs || "0");
}
