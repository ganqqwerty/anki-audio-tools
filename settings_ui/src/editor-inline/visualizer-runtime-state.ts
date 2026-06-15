import { visualizerForOrd } from "./dom-selectors.js";
import { normalizeTimeViewport, type TimeViewport } from "./time-viewport.js";
import type { PlaybackPass } from "./playback-model.js";
import type { VisualizerElement } from "./types.js";

export interface PlaybackClockRuntimeState {
  playStartedAt: number;
  playStartMs: number;
}

export interface VisualizerRuntimeState {
  learnerDurationMs: number;
  playbackLoop: boolean;
  playbackResetCursorMs: number;
  preserveStatusOnPlaybackEnd: boolean;
  repeatPauseSeconds: number;
  repeatPauseWaiting: boolean;
  targetDurationMs: number;
  viewportEndMs: number | null;
  viewportStartMs: number;
  playbackClock: PlaybackClockRuntimeState;
}

const runtimeStates: Map<number, VisualizerRuntimeState> = new Map();

export function emptyVisualizerRuntimeState(): VisualizerRuntimeState {
  return {
    learnerDurationMs: 0,
    playbackClock: {
      playStartedAt: 0,
      playStartMs: 0,
    },
    playbackLoop: false,
    playbackResetCursorMs: 0,
    preserveStatusOnPlaybackEnd: false,
    repeatPauseSeconds: 0,
    repeatPauseWaiting: false,
    targetDurationMs: 0,
    viewportEndMs: null,
    viewportStartMs: 0,
  };
}

export function fieldOrdForVisualizer(visualizer: VisualizerElement): number {
  return Number(visualizer.dataset.aqeFieldOrd || "0");
}

export function readVisualizerRuntimeState(ord: number): VisualizerRuntimeState {
  return runtimeStates.get(ord) ?? emptyVisualizerRuntimeState();
}

function writeVisualizerRuntimeState(
  ord: number,
  patch: Partial<VisualizerRuntimeState>,
): VisualizerRuntimeState {
  const previous = readVisualizerRuntimeState(ord);
  const next: VisualizerRuntimeState = {
    ...previous,
    ...patch,
    playbackClock: {
      ...previous.playbackClock,
      ...patch.playbackClock,
    },
  };
  runtimeStates.set(ord, next);
  return next;
}

export function resetVisualizerRuntimeState(ord: number, visualizer: VisualizerElement | null = visualizerForOrd(ord)): VisualizerRuntimeState {
  const next = emptyVisualizerRuntimeState();
  runtimeStates.set(ord, next);
  projectVisualizerRuntimeState(ord, next, visualizer);
  return next;
}

export function clearVisualizerRuntimeStates(): void {
  runtimeStates.clear();
}

function projectVisualizerRuntimeState(
  ord: number,
  state: VisualizerRuntimeState = readVisualizerRuntimeState(ord),
  visualizer: VisualizerElement | null = visualizerForOrd(ord),
): void {
  if (!visualizer) return;
  visualizer.dataset.targetDurationMs = String(Math.round(state.targetDurationMs));
  visualizer.dataset.learnerDurationMs = String(Math.round(state.learnerDurationMs));
  visualizer.dataset.playbackResetCursorMs = String(Math.round(state.playbackResetCursorMs));
  visualizer.dataset.playbackLoop = state.playbackLoop ? "true" : "false";
  visualizer.dataset.playStartedAt = String(state.playbackClock.playStartedAt);
  visualizer.dataset.playStartMs = String(Math.round(state.playbackClock.playStartMs));
  visualizer.dataset.repeatPauseSeconds = String(state.repeatPauseSeconds);
  visualizer.dataset.repeatPauseWaiting = state.repeatPauseWaiting ? "true" : "false";
  visualizer.dataset.preserveStatusOnPlaybackEnd = state.preserveStatusOnPlaybackEnd ? "true" : "false";
  visualizer.dataset.viewportStartMs = String(Math.round(state.viewportStartMs));
  if (state.viewportEndMs === null) {
    delete visualizer.dataset.viewportEndMs;
  } else {
    visualizer.dataset.viewportEndMs = String(Math.round(state.viewportEndMs));
  }
}

export function setTargetDurationMsForVisualizer(
  visualizer: VisualizerElement,
  targetDurationMs: number,
): number {
  const ord = fieldOrdForVisualizer(visualizer);
  const next = Math.max(0, Math.round(Number(targetDurationMs) || 0));
  const state = writeVisualizerRuntimeState(ord, { targetDurationMs: next });
  projectVisualizerRuntimeState(ord, state, visualizer);
  return next;
}

export function readTargetDurationMsForVisualizer(visualizer: VisualizerElement, fallbackDurationMs: number): number {
  const targetDurationMs = readVisualizerRuntimeState(fieldOrdForVisualizer(visualizer)).targetDurationMs;
  return targetDurationMs > 0 ? targetDurationMs : fallbackDurationMs;
}

export function setLearnerDurationMsForVisualizer(
  visualizer: VisualizerElement,
  learnerDurationMs: number,
): number {
  const ord = fieldOrdForVisualizer(visualizer);
  const next = Math.max(0, Math.round(Number(learnerDurationMs) || 0));
  const state = writeVisualizerRuntimeState(ord, { learnerDurationMs: next });
  projectVisualizerRuntimeState(ord, state, visualizer);
  return next;
}

