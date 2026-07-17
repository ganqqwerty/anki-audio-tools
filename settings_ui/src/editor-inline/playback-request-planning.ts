import {
  readHtmlAudioTransportPosition,
  readHtmlAudioTransportSnapshot,
} from "./html-audio-session-controller.js";
import type { PlaybackReadinessDecision } from "./playback-engine-decision.js";
import { planPlaybackRequest, type PlaybackSnapshot } from "./playback-model.js";
import { effectivePlaybackRegion } from "./selection-controller.js";
import type { PlaybackRequest, VisualizerElement } from "./types.js";
import { readFieldState } from "./field-state-store.js";
import { readVisualizerTargetDurationMs } from "./visualizer-state.js";
import { editorPracticePlaybackState } from "./editor-practice-controller.js";

export function playbackRequestForVisualizer(
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
  const transport = readHtmlAudioTransportSnapshot(ord);
  const programPlaybackState = editorPracticePlaybackState(ord);
  const playbackState = programPlaybackState !== "stopped"
    ? programPlaybackState
    : transport.session.kind === "paused"
    ? "paused"
    : transport.active ? "playing" : "stopped";
  return {
    anchorMs: s.cursor.anchorMs,
    currentProgressMs: transport.active || transport.session.kind === "paused"
      ? readHtmlAudioTransportPosition(ord)
      : s.cursor.progressMs,
    cursorMs: s.cursor.ms,
    durationMs: readVisualizerTargetDurationMs(visualizer),
    engine: decision.engine,
    ord,
    playbackState,
    region: effectivePlaybackRegion(visualizer),
    repeat: s.playback.repeat,
    resumeRequiresRestart: s.playback.resumeRequiresRestart,
  };
}
