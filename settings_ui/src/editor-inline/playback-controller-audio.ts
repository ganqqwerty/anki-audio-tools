import { audioClockFor } from "./audio-clock.js";
import { liveProgressMs } from "./playback-plan-state.js";
import { readFieldState } from "./field-state-store.js";
import type { EditorFieldState } from "./field-state.js";
import type { VisualizerElement } from "./types.js";
import { readPlaybackClockRuntime } from "./visualizer-runtime-state.js";

function fieldState(visualizer: VisualizerElement): EditorFieldState {
  return readFieldState(Number(visualizer.dataset.aqeFieldOrd || "0"));
}

export function manualProgressMs(visualizer: VisualizerElement): number {
  const planned = liveProgressMs(visualizer);
  if (planned !== null) return planned;
  const s = fieldState(visualizer);
  const clock = readPlaybackClockRuntime(visualizer);
  const elapsed = performance.now() - clock.playStartedAt;
  return Math.min(s.graph.durationMs, clock.playStartMs + elapsed);
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
