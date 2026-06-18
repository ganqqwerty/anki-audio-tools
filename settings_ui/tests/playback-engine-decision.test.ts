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

  it("records why native is selected when graph-backed browser audio is not ready", () => {
    expect(choosePlaybackEngine({
      ...baseInput,
      audioClockReady: false,
      graphHasTrack: true,
    })).toEqual({ engine: "native", reason: "audio_clock_not_ready" });
  });

  it("records native reasons before graph playback can use browser audio", () => {
    expect(choosePlaybackEngine({
      ...baseInput,
      graphHasTrack: false,
      repeat: false,
    })).toEqual({ engine: "native", reason: "no_graph_track_repeat_disabled" });
    expect(choosePlaybackEngine({
      ...baseInput,
      graphDurationMs: 0,
      graphHasTrack: false,
      repeat: true,
    })).toEqual({ engine: "native", reason: "no_graph_track_duration_unknown" });
    expect(choosePlaybackEngine({
      ...baseInput,
      audioClockReady: false,
      graphHasTrack: false,
      repeat: true,
    })).toEqual({ engine: "native", reason: "no_graph_track_audio_clock_not_ready" });
  });
});
