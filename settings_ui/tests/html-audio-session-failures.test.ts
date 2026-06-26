import { describe, expect, it } from "vitest";

import {
  initialHtmlAudioSessionState,
  transitionHtmlAudioSession,
  type HtmlAudioSessionState,
} from "../src/editor-inline/html-audio-session-machine.js";

const source = {
  kind: "source" as const,
  sourceFilename: "clip one.mp3",
};

const request = {
  cursorMs: 0,
  endMs: 1000,
  loop: false,
  ord: 0,
  regionMode: "full" as const,
  source: "user" as const,
};

describe("html audio session failures", () => {
  it("reports source audio element errors as missing referenced media", () => {
    let state: HtmlAudioSessionState = initialHtmlAudioSessionState(0);
    state = transitionHtmlAudioSession(state, { cursorMs: 0, source, type: "SourceConfigured" }).state;
    state = transitionHtmlAudioSession(state, { durationMs: 1000, type: "MetadataLoaded" }).state;
    state = transitionHtmlAudioSession(state, {
      request: { ...request, cursorMs: 250 },
      type: "StartRequested",
    }).state;

    const transition = transitionHtmlAudioSession(state, {
      cursorMs: 250,
      reason: "audio_error",
      type: "AudioError",
    });

    expect(transition.state).toMatchObject({
      cursorMs: 250,
      kind: "failed",
      reason: "audio_error",
    });
    expect(transition.effects.map((effect) => effect.type)).toEqual([
      "ClearProgressFrame",
      "ClearRepeatTimer",
      "ClearMetadataTimer",
      "PauseAudio",
      "PublishPlaybackState",
      "ShowPlaybackStatus",
      "LogPlaybackTelemetry",
    ]);
    expect(transition.effects).toContainEqual({
      kind: "error",
      statusCode: "AQE-MEDIA-002",
      statusKey: "editor.status.referenced_audio_missing",
      type: "ShowPlaybackStatus",
    });
  });
});
