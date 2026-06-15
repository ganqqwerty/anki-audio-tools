import {
  playbackProgressPlan,
  progressMsForPlan,
} from "./playback-progress-clock.js";
import type { VisualizerElement } from "./types.js";
import {
  startPlaybackCursorTransition,
  stopPlaybackCursorTransition,
} from "./visualizer-renderer.js";
import { readFieldState, writeFieldState, setCachedProgressMs } from "./field-state-store.js";
import {
  readRepeatPauseSecondsRuntime,
  setPlaybackClockRuntime,
} from "./visualizer-runtime-state.js";

function fieldOrd(v: VisualizerElement): number {
  return Number(v.dataset.aqeFieldOrd || "0");
}

export function startPlaybackPlan(visualizer: VisualizerElement, startMs: number, endMs: number): void {
  const nowMs = performance.now();
  const plan = playbackProgressPlan(startMs, endMs, nowMs);
  visualizer.__aqePlaybackGeneration = (visualizer.__aqePlaybackGeneration ?? 0) + 1;
  visualizer.__aqePlaybackPlan = plan;
  visualizer.__aqeLiveProgressMs = Math.round(plan.startMs);
  delete visualizer.__aqeCursorPaintedAtMs;
  delete visualizer.__aqeCursorTextPaintedAtMs;
  setPlaybackClockRuntime(visualizer, plan.startMs, nowMs);
  const ord = fieldOrd(visualizer);
  writeFieldState(ord, {
    ...readFieldState(ord),
    cursor: { ...readFieldState(ord).cursor, progressMs: Math.round(plan.startMs) },
  });
  startPlaybackCursorTransition(visualizer, plan.startMs, plan.endMs);
}

export function liveProgressMs(
  visualizer: VisualizerElement,
  nowMs: number = performance.now(),
): number | null {
  const plan = visualizer.__aqePlaybackPlan;
  const ord = fieldOrd(visualizer);
  if (!plan || readFieldState(ord).playback.state !== "playing") return null;
  const progressMs = progressMsForPlan(plan, nowMs);
  visualizer.__aqeLiveProgressMs = Math.round(progressMs);
  setCachedProgressMs(ord, progressMs, visualizer);
  return progressMs;
}

export function clearPlaybackPlan(visualizer: VisualizerElement): void {
  delete visualizer.__aqePlaybackPlan;
  delete visualizer.__aqeLiveProgressMs;
  delete visualizer.__aqeCursorPaintedAtMs;
  delete visualizer.__aqeCursorTextPaintedAtMs;
  stopPlaybackCursorTransition(visualizer);
}

export function invalidatePlaybackFrames(visualizer: VisualizerElement): void {
  visualizer.__aqePlaybackGeneration = (visualizer.__aqePlaybackGeneration ?? 0) + 1;
}

export function repeatPauseDelayMs(visualizer: VisualizerElement): number {
  const seconds = readRepeatPauseSecondsRuntime(visualizer);
  if (!Number.isFinite(seconds) || seconds <= 0) return 0;
  return Math.round(Math.min(10, seconds) * 1000);
}

export function clampProgressMs(visualizer: VisualizerElement, ms: number): number {
  const durationMs = readFieldState(fieldOrd(visualizer)).graph.durationMs;
  return Math.max(0, Math.min(Number(ms) || 0, durationMs || 0));
}
