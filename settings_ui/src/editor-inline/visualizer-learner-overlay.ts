import type { NormalizedProsodyTrack, VisualizerElement } from "./types.js";
import { readTargetDurationMsForVisualizer } from "./visualizer-runtime-state.js";

const DURATION_TOLERANCE_MS = 120;

export interface LearnerOverlayOptions {
  preserveLearnerOverlay?: boolean;
}

export function learnerTrackForReplacement(
  visualizer: VisualizerElement,
  track: NormalizedProsodyTrack,
  options: LearnerOverlayOptions,
): NormalizedProsodyTrack | undefined {
  if (options.preserveLearnerOverlay !== true) return undefined;
  const learner = visualizer.__aqeLearnerTrack;
  if (!learner) return undefined;
  const previousDurationMs = Number(
    visualizer.dataset.pendingLearnerOverlayTargetDurationMs
      || readTargetDurationMsForVisualizer(visualizer, 0)
      || "0",
  ) || 0;
  const nextDurationMs = track.durationMs || 0;
  if (previousDurationMs <= 0 || nextDurationMs <= 0) return undefined;
  return Math.abs(previousDurationMs - nextDurationMs) <= DURATION_TOLERANCE_MS ? learner : undefined;
}
