import { repeatEnabledFor } from "./actions-audio-clock.js";
import { currentProgressMs } from "./playback-controller.js";
import type { PlaybackReadinessDecision } from "./playback-engine-decision.js";
import { planPlaybackRequest, type PlaybackSnapshot } from "./playback-model.js";
import { effectivePlaybackRegion } from "./selection-controller.js";
import type { PlaybackRequest, VisualizerElement } from "./types.js";
import { readFieldState } from "./field-state-store.js";
import { readVisualizerTargetDurationMs } from "./visualizer-state.js";

export function playbackRequestFromSnapshot(
  visualizer: VisualizerElement,
  ord: number,
  decision: PlaybackReadinessDecision,
): PlaybackRequest {
  return planPlaybackRequest(playbackSnapshotFor(visualizer, ord, decision));
}

function playbackSnapshotFor(
  visualizer: VisualizerElement,
  ord: number,
  decision: PlaybackReadinessDecision,
): PlaybackSnapshot {
  const s = readFieldState(ord);
  return {
    anchorMs: s.cursor.anchorMs,
    currentProgressMs: currentProgressMs(visualizer),
    cursorMs: s.cursor.ms,
    durationMs: readVisualizerTargetDurationMs(visualizer),
    engine: decision.engine,
    ord,
    playbackState: s.playback.state,
    region: effectivePlaybackRegion(visualizer),
    repeat: repeatEnabledFor(visualizer),
    resumeRequiresRestart: s.playback.resumeRequiresRestart,
  };
}
