import { describe, expect, it } from "vitest";

import {
  initialHtmlAudioSessionState,
  transitionHtmlAudioSession,
  type HtmlAudioSessionEvent,
  type HtmlAudioSessionState,
} from "../src/editor-inline/html-audio-session-machine.js";

const source = { kind: "source" as const, sourceFilename: "clip one.mp3" };
const request = {
  cursorMs: 0,
  endMs: 1000,
  loop: false,
  ord: 0,
  regionMode: "full" as const,
  source: "user" as const,
};
const states = {
  empty: initialHtmlAudioSessionState(0),
  loading: { cursorMs: 125, kind: "loading", ord: 0, pendingStart: null, source } as const,
  ready: { cursorMs: 125, durationMs: 1000, kind: "ready", ord: 0, source } as const,
  starting: { durationMs: 1000, kind: "starting", ord: 0, request, source } as const,
  playing: { durationMs: 1000, kind: "playing", ord: 0, request, source, startedAtMs: 10 } as const,
  paused: { durationMs: 1000, kind: "paused", ord: 0, pausedAtMs: 375, request, source } as const,
  failed: {
    cursorMs: 0,
    kind: "failed",
    mediaErrorCode: null,
    mediaResponseStatus: null,
    ord: 0,
    reason: "audio_error",
    recovery: "none",
    source,
  } as const,
} satisfies Record<HtmlAudioSessionState["kind"], HtmlAudioSessionState>;

function effectTypes(state: HtmlAudioSessionState, event: HtmlAudioSessionEvent): string[] {
  return transitionHtmlAudioSession(state, event).effects.map((effect) => effect.type);
}

const eventInventory = [
  { cursorMs: 0, source, type: "SourceConfigured" },
  { type: "SourceCleared" },
  { durationMs: 1000, type: "MetadataLoaded" },
  { type: "MetadataTimeout" },
  { request, type: "StartRequested" },
  { nowMs: 1, sourceFilename: source.sourceFilename, type: "PlayResolved" },
  { reason: "audio_play_rejected", sourceFilename: source.sourceFilename, type: "PlayRejected" },
  { cursorMs: 0, reason: "audio_seek_failed", type: "SeekFailed" },
  { cursorMs: 0, type: "PauseRequested" },
  { type: "ResumeRequested" },
  { cursorMs: 0, type: "StopRequested" },
  { cursorMs: 1000, type: "BoundaryReached" },
  { cursorMs: 0, mediaErrorCode: null, mediaResponseStatus: null, reason: "audio_error", type: "AudioError" },
  { type: "RecoveryClaimed" },
  { type: "RuntimeDisposed" },
] satisfies HtmlAudioSessionEvent[];

