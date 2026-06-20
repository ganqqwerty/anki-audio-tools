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

describe("html audio session machine", () => {
  it("owns source playback transitions from configured source to playing", () => {
    let state: HtmlAudioSessionState = initialHtmlAudioSessionState(0);

    let transition = transitionHtmlAudioSession(state, {
      cursorMs: 0,
      source,
      type: "SourceConfigured",
    });
    expect(transition.state).toMatchObject({
      kind: "loading",
      ord: 0,
      source,
    });
    expect(transition.effects).toContainEqual({
      sourceFilename: "clip one.mp3",
      type: "ConfigureAudioSource",
    });
    state = transition.state;

    transition = transitionHtmlAudioSession(state, {
      durationMs: 1000,
      type: "MetadataLoaded",
    });
    expect(transition.state).toMatchObject({
      durationMs: 1000,
      kind: "ready",
      source,
    });
    state = transition.state;

    transition = transitionHtmlAudioSession(state, {
      request,
      type: "StartRequested",
    });
    expect(transition.state).toMatchObject({
      durationMs: 1000,
      kind: "starting",
      request,
      source,
    });
    expect(transition.effects).toEqual([
      { cursorMs: 0, type: "SeekAudio" },
      { type: "PlayAudio" },
      { cursorMs: 0, endMs: 1000, type: "StartProgressFrame" },
      { status: "playing", type: "PublishPlaybackState" },
    ]);

    transition = transitionHtmlAudioSession(transition.state, {
      nowMs: 120,
      sourceFilename: "clip one.mp3",
      type: "PlayResolved",
    });
    expect(transition.state).toMatchObject({
      kind: "playing",
      startedAtMs: 120,
    });
    expect(transition.effects).toEqual([
      { status: "playing", type: "PublishPlaybackState" },
      { request, type: "QueueBackendPlayback" },
    ]);
  });

  it("starts playback when metadata loads after a start request during loading", () => {
    let state: HtmlAudioSessionState = initialHtmlAudioSessionState(0);

    state = transitionHtmlAudioSession(state, {
      cursorMs: 250,
      source,
      type: "SourceConfigured",
    }).state;

    state = transitionHtmlAudioSession(state, {
      request: { ...request, cursorMs: 250, endMs: 750 },
      type: "StartRequested",
    }).state;

    const transition = transitionHtmlAudioSession(state, {
      durationMs: 1000,
      type: "MetadataLoaded",
    });

    expect(transition.state).toMatchObject({
      durationMs: 1000,
      kind: "starting",
      request: { ...request, cursorMs: 250, endMs: 750 },
      source,
    });
    expect(transition.effects).toEqual([
      { type: "ClearMetadataTimer" },
      { cursorMs: 250, type: "SeekAudio" },
      { type: "PlayAudio" },
      { cursorMs: 250, endMs: 750, type: "StartProgressFrame" },
      { status: "playing", type: "PublishPlaybackState" },
    ]);
  });

  it("cancels loading source playback and does not fake paused state before playback starts", () => {
    let state: HtmlAudioSessionState = initialHtmlAudioSessionState(0);
    state = transitionHtmlAudioSession(state, { cursorMs: 250, source, type: "SourceConfigured" }).state;
    const pause = transitionHtmlAudioSession(state, { cursorMs: 250, type: "PauseRequested" });
    expect(pause).toEqual({ state, effects: [{ type: "PauseAudio" }, { type: "ClearProgressFrame" }] });
    const transition = transitionHtmlAudioSession(state, { cursorMs: 250, type: "StopRequested" });
    expect(transition.state).toEqual(initialHtmlAudioSessionState(0));
    expect(transition.effects.map((effect) => effect.type)).toEqual([
      "PauseAudio", "ClearProgressFrame", "ClearRepeatTimer", "ClearMetadataTimer", "PublishPlaybackState",
    ]);
    expect(transition.effects.at(-1)).toEqual({ cursorMs: 250, status: "stopped", type: "PublishPlaybackState" });
  });

  it("clears active playback artifacts before configuring a new source", () => {
    let state: HtmlAudioSessionState = initialHtmlAudioSessionState(0);

    state = transitionHtmlAudioSession(state, {
      cursorMs: 0,
      source,
      type: "SourceConfigured",
    }).state;
    state = transitionHtmlAudioSession(state, {
      durationMs: 1000,
      type: "MetadataLoaded",
    }).state;
    state = transitionHtmlAudioSession(state, {
      request,
      type: "StartRequested",
    }).state;
    state = transitionHtmlAudioSession(state, {
      nowMs: 120,
      sourceFilename: "clip one.mp3",
      type: "PlayResolved",
    }).state;

    const nextSource = {
      kind: "source" as const,
      sourceFilename: "clip two.mp3",
    };
    const transition = transitionHtmlAudioSession(state, {
      cursorMs: 125,
      source: nextSource,
      type: "SourceConfigured",
    });

    expect(transition.effects.slice(0, 5)).toEqual([
      { type: "ClearProgressFrame" },
      { type: "ClearRepeatTimer" },
      { type: "ClearMetadataTimer" },
      { type: "PauseAudio" },
      { sourceFilename: "clip two.mp3", type: "ConfigureAudioSource" },
    ]);
  });

  it("dispatches post-edit ready once when a generated source has a rendered graph before metadata", () => {
    let state: HtmlAudioSessionState = initialHtmlAudioSessionState(0);
    const generatedSource = {
      kind: "source" as const,
      sourceFilename: "clip__aqe_123.mp3",
    };
    const intent = {
      fieldOrd: 0,
      generation: 7,
      requireGraphRedraw: true,
      sourceFilename: "clip__aqe_123.mp3",
      sourceKind: "generated_edit" as const,
    };
    const postEditRequest = {
      cursorMs: 0,
      endMs: 1333,
      loop: false,
      ord: 0,
      regionMode: "full" as const,
      source: "post_edit" as const,
    };

    state = transitionHtmlAudioSession(state, {
      cursorMs: 0,
      source: generatedSource,
      type: "SourceConfigured",
    }).state;

    let transition = transitionHtmlAudioSession(state, {
      intent,
      request: postEditRequest,
      type: "PostEditAutoplayRequested",
    });
    expect(transition.state).toMatchObject({
      kind: "post_edit_waiting",
      postEdit: intent,
      request: postEditRequest,
    });

    transition = transitionHtmlAudioSession(transition.state, {
      durationMs: 1333,
      sourceFilename: "clip__aqe_123.mp3",
      type: "GraphRenderedForSource",
    });
    expect(transition.state).toMatchObject({
      cursorMs: 0,
      durationMs: 1333,
      kind: "ready",
      source: generatedSource,
    });
    expect(transition.effects).toContainEqual({
      generation: 7,
      ord: 0,
      sourceFilename: "clip__aqe_123.mp3",
      type: "DispatchPostEditReady",
    });

    const duplicateTransition = transitionHtmlAudioSession(transition.state, {
      durationMs: 1333,
      sourceFilename: "clip__aqe_123.mp3",
      type: "GraphRenderedForSource",
    });
    expect(duplicateTransition.effects).not.toContainEqual({
      generation: 7,
      ord: 0,
      sourceFilename: "clip__aqe_123.mp3",
      type: "DispatchPostEditReady",
    });
  });

  it("dispatches post-edit ready when readiness is confirmed after metadata", () => {
    let state: HtmlAudioSessionState = initialHtmlAudioSessionState(0);
    const intent = {
      fieldOrd: 0,
      generation: 8,
      requireGraphRedraw: false,
      sourceFilename: "clip one.mp3",
      sourceKind: "existing_media" as const,
    };
    const postEditRequest = {
      ...request,
      source: "post_edit" as const,
    };

    state = transitionHtmlAudioSession(state, {
      cursorMs: 0,
      source,
      type: "SourceConfigured",
    }).state;
    state = transitionHtmlAudioSession(state, {
      intent,
      request: postEditRequest,
      type: "PostEditAutoplayRequested",
    }).state;

    const transition = transitionHtmlAudioSession(state, {
      durationMs: 1000,
      sourceFilename: "clip one.mp3",
      type: "PostEditReadyConfirmed",
    });

    expect(transition.state).toMatchObject({
      durationMs: 1000,
      kind: "ready",
      source,
    });
    expect(transition.effects).toEqual([
      { type: "ClearMetadataTimer" },
      {
        generation: 8,
        ord: 0,
        sourceFilename: "clip one.mp3",
        type: "DispatchPostEditReady",
      },
    ]);
  });

  it("completes non-loop source playback through an explicit effect", () => {
    let state: HtmlAudioSessionState = initialHtmlAudioSessionState(0);
    state = transitionHtmlAudioSession(state, {
      cursorMs: 0,
      source,
      type: "SourceConfigured",
    }).state;
    state = transitionHtmlAudioSession(state, {
      durationMs: 1000,
      type: "MetadataLoaded",
    }).state;
    state = transitionHtmlAudioSession(state, {
      request,
      type: "StartRequested",
    }).state;
    state = transitionHtmlAudioSession(state, {
      nowMs: 120,
      sourceFilename: "clip one.mp3",
      type: "PlayResolved",
    }).state;

    const transition = transitionHtmlAudioSession(state, {
      cursorMs: 1000,
      resetCursorMs: 0,
      type: "BoundaryReached",
    });

    expect(transition.state).toMatchObject({
      cursorMs: 0,
      kind: "ready",
    });
    expect(transition.effects).toEqual([
      { type: "PauseAudio" },
      { type: "ClearProgressFrame" },
      { type: "ClearRepeatTimer" },
      { cursorMs: 0, type: "CompletePlayback" },
    ]);
  });

  it("waits for the configured repeat pause before restarting a loop", () => {
    let state: HtmlAudioSessionState = initialHtmlAudioSessionState(0);
    const loopRequest = { ...request, loop: true };
    state = transitionHtmlAudioSession(state, {
      cursorMs: 0,
      source,
      type: "SourceConfigured",
    }).state;
    state = transitionHtmlAudioSession(state, {
      durationMs: 1000,
      type: "MetadataLoaded",
    }).state;
    state = transitionHtmlAudioSession(state, {
      request: loopRequest,
      type: "StartRequested",
    }).state;
    state = transitionHtmlAudioSession(state, {
      nowMs: 120,
      sourceFilename: "clip one.mp3",
      type: "PlayResolved",
    }).state;

    const waiting = transitionHtmlAudioSession(state, {
      cursorMs: 1000,
      repeatPauseMs: 750,
      resetCursorMs: 0,
      type: "BoundaryReached",
    });

    expect(waiting.state).toMatchObject({
      kind: "repeat_waiting",
      request: loopRequest,
      resumeAtMs: 0,
    });
    expect(waiting.effects).toEqual([
      { type: "PauseAudio" },
      { type: "ClearProgressFrame" },
      { pauseMs: 750, type: "StartRepeatTimer" },
      { cursorMs: 0, type: "PublishRepeatWaitingState" },
    ]);

    const restarting = transitionHtmlAudioSession(waiting.state, {
      type: "RepeatDelayElapsed",
    });
    expect(restarting.state).toMatchObject({
      kind: "starting",
      request: loopRequest,
    });
    expect(restarting.effects).toContainEqual({ type: "ReloadAudioSource" });
    expect(restarting.effects).toContainEqual({ type: "PlayAudio" });
  });

  it("fails starting playback when html audio play is rejected", () => {
    let state: HtmlAudioSessionState = initialHtmlAudioSessionState(0);

    state = transitionHtmlAudioSession(state, {
      cursorMs: 0,
      source,
      type: "SourceConfigured",
    }).state;
    state = transitionHtmlAudioSession(state, {
      durationMs: 1000,
      type: "MetadataLoaded",
    }).state;
    state = transitionHtmlAudioSession(state, {
      request: { ...request, cursorMs: 250 },
      type: "StartRequested",
    }).state;

    const transition = transitionHtmlAudioSession(state, {
      reason: "audio_play_rejected",
      sourceFilename: "clip one.mp3",
      type: "PlayRejected",
    });

    expect(transition.state).toEqual({
      kind: "failed",
      ord: 0,
      source,
      cursorMs: 250,
      reason: "audio_play_rejected",
    });
    expect(transition.effects).toEqual([
      { type: "ClearProgressFrame" },
      { type: "PauseAudio" },
      { cursorMs: 250, status: "stopped", type: "PublishPlaybackState" },
      { statusKey: "editor.status.browser_audio_unavailable", type: "ShowPlaybackStatus" },
      {
        data: { reason: "audio_play_rejected" },
        event: "playback.html_failed",
        type: "LogPlaybackTelemetry",
      },
    ]);
  });

  it("fails active source sessions when seek fails", () => {
    let state: HtmlAudioSessionState = initialHtmlAudioSessionState(0);

    state = transitionHtmlAudioSession(state, {
      cursorMs: 0,
      source,
      type: "SourceConfigured",
    }).state;
    state = transitionHtmlAudioSession(state, {
      durationMs: 1000,
      type: "MetadataLoaded",
    }).state;

    const transition = transitionHtmlAudioSession(state, {
      cursorMs: 400,
      reason: "audio_seek_failed",
      type: "SeekFailed",
    });

    expect(transition.state).toEqual({
      kind: "failed",
      ord: 0,
      source,
      cursorMs: 400,
      reason: "audio_seek_failed",
    });
    expect(transition.effects).toEqual([
      { type: "ClearProgressFrame" },
      { type: "PauseAudio" },
      { cursorMs: 400, status: "stopped", type: "PublishPlaybackState" },
      { statusKey: "editor.status.browser_audio_unavailable", type: "ShowPlaybackStatus" },
      {
        data: { reason: "audio_seek_failed" },
        event: "playback.html_failed",
        type: "LogPlaybackTelemetry",
      },
    ]);
  });

  it("ignores stale play resolution for a reconfigured source", () => {
    let state: HtmlAudioSessionState = initialHtmlAudioSessionState(0);

    state = transitionHtmlAudioSession(state, {
      cursorMs: 0,
      source,
      type: "SourceConfigured",
    }).state;
    state = transitionHtmlAudioSession(state, {
      durationMs: 1000,
      type: "MetadataLoaded",
    }).state;
    state = transitionHtmlAudioSession(state, {
      request,
      type: "StartRequested",
    }).state;

    const nextSource = {
      kind: "source" as const,
      sourceFilename: "clip two.mp3",
    };
    state = transitionHtmlAudioSession(state, {
      cursorMs: 125,
      source: nextSource,
      type: "SourceConfigured",
    }).state;

    const transition = transitionHtmlAudioSession(state, {
      nowMs: 120,
      sourceFilename: "clip one.mp3",
      type: "PlayResolved",
    });

    expect(transition).toEqual({ state, effects: [] });
  });
});
