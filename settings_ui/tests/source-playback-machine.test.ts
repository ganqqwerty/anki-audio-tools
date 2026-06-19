import { describe, expect, it } from "vitest";

import {
  initialSourcePlaybackState,
  transitionSourcePlayback,
  type SourcePlaybackEffect,
  type SourcePlaybackRequest,
  type SourcePlaybackState,
} from "../src/editor-inline/source-playback-machine.js";

const request: SourcePlaybackRequest = {
  cursorMs: 120,
  endMs: 900,
  loop: false,
  ord: 0,
  regionMode: "full",
  repeatPauseMs: 0,
  source: "user",
};

function effectTypes(effects: SourcePlaybackEffect[]): SourcePlaybackEffect["type"][] {
  return effects.map((effect) => effect.type);
}

function loading(
  pendingStart: Extract<SourcePlaybackState, { kind: "loading_metadata" }>["pendingStart"] = null,
): SourcePlaybackState {
  return {
    cursorMs: 0,
    kind: "loading_metadata",
    pendingStart,
    sourceFilename: "clip.mp3",
  };
}

function ready(overrides: Partial<Extract<SourcePlaybackState, { kind: "ready" }>> = {}): SourcePlaybackState {
  return {
    cursorMs: 0,
    durationMs: 1000,
    kind: "ready",
    sourceFilename: "clip.mp3",
    ...overrides,
  };
}

function playing(overrides: Partial<Extract<SourcePlaybackState, { kind: "playing" }>["request"]> = {}): SourcePlaybackState {
  return {
    durationMs: 1000,
    kind: "playing",
    request: { ...request, ...overrides },
    sourceFilename: "clip.mp3",
  };
}