describe("html audio session transition matrix", () => {
  it("keeps a typed sample for every declared event", () => {
    expect(new Set(eventInventory.map((event) => event.type))).toEqual(new Set([
      "AudioError", "BoundaryReached", "MetadataLoaded", "MetadataTimeout",
      "PauseRequested", "PlayRejected", "PlayResolved",
      "ResumeRequested", "RuntimeDisposed", "SeekFailed", "SourceCleared", "SourceConfigured",
      "StartRequested", "StopRequested", "RecoveryClaimed",
    ]));
  });

  it("resumes only paused playback from the captured cursor", () => {
    const paused: HtmlAudioSessionState = {
      durationMs: 1000, kind: "paused", ord: 0, pausedAtMs: 375, request, source,
    };
    const resumed = transitionHtmlAudioSession(paused, { type: "ResumeRequested" });
    expect(resumed.state).toMatchObject({ kind: "starting", request: { ...request, cursorMs: 375 } });
    expect(resumed.effects).toEqual([{ cursorMs: 375, type: "SeekAudio" }, { type: "PlayAudio" }]);

    for (const invalid of [
      initialHtmlAudioSessionState(0),
      { cursorMs: 0, durationMs: 1000, kind: "ready", ord: 0, source } as const,
      {
        cursorMs: 0,
        kind: "failed",
        mediaErrorCode: null,
        mediaResponseStatus: null,
        ord: 0,
        reason: "audio_error",
        recovery: "none",
        source,
      } as const,
    ]) {
      expect(transitionHtmlAudioSession(invalid, { type: "ResumeRequested" })).toEqual({ state: invalid, effects: [] });
    }
  });

  it("fails only loading sessions on metadata timeout and cancels all timers", () => {
    const loading: HtmlAudioSessionState = { cursorMs: 125, kind: "loading", ord: 0, pendingStart: null, source };
    const timedOut = transitionHtmlAudioSession(loading, { type: "MetadataTimeout" });
    expect(timedOut.state).toMatchObject({ cursorMs: 125, kind: "failed", reason: "metadata_timeout" });
    expect(timedOut.effects.map((effect) => effect.type)).toEqual([
      "ClearProgressFrame", "ClearMetadataTimer", "PauseAudio", "PublishPlaybackState",
      "ShowPlaybackStatus", "LogPlaybackTelemetry",
    ]);

    const ready: HtmlAudioSessionState = { cursorMs: 0, durationMs: 1000, kind: "ready", ord: 0, source };
    expect(transitionHtmlAudioSession(ready, { type: "MetadataTimeout" })).toEqual({ state: ready, effects: [] });
  });

  it.each(["SourceCleared", "RuntimeDisposed"] as const)("%s disposes every active resource", (type) => {
    const active: HtmlAudioSessionState = states.playing;
    const transition = transitionHtmlAudioSession(active, { type });
    expect(transition.state).toEqual(initialHtmlAudioSessionState(0));
    expect(transition.effects.map((effect) => effect.type)).toEqual([
      "ClearAudioSource", "ClearProgressFrame", "ClearMetadataTimer",
      "PublishPlaybackState",
    ]);
  });

  it("source clearing is idempotent while runtime disposal preserves an empty no-op", () => {
    const empty = initialHtmlAudioSessionState(0);
    expect(transitionHtmlAudioSession(empty, { type: "SourceCleared" }).effects).toHaveLength(4);
    expect(transitionHtmlAudioSession(empty, { type: "RuntimeDisposed" })).toEqual({ state: empty, effects: [] });
  });

  it("configures a source from every state and cancels only active resources", () => {
    for (const [kind, state] of Object.entries(states)) {
      const result = transitionHtmlAudioSession(state, { cursorMs: 44, replace: true, source, type: "SourceConfigured" });
      expect(result.state, kind).toEqual({ cursorMs: 44, kind: "loading", ord: 0, pendingStart: null, source });
      expect(result.effects, kind).toEqual([
        ...(["loading", "starting", "playing", "paused"].includes(kind)
          ? [{ type: "ClearProgressFrame" }, { type: "ClearMetadataTimer" }]
          : []),
        { sourceFilename: source.sourceFilename, type: "ConfigureAudioSource" },
        { timeoutMs: 5000, type: "StartMetadataTimer" },
        { status: "stopped", type: "PublishPlaybackState" },
      ]);
    }
  });

  it("keeps an identical source binding and distinguishes learner recording attempts", () => {
    expect(transitionHtmlAudioSession(states.ready, {
      cursorMs: 999,
      source,
      type: "SourceConfigured",
    })).toEqual({ state: states.ready, effects: [] });

    const firstLearnerSource = {
      attemptId: 1,
      kind: "learner_recording" as const,
      sourceFilename: "learner.wav",
      startCursorMs: 125,
    };
    const learnerReady: HtmlAudioSessionState = {
      cursorMs: 0,
      durationMs: 1000,
      kind: "ready",
      ord: 0,
      source: firstLearnerSource,
    };
    expect(transitionHtmlAudioSession(learnerReady, {
      cursorMs: 50,
      source: firstLearnerSource,
      type: "SourceConfigured",
    })).toEqual({ state: learnerReady, effects: [] });
    expect(transitionHtmlAudioSession(learnerReady, {
      cursorMs: 50,
      source: { ...firstLearnerSource, attemptId: 2 },
      type: "SourceConfigured",
    }).state).toEqual({
      cursorMs: 50,
      kind: "loading",
      ord: 0,
      pendingStart: null,
      source: { ...firstLearnerSource, attemptId: 2 },
    });
    expect(transitionHtmlAudioSession(learnerReady, {
      cursorMs: 50,
      source: { kind: "source", sourceFilename: firstLearnerSource.sourceFilename },
      type: "SourceConfigured",
    }).state).toMatchObject({ kind: "loading", source: { kind: "source" } });
    expect(transitionHtmlAudioSession(states.failed, {
      cursorMs: 50,
      source,
      type: "SourceConfigured",
    }).state).toMatchObject({ kind: "loading" });
  });

  it("loads metadata with and without a deferred start", () => {
    expect(transitionHtmlAudioSession(states.loading, { durationMs: 900, type: "MetadataLoaded" })).toEqual({
      state: { cursorMs: 125, durationMs: 900, kind: "ready", ord: 0, source },
      effects: [{ type: "ClearMetadataTimer" }, { status: "stopped", type: "PublishPlaybackState" }],
    });
    const deferred = { ...states.loading, pendingStart: { ...request, cursorMs: 77 } };
    expect(transitionHtmlAudioSession(deferred, { durationMs: 900, type: "MetadataLoaded" })).toEqual({
      state: { durationMs: 900, kind: "starting", ord: 0, request: deferred.pendingStart, source },
      effects: [{ type: "ClearMetadataTimer" }, { cursorMs: 77, type: "SeekAudio" }, { type: "PlayAudio" }],
    });
    for (const kind of Object.keys(states).filter((kind) => kind !== "loading") as Array<keyof typeof states>) {
      expect(transitionHtmlAudioSession(states[kind], { durationMs: 900, type: "MetadataLoaded" }), kind)
        .toEqual({ state: states[kind], effects: [] });
    }
  });

  it("starts from loading, ready, and every active playback state", () => {
    const nextRequest = { ...request, cursorMs: 222 };
    const deferred = transitionHtmlAudioSession(states.loading, { request: nextRequest, type: "StartRequested" });
    expect(deferred.state).toEqual({ ...states.loading, pendingStart: nextRequest });
    expect(deferred.effects).toEqual([
      { status: "stopped", type: "PublishPlaybackState" },
      { data: { ord: 0, sourceKind: "source" }, event: "html_audio_start_deferred_until_metadata", type: "LogPlaybackTelemetry" },
    ]);
    expect(transitionHtmlAudioSession(states.ready, { request: nextRequest, type: "StartRequested" })).toEqual({
      state: { durationMs: 1000, kind: "starting", ord: 0, request: nextRequest, source },
      effects: [{ cursorMs: 222, type: "SeekAudio" }, { type: "PlayAudio" }],
    });
    for (const kind of ["starting", "playing", "paused"] as const) {
      expect(transitionHtmlAudioSession(states[kind], {
        request: nextRequest,
        type: "StartRequested",
      }), kind).toEqual({
        state: { durationMs: 1000, kind: "starting", ord: 0, request: nextRequest, source },
        effects: [
          { type: "ClearProgressFrame" },
          { cursorMs: 222, type: "SeekAudio" },
          { type: "PlayAudio" },
        ],
      });
    }
    for (const kind of ["empty", "failed"] as const) {
      expect(transitionHtmlAudioSession(states[kind], { request: nextRequest, type: "StartRequested" }))
        .toEqual({ state: states[kind], effects: [] });
    }
  });

  it("accepts play outcomes only for the matching starting source", () => {
    expect(transitionHtmlAudioSession(states.starting, { nowMs: 55, sourceFilename: source.sourceFilename, type: "PlayResolved" })).toEqual({
      state: { ...states.starting, kind: "playing", startedAtMs: 55 },
      effects: [{ cursorMs: 0, endMs: 1000, type: "StartProgressFrame" }, { status: "playing", type: "PublishPlaybackState" }],
    });
    const rejected = transitionHtmlAudioSession(states.starting, {
      reason: "audio_play_rejected", sourceFilename: source.sourceFilename, type: "PlayRejected",
    });
    expect(rejected.state).toEqual({
      cursorMs: 0,
      kind: "failed",
      mediaErrorCode: null,
      mediaResponseStatus: null,
      ord: 0,
      reason: "audio_play_rejected",
      recovery: "none",
      source,
    });
    expect(effectTypes(states.starting, { reason: "audio_play_rejected", sourceFilename: source.sourceFilename, type: "PlayRejected" }))
      .toEqual(["ClearProgressFrame", "ClearMetadataTimer", "PauseAudio", "PublishPlaybackState", "ShowPlaybackStatus", "LogPlaybackTelemetry"]);
    for (const event of [
      { nowMs: 55, sourceFilename: "other.mp3", type: "PlayResolved" } as const,
      { reason: "audio_play_rejected", sourceFilename: "other.mp3", type: "PlayRejected" } as const,
    ]) expect(transitionHtmlAudioSession(states.starting, event)).toEqual({ state: states.starting, effects: [] });
    expect(transitionHtmlAudioSession(states.ready, { nowMs: 55, sourceFilename: source.sourceFilename, type: "PlayResolved" }))
      .toEqual({ state: states.ready, effects: [] });
    expect(transitionHtmlAudioSession(states.ready, {
      reason: "audio_play_rejected",
      sourceFilename: source.sourceFilename,
      type: "PlayRejected",
    })).toEqual({ state: states.ready, effects: [] });
  });

  it("implements pause and stop semantics for every state category", () => {
    expect(transitionHtmlAudioSession(states.loading, { cursorMs: 9, type: "PauseRequested" })).toEqual({
      state: states.empty, effects: [{ type: "PauseAudio" }, { type: "ClearProgressFrame" }, { type: "ClearMetadataTimer" }],
    });
    expect(effectTypes(states.ready, { cursorMs: 9, type: "PauseRequested" })).toEqual(["PauseAudio", "ClearProgressFrame"]);
    for (const kind of ["starting", "playing"] as const) {
      const result = transitionHtmlAudioSession(states[kind], { cursorMs: 9, type: "PauseRequested" });
      expect(result.state, kind).toEqual({ durationMs: 1000, kind: "paused", ord: 0, pausedAtMs: 9, request, source });
      expect(result.effects).toEqual([{ type: "PauseAudio" }, { type: "ClearProgressFrame" }, { cursorMs: 9, status: "paused", type: "PublishPlaybackState" }]);
    }
    for (const kind of ["empty", "paused", "failed"] as const) {
      expect(transitionHtmlAudioSession(states[kind], { cursorMs: 9, type: "PauseRequested" }), kind)
        .toEqual({ state: states[kind], effects: [] });
    }
    expect(effectTypes(states.loading, { cursorMs: 9, type: "StopRequested" })).toEqual([
      "PauseAudio", "ClearProgressFrame", "ClearMetadataTimer", "PublishPlaybackState",
    ]);
    expect(transitionHtmlAudioSession(states.ready, { cursorMs: 9, type: "StopRequested" })).toEqual({
      state: states.ready,
      effects: [
        { type: "PauseAudio" }, { type: "ClearProgressFrame" },
        { cursorMs: 9, status: "stopped", type: "PublishPlaybackState" },
      ],
    });
    for (const kind of ["starting", "playing", "paused"] as const) {
      expect(transitionHtmlAudioSession(states[kind], { cursorMs: 9, type: "StopRequested" }), kind)
        .toEqual({
          state: { cursorMs: 9, durationMs: 1000, kind: "ready", ord: 0, source },
          effects: [
            { type: "PauseAudio" },
            { type: "ClearProgressFrame" },
            { cursorMs: 9, status: "stopped", type: "PublishPlaybackState" },
          ],
        });
    }
    for (const kind of ["empty", "failed"] as const) {
      expect(transitionHtmlAudioSession(states[kind], { cursorMs: 9, type: "StopRequested" }), kind)
        .toEqual({ state: states[kind], effects: [] });
    }
  });

  it("completes boundaries and reports the immutable pass", () => {
    const exhausted = transitionHtmlAudioSession(states.playing, { cursorMs: 1000, type: "BoundaryReached" });
    expect(exhausted).toEqual({
      state: { cursorMs: 0, durationMs: 1000, kind: "ready", mediaExhausted: true, ord: 0, source },
      effects: [
        { type: "PauseAudio" }, { type: "ClearProgressFrame" },
        { request, type: "ReportPassCompleted" }, { cursorMs: 0, type: "CompletePlayback" },
      ],
    });
    expect(transitionHtmlAudioSession(exhausted.state, { request, type: "StartRequested" }).effects).toEqual([
      { type: "ReloadAudioSource" },
      { cursorMs: 0, type: "SeekAudio" },
      { type: "PlayAudio" },
    ]);
    const partial = transitionHtmlAudioSession(states.playing, { cursorMs: 750, type: "BoundaryReached" });
    expect(partial.state).not.toHaveProperty("mediaExhausted");
    expect(transitionHtmlAudioSession(partial.state, { request, type: "StartRequested" }).effects)
      .not.toContainEqual({ type: "ReloadAudioSource" });
    expect(transitionHtmlAudioSession(states.starting, {
      cursorMs: 1000,
      resetCursorMs: 33,
      type: "BoundaryReached",
    })).toEqual({
      state: { cursorMs: 33, durationMs: 1000, kind: "ready", mediaExhausted: true, ord: 0, source },
      effects: [
        { type: "PauseAudio" },
        { type: "ClearProgressFrame" },
        { request, type: "ReportPassCompleted" },
        { cursorMs: 33, type: "CompletePlayback" },
      ],
    });
    expect(transitionHtmlAudioSession(states.ready, { cursorMs: 1000, resetCursorMs: 33, type: "BoundaryReached" }))
      .toEqual({ state: states.ready, effects: [] });
    expect(transitionHtmlAudioSession(states.empty, { cursorMs: 1, type: "BoundaryReached" })).toEqual({ state: states.empty, effects: [] });
  });

  it("fails seek and audio errors only while a source is active", () => {
    for (const kind of ["loading", "ready", "starting", "playing", "paused"] as const) {
      const result = transitionHtmlAudioSession(states[kind], { cursorMs: 88, reason: "audio_seek_failed", type: "SeekFailed" });
      expect(result.state, kind).toMatchObject({ cursorMs: 88, kind: "failed", reason: "audio_seek_failed" });
    }
    for (const kind of ["empty", "failed"] as const) {
      expect(transitionHtmlAudioSession(states[kind], {
        cursorMs: 88,
        reason: "audio_seek_failed",
        type: "SeekFailed",
      })).toEqual({ state: states[kind], effects: [] });
      expect(transitionHtmlAudioSession(states[kind], {
        cursorMs: 88,
        mediaErrorCode: null,
        mediaResponseStatus: null,
        reason: "audio_error",
        type: "AudioError",
      }))
        .toEqual({ state: states[kind], effects: [] });
    }
  });

  it("claims an available recovery exactly once", () => {
    const recoverable: HtmlAudioSessionState = {
      ...states.failed,
      recovery: "available",
    };
    const claimed = transitionHtmlAudioSession(recoverable, { type: "RecoveryClaimed" });
    expect(claimed).toEqual({
      effects: [],
      state: { ...recoverable, recovery: "claimed" },
    });
    expect(transitionHtmlAudioSession(claimed.state, { type: "RecoveryClaimed" }))
      .toEqual({ effects: [], state: claimed.state });
    expect(transitionHtmlAudioSession(states.ready, { type: "RecoveryClaimed" }))
      .toEqual({ effects: [], state: states.ready });
  });

});
