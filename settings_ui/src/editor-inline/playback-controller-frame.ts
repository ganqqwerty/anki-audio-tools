import { clearRepeatPauseCountdownOverlay } from "./graph-countdown-overlay.js";
import {
  clearPlaybackPlan,
  invalidatePlaybackFrames,
} from "./playback-plan-state.js";
import type { VisualizerElement } from "./types.js";

export function clearPlaybackFrame(visualizer: VisualizerElement): void {
  if (visualizer.__aqePlaybackTimer) {
    window.cancelAnimationFrame(visualizer.__aqePlaybackTimer);
    visualizer.__aqePlaybackTimer = null;
  }
  clearRepeatPauseTimer(visualizer);
  clearPlaybackPlan(visualizer);
  invalidatePlaybackFrames(visualizer);
}

export function clearRepeatPauseTimer(visualizer: VisualizerElement): void {
  if (visualizer.__aqeRepeatPauseTimer) {
    window.clearTimeout(visualizer.__aqeRepeatPauseTimer);
    visualizer.__aqeRepeatPauseTimer = null;
  }
  clearRepeatPauseCountdownOverlay(visualizer);
  visualizer.dataset.repeatPauseWaiting = "false";
}
