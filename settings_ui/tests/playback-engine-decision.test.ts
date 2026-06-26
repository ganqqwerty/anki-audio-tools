import { describe, expect, it } from "vitest";

import {
  describeHtmlPlaybackReadiness,
  type PlaybackReadinessDecisionInput,
} from "../src/editor-inline/playback-engine-decision.js";

const baseInput: PlaybackReadinessDecisionInput = {
  audioClockReady: true,
  graphHasTrack: true,
  htmlAudioReadinessFailed: false,
  htmlAudioReadinessTransient: false,
  playbackState: "stopped",
  regionMode: "full",
  repeat: false,
  visualizerPresent: true,
};

describe("playback readiness decision", () => {
  it("keeps active playback on the HTML path while playback is not stopped", () => {
    expect(describeHtmlPlaybackReadiness({
      ...baseInput,
      playbackState: "playing",
    })).toEqual({ engine: "html", reason: "active_engine_html" });
    expect(describeHtmlPlaybackReadiness({
      ...baseInput,
      playbackState: "paused",
    })).toEqual({ engine: "html", reason: "active_engine_html" });
  });

  it("requires HTML playback for selected repeat", () => {
    expect(describeHtmlPlaybackReadiness({
      ...baseInput,
      audioClockReady: false,
      regionMode: "selection",
      repeat: true,
    })).toEqual({ engine: "html", reason: "selected_repeat_requires_html" });
  });

  it("keeps transient loading on the HTML path", () => {
    expect(describeHtmlPlaybackReadiness({
      ...baseInput,
      audioClockReady: false,
      graphHasTrack: true,
      htmlAudioReadinessTransient: true,
    })).toEqual({ engine: "html", reason: "audio_metadata_loading" });
  });

  it("records hard browser audio failures as HTML-path failures", () => {
    expect(describeHtmlPlaybackReadiness({
      ...baseInput,
      audioClockReady: false,
      htmlAudioReadinessFailed: true,
    })).toEqual({ engine: "html", reason: "audio_readiness_failed" });
  });

  it("uses HTML for hidden no-graph playback once metadata is ready", () => {
    expect(describeHtmlPlaybackReadiness({
      ...baseInput,
      graphHasTrack: false,
      repeat: false,
    })).toEqual({ engine: "html", reason: "no_graph_track_audio_ready" });
  });
});
