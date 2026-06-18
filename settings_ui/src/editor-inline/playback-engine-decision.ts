import type { PlaybackEngine, PlaybackRegionMode } from "./playback-state.js";
import type { PlaybackState } from "./types.js";

export type PlaybackEngineSelectionReason =
  | "active_engine_html"
  | "active_engine_native"
  | "audio_clock_not_ready"
  | "audio_clock_ready"
  | "no_graph_track_audio_clock_not_ready"
  | "no_graph_track_duration_unknown"
  | "no_graph_track_repeat_audio_ready"
  | "no_graph_track_repeat_disabled"
  | "selected_repeat_requires_html"
  | "visualizer_missing";

export interface PlaybackEngineDecisionInput {
  activeEngine: PlaybackEngine;
  audioClockReady: boolean;
  graphDurationMs: number;
  graphHasTrack: boolean;
  playbackState: PlaybackState;
  regionMode: PlaybackRegionMode;
  repeat: boolean;
  visualizerPresent: boolean;
}

export interface PlaybackEngineDecision {
  engine: "html" | "native";
  reason: PlaybackEngineSelectionReason;
}

export function choosePlaybackEngine(input: PlaybackEngineDecisionInput): PlaybackEngineDecision {
  if (!input.visualizerPresent) {
    return { engine: "native", reason: "visualizer_missing" };
  }
  if (input.playbackState !== "stopped" && input.activeEngine === "html") {
    return { engine: "html", reason: "active_engine_html" };
  }
  if (input.playbackState !== "stopped" && input.activeEngine === "native") {
    return { engine: "native", reason: "active_engine_native" };
  }
  if (input.regionMode === "selection" && input.repeat) {
    return { engine: "html", reason: "selected_repeat_requires_html" };
  }
  if (!input.graphHasTrack) {
    if (!input.repeat) {
      return { engine: "native", reason: "no_graph_track_repeat_disabled" };
    }
    if (input.graphDurationMs <= 0) {
      return { engine: "native", reason: "no_graph_track_duration_unknown" };
    }
    return input.audioClockReady
      ? { engine: "html", reason: "no_graph_track_repeat_audio_ready" }
      : { engine: "native", reason: "no_graph_track_audio_clock_not_ready" };
  }
  return input.audioClockReady
    ? { engine: "html", reason: "audio_clock_ready" }
    : { engine: "native", reason: "audio_clock_not_ready" };
}
