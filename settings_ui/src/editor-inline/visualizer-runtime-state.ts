import { visualizerForOrd } from "./dom-selectors.js";
import { normalizeTimeViewport, type TimeViewport } from "./time-viewport.js";
import type { VisualizerElement } from "./types.js";

export interface VisualizerRuntimeState {
  learnerDurationMs: number;
  repeatPauseSeconds: number;
  targetDurationMs: number;
  viewportEndMs: number | null;
  viewportStartMs: number;
}

const runtimeStates: Map<number, VisualizerRuntimeState> = new Map();

export function emptyVisualizerRuntimeState(): VisualizerRuntimeState {
  return {
    learnerDurationMs: 0,
    repeatPauseSeconds: 0,
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
  visualizer.dataset.repeatPauseSeconds = String(state.repeatPauseSeconds);
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