export function readLearnerDurationMsForVisualizer(visualizer: VisualizerElement): number {
  return readVisualizerRuntimeState(fieldOrdForVisualizer(visualizer)).learnerDurationMs;
}

export function readRuntimeTimeViewport(visualizer: VisualizerElement, durationMs: number): TimeViewport {
  const state = readVisualizerRuntimeState(fieldOrdForVisualizer(visualizer));
  return normalizeTimeViewport(
    state.viewportStartMs,
    state.viewportEndMs ?? durationMs,
    durationMs,
  );
}

export function writeRuntimeTimeViewport(visualizer: VisualizerElement, viewport: TimeViewport): TimeViewport {
  const normalized = normalizeTimeViewport(viewport.startMs, viewport.endMs, viewport.durationMs);
  const ord = fieldOrdForVisualizer(visualizer);
  const state = writeVisualizerRuntimeState(ord, {
    viewportEndMs: Math.round(normalized.endMs),
    viewportStartMs: Math.round(normalized.startMs),
  });
  projectVisualizerRuntimeState(ord, state, visualizer);
  return normalized;
}

export function setPlaybackPassRuntime(visualizer: VisualizerElement, pass: PlaybackPass): void {
  const ord = fieldOrdForVisualizer(visualizer);
  const state = writeVisualizerRuntimeState(ord, {
    playbackLoop: pass.loop,
    playbackResetCursorMs: Math.round(pass.resetCursorMs),
  });
  projectVisualizerRuntimeState(ord, state, visualizer);
}

export function setPlaybackLoopRuntime(visualizer: VisualizerElement, loop: boolean): void {
  const ord = fieldOrdForVisualizer(visualizer);
  const state = writeVisualizerRuntimeState(ord, { playbackLoop: loop });
  projectVisualizerRuntimeState(ord, state, visualizer);
}

export function readPlaybackPassRuntime(
  visualizer: VisualizerElement,
  fallbackResetCursorMs: number,
): { loop: boolean; resetCursorMs: number } {
  const state = readVisualizerRuntimeState(fieldOrdForVisualizer(visualizer));
  const resetCursorMs = Number.isFinite(state.playbackResetCursorMs)
    ? state.playbackResetCursorMs
    : Math.round(fallbackResetCursorMs);
  return {
    loop: state.playbackLoop,
    resetCursorMs,
  };
}

export function setPlaybackResetCursorMsRuntime(visualizer: VisualizerElement, resetCursorMs: number): number {
  const ord = fieldOrdForVisualizer(visualizer);
  const next = Math.max(0, Math.round(Number(resetCursorMs) || 0));
  const state = writeVisualizerRuntimeState(ord, { playbackResetCursorMs: next });
  projectVisualizerRuntimeState(ord, state, visualizer);
  return next;
}

export function setPlaybackClockRuntime(
  visualizer: VisualizerElement,
  playStartMs: number,
  playStartedAt: number = performance.now(),
): void {
  const ord = fieldOrdForVisualizer(visualizer);
  const state = writeVisualizerRuntimeState(ord, {
    playbackClock: {
      playStartedAt,
      playStartMs: Math.round(playStartMs),
    },
  });
  projectVisualizerRuntimeState(ord, state, visualizer);
}

export function readPlaybackClockRuntime(visualizer: VisualizerElement): PlaybackClockRuntimeState {
  return readVisualizerRuntimeState(fieldOrdForVisualizer(visualizer)).playbackClock;
}

export function setRepeatPauseSecondsRuntime(visualizer: VisualizerElement, seconds: number): number {
  const ord = fieldOrdForVisualizer(visualizer);
  const next = Math.max(0, Math.min(10, Number(seconds) || 0));
  const state = writeVisualizerRuntimeState(ord, { repeatPauseSeconds: next });
  projectVisualizerRuntimeState(ord, state, visualizer);
  return next;
}

export function readRepeatPauseSecondsRuntime(visualizer: VisualizerElement): number {
  return readVisualizerRuntimeState(fieldOrdForVisualizer(visualizer)).repeatPauseSeconds;
}

export function setRepeatPauseWaitingRuntime(visualizer: VisualizerElement, waiting: boolean): void {
  const ord = fieldOrdForVisualizer(visualizer);
  const state = writeVisualizerRuntimeState(ord, { repeatPauseWaiting: waiting });
  projectVisualizerRuntimeState(ord, state, visualizer);
}

export function isRepeatPauseWaitingRuntime(visualizer: VisualizerElement): boolean {
  return readVisualizerRuntimeState(fieldOrdForVisualizer(visualizer)).repeatPauseWaiting;
}

export function setPreserveStatusOnPlaybackEndRuntime(visualizer: VisualizerElement, preserve: boolean): void {
  const ord = fieldOrdForVisualizer(visualizer);
  const state = writeVisualizerRuntimeState(ord, { preserveStatusOnPlaybackEnd: preserve });
  projectVisualizerRuntimeState(ord, state, visualizer);
}

export function preserveStatusOnPlaybackEndRuntime(visualizer: VisualizerElement): boolean {
  return readVisualizerRuntimeState(fieldOrdForVisualizer(visualizer)).preserveStatusOnPlaybackEnd;
}
