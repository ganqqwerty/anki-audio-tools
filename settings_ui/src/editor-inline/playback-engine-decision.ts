import type { PlaybackEngine, PlaybackRegionMode } from "./playback-state.js";
import type { PlaybackState } from "./types.js";
import type { HtmlAudioReadinessReason, HtmlAudioReadinessState } from "./audio-readiness.js";

export type PlaybackEngineSelectionReason =
  | "active_engine_html"
  | "audio_clock_not_ready"
  | "audio_clock_ready"
  | "audio_metadata_loading"
  | "audio_readiness_failed"
  | "no_graph_track_audio_clock_not_ready"
  | "no_graph_track_audio_loading"
  | "no_graph_track_audio_ready"
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
  htmlAudioReadinessFailed: boolean;
  htmlAudioReadinessReason: HtmlAudioReadinessReason;
  htmlAudioReadinessState: HtmlAudioReadinessState;
  htmlAudioReadinessTransient: boolean;
  playbackState: PlaybackState;
  regionMode: PlaybackRegionMode;
  repeat: boolean;
  visualizerPresent: boolean;
}

export interface PlaybackEngineDecision {
  engine: "html";
  reason: PlaybackEngineSelectionReason;
}

export function choosePlaybackEngine(input: PlaybackEngineDecisionInput): PlaybackEngineDecision {
  if (!input.visualizerPresent) {
    return { engine: "html", reason: "visualizer_missing" };
  }
  if (input.playbackState !== "stopped") {
    return { engine: "html", reason: "active_engine_html" };
  }
  if (input.regionMode === "selection" && input.repeat) {
    return { engine: "html", reason: "selected_repeat_requires_html" };
  }
  if (input.htmlAudioReadinessFailed) {
    return { engine: "html", reason: "audio_readiness_failed" };
  }
  if (!input.graphHasTrack) {
    if (input.audioClockReady) return { engine: "html", reason: "no_graph_track_audio_ready" };
    if (input.htmlAudioReadinessTransient) return { engine: "html", reason: "no_graph_track_audio_loading" };
    return { engine: "html", reason: "no_graph_track_audio_clock_not_ready" };
  }
  if (input.htmlAudioReadinessTransient) {
    return { engine: "html", reason: "audio_metadata_loading" };
  }
  return input.audioClockReady
    ? { engine: "html", reason: "audio_clock_ready" }
    : { engine: "html", reason: "audio_clock_not_ready" };
}
