import { readFieldState } from "./field-state-store.js";
import { logger } from "./logger.js";
import { audioClockTelemetryFor } from "./playback-audio-telemetry.js";
import {
  choosePlaybackEngine,
  type PlaybackEngineDecision,
} from "./playback-engine-decision.js";
import { effectivePlaybackRegion } from "./selection-controller.js";
import type { VisualizerElement } from "./types.js";

function fieldOrd(visualizer: VisualizerElement): number {
  return Number(visualizer.dataset.aqeFieldOrd || "0");
}

export function playbackEngineDecisionFor(visualizer: VisualizerElement | null): PlaybackEngineDecision {
  if (!visualizer) {
    return choosePlaybackEngine({
      activeEngine: "",
      audioClockReady: false,
      graphDurationMs: 0,
      graphHasTrack: false,
      htmlAudioReadinessFailed: true,
      htmlAudioReadinessReason: "audio_element_missing",
      htmlAudioReadinessState: "missing",
      htmlAudioReadinessTransient: false,
      playbackState: "stopped",
      regionMode: "full",
      repeat: false,
      visualizerPresent: false,
    });
  }
  const state = readFieldState(fieldOrd(visualizer));
  const region = effectivePlaybackRegion(visualizer);
  const telemetry = audioClockTelemetryFor(visualizer);
  return choosePlaybackEngine({
    activeEngine: state.playback.engine,
    audioClockReady: telemetry.audioClockReady,
    graphDurationMs: state.graph.durationMs,
    graphHasTrack: state.graph.hasTrack,
    htmlAudioReadinessFailed: telemetry.htmlAudioReadinessFailed,
    htmlAudioReadinessReason: telemetry.htmlAudioReadinessReason,
    htmlAudioReadinessState: telemetry.htmlAudioReadinessState,
    htmlAudioReadinessTransient: telemetry.htmlAudioReadinessTransient,
    playbackState: state.playback.state,
    regionMode: region.mode,
    repeat: state.playback.repeat,
    visualizerPresent: true,
  });
}

export function playbackTelemetryContext(
  visualizer: VisualizerElement | null,
  decision: PlaybackEngineDecision,
  extra: Record<string, unknown> = {},
): Record<string, unknown> {
  if (!visualizer) {
    return {
      engine: decision.engine,
      reason: decision.reason,
      ...audioClockTelemetryFor(null),
      ...extra,
    };
  }
  const state = readFieldState(fieldOrd(visualizer));
  const region = effectivePlaybackRegion(visualizer);
  return {
    activeEngine: state.playback.engine,
    cursorMs: state.cursor.ms,
    durationMs: state.graph.durationMs,
    engine: decision.engine,
    graphHasTrack: state.graph.hasTrack,
    ord: state.ord,
    playbackState: state.playback.state,
    reason: decision.reason,
    regionMode: region.mode,
    repeat: state.playback.repeat,
    sourceFilename: state.sourceFilename,
    ...audioClockTelemetryFor(visualizer),
    ...extra,
  };
}

export function logPlaybackEngineDecision(
  trigger: string,
  visualizer: VisualizerElement | null,
  decision: PlaybackEngineDecision,
  extra: Record<string, unknown> = {},
): void {
  logger.debug("playback.engine_selected", playbackTelemetryContext(visualizer, decision, { trigger, ...extra }));
}

export function postEditPlaybackStartContext(ord: number, visualizer: VisualizerElement): Record<string, unknown> {
  const state = readFieldState(fieldOrd(visualizer));
  return {
    audioClockReady: audioClockTelemetryFor(visualizer).audioClockReady,
    engine: playbackEngineDecisionFor(visualizer).engine,
    graphBusy: state.graph.busy ? "true" : "",
    hasTrack: state.graph.hasTrack ? "true" : "",
    ord,
    playbackState: state.playback.state,
    repeatEnabled: state.playback.repeat,
    sourceFilename: state.sourceFilename,
  };
}
