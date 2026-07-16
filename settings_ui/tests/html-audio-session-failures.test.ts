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
  function audioErrorTransition(
    sourceFilename: string,
    mediaErrorCode: number | null,
    requestSource: "user" | "post_edit" = "user",
    mediaResponseStatus: number | null = 200,
  ) {
    let state: HtmlAudioSessionState = initialHtmlAudioSessionState(0);
    state = transitionHtmlAudioSession(state, {
      cursorMs: 0,
      source: { ...source, sourceFilename },
      type: "SourceConfigured",
    }).state;
    state = transitionHtmlAudioSession(state, { durationMs: 1000, type: "MetadataLoaded" }).state;
    state = transitionHtmlAudioSession(state, {
      request: { ...request, cursorMs: 250, source: requestSource },
      type: "StartRequested",
    }).state;

    return transitionHtmlAudioSession(state, {
      cursorMs: 250,
      mediaErrorCode,
      mediaResponseStatus,
      reason: "audio_error",
      type: "AudioError",
    });
  }

  it.each([3, 4])("offers MP3 recovery for non-MP3 source media error code %s", (mediaErrorCode) => {
    const transition = audioErrorTransition("clip one.m4a", mediaErrorCode);

    expect(transition.state).toMatchObject({
      cursorMs: 250,
      kind: "failed",
      mediaErrorCode,
      mediaResponseStatus: 200,
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
      recovery: {
        fieldOrd: 0,
        kind: "convert_to_mp3",
        sourceFilename: "clip one.m4a",
      },
      statusCode: "AQE-PLAYBACK-002",
      statusKey: "editor.status.browser_audio_format_unsupported",
      type: "ShowPlaybackStatus",
    });
    expect(JSON.stringify(transition.effects)).not.toContain("AQE-MEDIA-002");
  });

  it.each([404, 410])("keeps missing media as AQE-MEDIA-002 for route status %s", (mediaResponseStatus) => {
    const transition = audioErrorTransition("missing.m4a", 4, "user", mediaResponseStatus);
    const status = transition.effects.find((effect) => effect.type === "ShowPlaybackStatus");

    expect(status).toEqual({
      kind: "error",
      statusCode: "AQE-MEDIA-002",
      statusKey: "editor.status.referenced_audio_missing",
      type: "ShowPlaybackStatus",
    });
    expect(JSON.stringify(transition.effects)).not.toContain("convert_to_mp3");
    expect(JSON.stringify(transition.effects)).not.toContain("AQE-PLAYBACK-002");
  });

  it.each([1, 2, null])("does not offer conversion for media error code %s", (mediaErrorCode) => {
    const transition = audioErrorTransition("clip one.m4a", mediaErrorCode);
    const status = transition.effects.find((effect) => effect.type === "ShowPlaybackStatus");

    expect(status).toEqual({
      statusKey: "editor.status.browser_audio_unavailable",
      type: "ShowPlaybackStatus",
    });
    expect(JSON.stringify(transition.effects)).not.toContain("convert_to_mp3");
    expect(JSON.stringify(transition.effects)).not.toContain("AQE-MEDIA-002");
  });

  it("does not offer same-format recovery for an MP3 source", () => {
    const transition = audioErrorTransition("already.mp3", 4);
    const status = transition.effects.find((effect) => effect.type === "ShowPlaybackStatus");

    expect(status).toEqual({
      kind: "error",
      statusCode: "AQE-PLAYBACK-002",
      statusKey: "editor.status.browser_audio_format_unsupported",
      type: "ShowPlaybackStatus",
    });
    expect(JSON.stringify(transition.effects)).not.toContain("convert_to_mp3");
  });

  it("keeps post-edit success separate from an actionable playback warning", () => {
    const transition = audioErrorTransition("edited.m4a", 4, "post_edit");

    expect(transition.effects).toContainEqual({
      recovery: {
        fieldOrd: 0,
        kind: "convert_to_mp3",
        sourceFilename: "edited.m4a",
      },
      statusCode: "AQE-PLAYBACK-002",
      statusKey: "editor.status.browser_audio_format_unsupported_after_edit",
      type: "ShowPostEditPlaybackWarning",
    });
    expect(transition.effects.some((effect) => effect.type === "ShowPlaybackStatus")).toBe(false);
  });
});
