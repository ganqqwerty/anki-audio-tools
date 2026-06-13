import { audioClockFor } from "./audio-clock.js";
import { liveProgressMs } from "./playback-plan-state.js";
import { readFieldState } from "./field-state-store.js";
import type { EditorFieldState } from "./field-state.js";
import type { VisualizerElement } from "./types.js";

function fieldState(visualizer: VisualizerElement): EditorFieldState {
  return readFieldState(Number(visualizer.dataset.aqeFieldOrd || "0"));
}

export function manualProgressMs(visualizer: VisualizerElement): number {
  const planned = liveProgressMs(visualizer);
  if (planned !== null) return planned;
  const s = fieldState(visualizer);
  const elapsed = performance.now() - Number(visualizer.dataset.playStartedAt || "0");
  return Math.min(s.graph.durationMs, Number(visualizer.dataset.playStartMs || "0") + elapsed);
}

export function audioProgressMs(visualizer: VisualizerElement): number | null {
  const audio = audioClockFor(visualizer);
  if (!audio) return null;
  const s = fieldState(visualizer);
  return Math.min(s.graph.durationMs, (Number(audio.currentTime) || 0) * 1000);
}

export function currentProgressMs(visualizer: VisualizerElement): number | null {
  const planned = liveProgressMs(visualizer);
  if (planned !== null) return planned;
  const s = fieldState(visualizer);
  return s.cursor.progressMs || s.cursor.ms;
}
