import {
  playbackProgressPlan,
  progressMsForPlan,
} from "./playback-progress-clock.js";
import type { VisualizerElement } from "./types.js";
import {
  startPlaybackCursorTransition,
  stopPlaybackCursorTransition,
} from "./visualizer-renderer.js";

export function startPlaybackPlan(visualizer: VisualizerElement, startMs: number, endMs: number): void {
  const nowMs = performance.now();
  const plan = playbackProgressPlan(startMs, endMs, nowMs);
  visualizer.__aqePlaybackGeneration = (visualizer.__aqePlaybackGeneration ?? 0) + 1;
  visualizer.__aqePlaybackPlan = plan;
  visualizer.__aqeLiveProgressMs = Math.round(plan.startMs);
  delete visualizer.__aqeCursorPaintedAtMs;
  delete visualizer.__aqeCursorTextPaintedAtMs;
  visualizer.dataset.playStartedAt = String(nowMs);
  visualizer.dataset.playStartMs = String(Math.round(plan.startMs));
  visualizer.dataset.progressMs = String(Math.round(plan.startMs));
  startPlaybackCursorTransition(visualizer, plan.startMs, plan.endMs);
}

export function liveProgressMs(
  visualizer: VisualizerElement,
  nowMs: number = performance.now(),
): number | null {
  const plan = visualizer.__aqePlaybackPlan;
  if (!plan || visualizer.dataset.playbackState !== "playing") return null;
  const progressMs = progressMsForPlan(plan, nowMs);
  visualizer.__aqeLiveProgressMs = Math.round(progressMs);
  visualizer.dataset.progressMs = String(Math.round(progressMs));
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
  const seconds = Number(visualizer.dataset.repeatPauseSeconds || "0");
  if (!Number.isFinite(seconds) || seconds <= 0) return 0;
  return Math.round(Math.min(10, seconds) * 1000);
}

export function clampProgressMs(visualizer: VisualizerElement, ms: number): number {
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  return Math.max(0, Math.min(Number(ms) || 0, durationMs || 0));
}
