import { describe, expect, it } from "vitest";

import {
  choosePlaybackEngine,
  type PlaybackEngineDecisionInput,
} from "../src/editor-inline/playback-engine-decision.js";

const baseInput: PlaybackEngineDecisionInput = {
  activeEngine: "",
  audioClockReady: true,
  graphDurationMs: 1000,
  graphHasTrack: true,
  htmlAudioReadinessFailed: false,
  htmlAudioReadinessReason: "audio_ready",
  htmlAudioReadinessState: "ready",
  htmlAudioReadinessTransient: false,
  playbackState: "stopped",
  regionMode: "full",
  repeat: false,
  visualizerPresent: true,
};

describe("playback engine decision", () => {
  it("keeps the active playback engine while playback is not stopped", () => {
    expect(choosePlaybackEngine({
      ...baseInput,
      activeEngine: "native",
      playbackState: "playing",
    })).toEqual({ engine: "native", reason: "active_engine_native" });
    expect(choosePlaybackEngine({
      ...baseInput,
      activeEngine: "html",
      playbackState: "paused",
    })).toEqual({ engine: "html", reason: "active_engine_html" });
  });

  it("requires HTML playback for selected repeat", () => {
    expect(choosePlaybackEngine({
      ...baseInput,
      audioClockReady: false,
      regionMode: "selection",
      repeat: true,
    })).toEqual({ engine: "html", reason: "selected_repeat_requires_html" });
  });

  it("keeps transient loading on the HTML path instead of selecting native", () => {
    expect(choosePlaybackEngine({
      ...baseInput,
      audioClockReady: false,
      graphHasTrack: true,
      htmlAudioReadinessReason: "audio_metadata_loading",
      htmlAudioReadinessState: "loading_metadata",
      htmlAudioReadinessTransient: true,
    })).toEqual({ engine: "html", reason: "audio_metadata_loading" });
  });

  it("records native reasons for hard browser audio failures", () => {
    expect(choosePlaybackEngine({
      ...baseInput,
      audioClockReady: false,
      htmlAudioReadinessFailed: true,
      htmlAudioReadinessReason: "audio_error",
      htmlAudioReadinessState: "failed",
    })).toEqual({ engine: "native", reason: "audio_readiness_failed" });
  });

  it("uses HTML for hidden no-graph playback once metadata is ready", () => {
    expect(choosePlaybackEngine({
      ...baseInput,
      graphHasTrack: false,
      repeat: false,
    })).toEqual({ engine: "html", reason: "no_graph_track_audio_ready" });
  });
});