describe("source playback machine", () => {
  it("defers user play while metadata is loading", () => {
    const result = transitionSourcePlayback(loading(), { type: "UserPlayRequested", request });

    expect(result.state).toEqual({
      cursorMs: request.cursorMs,
      kind: "loading_metadata",
      pendingStart: { request, source: "user" },
      sourceFilename: "clip.mp3",
    });
    expect(effectTypes(result.effects)).toEqual(["PublishPlaybackState", "LogPlaybackTelemetry"]);
  });

  it("starts immediately when metadata is already available after source configuration", () => {
    const configured = transitionSourcePlayback(initialSourcePlaybackState(), {
      cursorMs: 0,
      sourceFilename: "clip.mp3",
      type: "SourceConfigured",
    });
    expect(effectTypes(configured.effects)).toEqual([
      "ConfigureAudioSource",
      "ProbeAudioMetadata",
      "StartMetadataTimer",
      "PublishPlaybackState",
    ]);

    const queued = transitionSourcePlayback(configured.state, { type: "UserPlayRequested", request });
    const started = transitionSourcePlayback(queued.state, { durationMs: 1000, type: "MetadataLoaded" });

    expect(started.state).toMatchObject({ kind: "starting", request });
    expect(effectTypes(started.effects)).toEqual([
      "ClearMetadataTimer",
      "SeekAudio",
      "PlayAudio",
      "PublishPlaybackState",
    ]);
  });

  it("starts pending user playback after metadata loads", () => {
    const result = transitionSourcePlayback(
      loading({ request, source: "user" }),
      { durationMs: 1000, type: "MetadataLoaded" },
    );

    expect(result.state).toMatchObject({ durationMs: 1000, kind: "starting", request });
    expect(result.effects).toContainEqual({ cursorMs: request.cursorMs, type: "SeekAudio" });
    expect(effectTypes(result.effects)).toContain("PlayAudio");
  });

  it("starts pending post-edit autoplay after metadata loads", () => {
    const postEditRequest: SourcePlaybackRequest = { ...request, source: "post_edit" };
    const result = transitionSourcePlayback(
      loading({ request: postEditRequest, source: "post_edit" }),
      { durationMs: 1000, type: "MetadataLoaded" },
    );

    expect(result.state).toMatchObject({ kind: "starting", request: postEditRequest });
    expect(effectTypes(result.effects)).toEqual([
      "ClearMetadataTimer",
      "SeekAudio",
      "PlayAudio",
      "PublishPlaybackState",
    ]);
  });

  it("fails without native fallback when metadata times out", () => {
    const result = transitionSourcePlayback(loading(), { type: "MetadataTimeout" });

    expect(result.state).toEqual({
      cursorMs: 0,
      kind: "failed",
      reason: "metadata_timeout",
      sourceFilename: "clip.mp3",
    });
    expect(effectTypes(result.effects)).toEqual([
      "ClearMetadataTimer",
      "PublishPlaybackState",
      "ShowPlaybackStatus",
      "LogPlaybackTelemetry",
    ]);
  });

  it("moves ready to starting to playing for normal playback", () => {
    const starting = transitionSourcePlayback(ready(), { type: "UserPlayRequested", request });
    expect(starting.state).toMatchObject({ kind: "starting", request });
    expect(effectTypes(starting.effects)).toEqual(["SeekAudio", "PlayAudio", "PublishPlaybackState"]);

    const started = transitionSourcePlayback(starting.state, { type: "PlayResolved" });
    expect(started.state).toMatchObject({ kind: "playing", request });
    expect(effectTypes(started.effects)).toEqual(["PublishPlaybackState", "ShowPlaybackStatus"]);
  });

  it("pauses and resumes through explicit events", () => {
    const paused = transitionSourcePlayback(playing(), { cursorMs: 375, type: "PauseRequested" });
    expect(paused.state).toMatchObject({ kind: "paused", pausedAtMs: 375 });
    expect(effectTypes(paused.effects)).toEqual(["PauseAudio", "PublishPlaybackState", "ShowPlaybackStatus"]);

    const resumed = transitionSourcePlayback(paused.state, { type: "ResumeRequested" });
    expect(resumed.state).toMatchObject({ kind: "starting", request: { ...request, cursorMs: 375 } });
    expect(resumed.effects).toContainEqual({ cursorMs: 375, type: "SeekAudio" });
    expect(effectTypes(resumed.effects)).toContain("PlayAudio");
  });

  it("moves playing to repeat_waiting when a loop boundary is reached with a pause", () => {
    const result = transitionSourcePlayback(
      playing({ loop: true, repeatPauseMs: 250 }),
      { cursorMs: 900, type: "BoundaryReached" },
    );

    expect(result.state).toMatchObject({ kind: "repeat_waiting", resumeAtMs: request.cursorMs });
    expect(result.effects).toContainEqual({ pauseMs: 250, type: "StartRepeatTimer" });
    expect(effectTypes(result.effects)).toEqual(["StopAudio", "StartRepeatTimer", "PublishPlaybackState"]);
  });

  it("starts the next loop when repeat delay elapses", () => {
    const repeatWaiting: SourcePlaybackState = {
      durationMs: 1000,
      kind: "repeat_waiting",
      request: { ...request, loop: true, repeatPauseMs: 250 },
      resumeAtMs: request.cursorMs,
      sourceFilename: "clip.mp3",
    };

    const result = transitionSourcePlayback(repeatWaiting, { type: "RepeatDelayElapsed" });

    expect(result.state).toMatchObject({ kind: "starting", request: repeatWaiting.request });
    expect(effectTypes(result.effects)).toEqual(["SeekAudio", "PlayAudio", "PublishPlaybackState"]);
  });

  it("fails without native fallback when audio.play is rejected", () => {
    const result = transitionSourcePlayback(
      { durationMs: 1000, kind: "starting", request, sourceFilename: "clip.mp3" },
      { cursorMs: 120, reason: "audio_play_rejected", type: "PlayRejected" },
    );

    expect(result.state).toEqual({
      cursorMs: 120,
      kind: "failed",
      reason: "audio_play_rejected",
      sourceFilename: "clip.mp3",
    });
    expect(effectTypes(result.effects)).toEqual([
      "StopAudio",
      "PublishPlaybackState",
      "ShowPlaybackStatus",
      "LogPlaybackTelemetry",
    ]);
  });

  it("fails without native fallback on audio error or seek failure", () => {
    const audioError = transitionSourcePlayback(playing(), {
      cursorMs: 400,
      reason: "audio_error",
      type: "AudioError",
    });
    expect(audioError.state).toMatchObject({ kind: "failed", reason: "audio_error" });
    expect(effectTypes(audioError.effects)).toEqual([
      "StopAudio",
      "ClearMetadataTimer",
      "ClearRepeatTimer",
      "PublishPlaybackState",
      "LogPlaybackTelemetry",
    ]);

    const seekFailed = transitionSourcePlayback(ready(), {
      cursorMs: 300,
      reason: "audio_seek_failed",
      type: "SeekFailed",
    });
    expect(seekFailed.state).toMatchObject({ kind: "failed", reason: "audio_seek_failed" });
    expect(effectTypes(seekFailed.effects)).toContain("StopAudio");
  });

  it("clears timers and stops audio on runtime dispose", () => {
    const result = transitionSourcePlayback(playing(), { type: "RuntimeDisposed" });

    expect(result.state).toEqual({
      cursorMs: request.cursorMs,
      kind: "unconfigured",
      reason: "audio_src_missing",
    });
    expect(effectTypes(result.effects)).toEqual([
      "StopAudio",
      "ClearMetadataTimer",
      "ClearRepeatTimer",
      "PublishPlaybackState",
    ]);
  });
});
