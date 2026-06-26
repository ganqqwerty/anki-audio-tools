import type { PlaybackRegionMode } from "./playback-state.js";
import type { PlaybackState } from "./types.js";

export type PlaybackReadinessReason =
  | "active_engine_html"
  | "audio_clock_not_ready"
  | "audio_clock_ready"
  | "audio_metadata_loading"
  | "audio_readiness_failed"
  | "no_graph_track_audio_clock_not_ready"
  | "no_graph_track_audio_loading"
  | "no_graph_track_audio_ready"
  | "selected_repeat_requires_html"
  | "visualizer_missing";

export interface PlaybackReadinessDecisionInput {
  audioClockReady: boolean;
  graphHasTrack: boolean;
  htmlAudioReadinessFailed: boolean;
  htmlAudioReadinessTransient: boolean;
  playbackState: PlaybackState;
  regionMode: PlaybackRegionMode;
  repeat: boolean;
  visualizerPresent: boolean;
}

export interface PlaybackReadinessDecision {
  engine: "html";
  reason: PlaybackReadinessReason;
}

export function describeHtmlPlaybackReadiness(input: PlaybackReadinessDecisionInput): PlaybackReadinessDecision {
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
