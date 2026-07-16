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
const postEditRequest = { ...request, source: "post_edit" as const };
const postEditIntent = {
  fieldOrd: 0, generation: 1, requireGraphRedraw: false,
  sourceFilename: source.sourceFilename, sourceKind: "existing_media" as const,
};

const states = {
  empty: initialHtmlAudioSessionState(0),
  loading: { cursorMs: 125, kind: "loading", ord: 0, pendingStart: null, source } as const,
  ready: { cursorMs: 125, durationMs: 1000, kind: "ready", ord: 0, source } as const,
  starting: { durationMs: 1000, kind: "starting", ord: 0, request, source } as const,
  playing: { durationMs: 1000, kind: "playing", ord: 0, request, source, startedAtMs: 10 } as const,
  paused: { durationMs: 1000, kind: "paused", ord: 0, pausedAtMs: 375, request, source } as const,
  repeat_waiting: {
    durationMs: 1000, kind: "repeat_waiting", ord: 0, request: { ...request, loop: true }, resumeAtMs: 0, source,
  } as const,
  post_edit_waiting: {
    cursorMs: 100, graphDurationMs: null, kind: "post_edit_waiting", ord: 0,
    postEdit: postEditIntent, readyDispatched: false, request: postEditRequest, source,
  } as const,
  failed: {
    cursorMs: 0,
    kind: "failed",
    mediaErrorCode: null,
    mediaResponseStatus: null,
    ord: 0,
    reason: "audio_error",
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
  {
    intent: { fieldOrd: 0, generation: 1, requireGraphRedraw: false, sourceFilename: source.sourceFilename, sourceKind: "existing_media" },
    request: { ...request, source: "post_edit" },
    type: "PostEditAutoplayRequested",
  },
  { durationMs: 1000, sourceFilename: source.sourceFilename, type: "GraphRenderedForSource" },
  { durationMs: 1000, sourceFilename: source.sourceFilename, type: "PostEditReadyConfirmed" },
  { nowMs: 1, sourceFilename: source.sourceFilename, type: "PlayResolved" },
  { reason: "audio_play_rejected", sourceFilename: source.sourceFilename, type: "PlayRejected" },
  { cursorMs: 0, reason: "audio_seek_failed", type: "SeekFailed" },
  { cursorMs: 0, type: "PauseRequested" },
  { type: "ResumeRequested" },
  { cursorMs: 0, type: "StopRequested" },
  { cursorMs: 1000, type: "BoundaryReached" },
  { type: "RepeatDelayElapsed" },
  { cursorMs: 0, mediaErrorCode: null, mediaResponseStatus: null, reason: "audio_error", type: "AudioError" },
  { type: "RuntimeDisposed" },
] satisfies HtmlAudioSessionEvent[];

describe("html audio session transition matrix", () => {
  it("keeps a typed sample for every declared event", () => {
    expect(new Set(eventInventory.map((event) => event.type))).toEqual(new Set([
      "AudioError", "BoundaryReached", "GraphRenderedForSource", "MetadataLoaded", "MetadataTimeout",
      "PauseRequested", "PlayRejected", "PlayResolved", "PostEditAutoplayRequested", "PostEditReadyConfirmed",
      "RepeatDelayElapsed", "ResumeRequested", "RuntimeDisposed", "SeekFailed", "SourceCleared", "SourceConfigured",
      "StartRequested", "StopRequested",
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
      "ClearProgressFrame", "ClearRepeatTimer", "ClearMetadataTimer", "PauseAudio", "PublishPlaybackState",
      "ShowPlaybackStatus", "LogPlaybackTelemetry",
    ]);

    const ready: HtmlAudioSessionState = { cursorMs: 0, durationMs: 1000, kind: "ready", ord: 0, source };
    expect(transitionHtmlAudioSession(ready, { type: "MetadataTimeout" })).toEqual({ state: ready, effects: [] });
  });

  it.each(["SourceCleared", "RuntimeDisposed"] as const)("%s disposes every active resource", (type) => {
    const active: HtmlAudioSessionState = {
      durationMs: 1000, kind: "repeat_waiting", ord: 0, request: { ...request, loop: true }, resumeAtMs: 0, source,
    };
    const transition = transitionHtmlAudioSession(active, { type });
    expect(transition.state).toEqual(initialHtmlAudioSessionState(0));
    expect(transition.effects.map((effect) => effect.type)).toEqual([
      "PauseAudio", "ClearAudioSource", "ClearProgressFrame", "ClearMetadataTimer", "ClearRepeatTimer",
      "PublishPlaybackState",
    ]);
  });

  it("source clearing is idempotent while runtime disposal preserves an empty no-op", () => {
    const empty = initialHtmlAudioSessionState(0);
    expect(transitionHtmlAudioSession(empty, { type: "SourceCleared" }).effects).toHaveLength(6);
    expect(transitionHtmlAudioSession(empty, { type: "RuntimeDisposed" })).toEqual({ state: empty, effects: [] });
  });

  it("configures a source from every state and cancels only active resources", () => {
    for (const [kind, state] of Object.entries(states)) {
      const result = transitionHtmlAudioSession(state, { cursorMs: 44, source, type: "SourceConfigured" });
      expect(result.state, kind).toEqual({ cursorMs: 44, kind: "loading", ord: 0, pendingStart: null, source });
      expect(result.effects, kind).toEqual([
        ...(["loading", "starting", "playing", "paused", "repeat_waiting", "post_edit_waiting"].includes(kind)
          ? [{ type: "ClearProgressFrame" }, { type: "ClearRepeatTimer" }, { type: "ClearMetadataTimer" }, { type: "PauseAudio" }]
          : []),
        { sourceFilename: source.sourceFilename, type: "ConfigureAudioSource" },
        { timeoutMs: 5000, type: "StartMetadataTimer" },
        { status: "stopped", type: "PublishPlaybackState" },
      ]);
    }
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
    for (const kind of ["starting", "playing", "paused", "repeat_waiting"] as const) {
      expect(effectTypes(states[kind], { request: nextRequest, type: "StartRequested" }), kind).toEqual([
        "ClearRepeatTimer", "ClearProgressFrame", "SeekAudio", "PlayAudio",
      ]);
    }
    for (const kind of ["empty", "post_edit_waiting", "failed"] as const) {
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
      source,
    });
    expect(effectTypes(states.starting, { reason: "audio_play_rejected", sourceFilename: source.sourceFilename, type: "PlayRejected" }))
      .toEqual(["ClearProgressFrame", "ClearRepeatTimer", "ClearMetadataTimer", "PauseAudio", "PublishPlaybackState", "ShowPlaybackStatus", "LogPlaybackTelemetry"]);
    for (const event of [
      { nowMs: 55, sourceFilename: "other.mp3", type: "PlayResolved" } as const,
      { reason: "audio_play_rejected", sourceFilename: "other.mp3", type: "PlayRejected" } as const,
    ]) expect(transitionHtmlAudioSession(states.starting, event)).toEqual({ state: states.starting, effects: [] });
    expect(transitionHtmlAudioSession(states.ready, { nowMs: 55, sourceFilename: source.sourceFilename, type: "PlayResolved" }))
      .toEqual({ state: states.ready, effects: [] });
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
    for (const kind of ["empty", "paused", "repeat_waiting", "post_edit_waiting", "failed"] as const) {
      expect(transitionHtmlAudioSession(states[kind], { cursorMs: 9, type: "PauseRequested" }), kind)
        .toEqual({ state: states[kind], effects: [] });
    }
    expect(effectTypes(states.loading, { cursorMs: 9, type: "StopRequested" })).toEqual([
      "PauseAudio", "ClearProgressFrame", "ClearRepeatTimer", "ClearMetadataTimer", "PublishPlaybackState",
    ]);
    expect(transitionHtmlAudioSession(states.ready, { cursorMs: 9, type: "StopRequested" })).toEqual({
      state: states.ready,
      effects: [
        { type: "PauseAudio" }, { type: "ClearProgressFrame" }, { type: "ClearRepeatTimer" },
        { cursorMs: 9, status: "stopped", type: "PublishPlaybackState" },
      ],
    });
    for (const kind of ["starting", "playing", "paused", "repeat_waiting"] as const) {
      expect(transitionHtmlAudioSession(states[kind], { cursorMs: 9, type: "StopRequested" }).state, kind)
        .toEqual({ cursorMs: 9, durationMs: 1000, kind: "ready", ord: 0, source });
    }
    for (const kind of ["empty", "post_edit_waiting", "failed"] as const) {
      expect(transitionHtmlAudioSession(states[kind], { cursorMs: 9, type: "StopRequested" }), kind)
        .toEqual({ state: states[kind], effects: [] });
    }
  });

  it("handles boundary completion, immediate repeat, delayed repeat, and cancellation", () => {
    expect(transitionHtmlAudioSession(states.playing, { cursorMs: 1000, type: "BoundaryReached" })).toEqual({
      state: { cursorMs: 0, durationMs: 1000, kind: "ready", ord: 0, source },
      effects: [{ type: "PauseAudio" }, { type: "ClearProgressFrame" }, { type: "ClearRepeatTimer" }, { cursorMs: 0, type: "CompletePlayback" }],
    });
    const looping = { ...states.playing, request: { ...request, cursorMs: 200, loop: true, resetCursorMs: 100 } };
    expect(effectTypes(looping, { cursorMs: 1000, restartAudio: true, type: "BoundaryReached" })).toEqual([
      "ClearRepeatTimer", "ClearProgressFrame", "SeekAudio", "PlayAudio",
    ]);
    const waiting = transitionHtmlAudioSession(looping, { cursorMs: 1000, repeatPauseMs: 250, type: "BoundaryReached" });
    expect(waiting.state).toEqual({ durationMs: 1000, kind: "repeat_waiting", ord: 0, request: looping.request, resumeAtMs: 100, source });
    expect(waiting.effects).toEqual([
      { type: "PauseAudio" }, { type: "ClearProgressFrame" }, { pauseMs: 250, type: "StartRepeatTimer" },
      { cursorMs: 100, type: "PublishRepeatWaitingState" },
    ]);
    expect(effectTypes(waiting.state, { type: "RepeatDelayElapsed" })).toEqual([
      "ClearRepeatTimer", "ClearProgressFrame", "SeekAudio", "PlayAudio",
    ]);
    expect(transitionHtmlAudioSession(waiting.state, { repeatEnabled: false, type: "RepeatDelayElapsed" })).toEqual({
      state: { cursorMs: 100, durationMs: 1000, kind: "ready", ord: 0, source },
      effects: [{ type: "ClearRepeatTimer" }, { cursorMs: 100, type: "CompletePlayback" }],
    });
    expect(transitionHtmlAudioSession(states.ready, {
      cursorMs: 1000, repeatEnabled: true, repeatPauseMs: 250, request: { ...request, loop: false },
      resetCursorMs: 33, type: "BoundaryReached",
    })).toEqual({
      state: {
        durationMs: 1000, kind: "repeat_waiting", ord: 0, request: { ...request, loop: false },
        resumeAtMs: 0, source,
      },
      effects: [
        { type: "PauseAudio" }, { type: "ClearProgressFrame" }, { pauseMs: 250, type: "StartRepeatTimer" },
        { cursorMs: 0, type: "PublishRepeatWaitingState" },
      ],
    });
    expect(transitionHtmlAudioSession(states.ready, { cursorMs: 1000, request, resetCursorMs: 33, type: "BoundaryReached" })).toEqual({
      state: { cursorMs: 33, durationMs: 1000, kind: "ready", ord: 0, source },
      effects: [
        { type: "PauseAudio" }, { type: "ClearProgressFrame" }, { type: "ClearRepeatTimer" },
        { cursorMs: 33, type: "CompletePlayback" },
      ],
    });
    expect(transitionHtmlAudioSession(states.empty, { cursorMs: 1, type: "BoundaryReached" })).toEqual({ state: states.empty, effects: [] });
  });

  it("fails seek and audio errors only while a source is active", () => {
    for (const kind of ["loading", "ready", "starting", "playing", "paused", "repeat_waiting", "post_edit_waiting"] as const) {
      const result = transitionHtmlAudioSession(states[kind], { cursorMs: 88, reason: "audio_seek_failed", type: "SeekFailed" });
      expect(result.state, kind).toMatchObject({ cursorMs: 88, kind: "failed", reason: "audio_seek_failed" });
    }
    for (const kind of ["empty", "failed"] as const) {
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

  it("gates post-edit autoplay by state, source, duplicate request, and readiness", () => {
    for (const kind of ["empty", "failed"] as const) {
      expect(transitionHtmlAudioSession(states[kind], { intent: postEditIntent, request: postEditRequest, type: "PostEditAutoplayRequested" }))
        .toEqual({ state: states[kind], effects: [] });
    }
    expect(transitionHtmlAudioSession(states.ready, {
      intent: { ...postEditIntent, sourceFilename: "other.mp3" }, request: postEditRequest, type: "PostEditAutoplayRequested",
    })).toEqual({ state: states.ready, effects: [] });
    const accepted = transitionHtmlAudioSession(states.ready, { intent: postEditIntent, request: postEditRequest, type: "PostEditAutoplayRequested" });
    expect(accepted.state).toEqual({
      cursorMs: 125, graphDurationMs: null, kind: "post_edit_waiting", ord: 0, postEdit: postEditIntent,
      readyDispatched: false, request: postEditRequest, source,
    });
    const expectedCursors: Partial<Record<keyof typeof states, number>> = {
      loading: 125, playing: 0, post_edit_waiting: 100, ready: 125, repeat_waiting: 0, starting: 0,
    };
    for (const kind of ["loading", "ready", "starting", "playing", "paused", "repeat_waiting", "post_edit_waiting"] as const) {
      const activeState = states[kind];
      const nonDuplicateRequest = kind === "starting" || kind === "playing" || kind === "paused" || kind === "repeat_waiting"
        ? { ...postEditRequest, cursorMs: 2 }
        : postEditRequest;
      const result = transitionHtmlAudioSession(activeState, {
        intent: postEditIntent, request: nonDuplicateRequest, type: "PostEditAutoplayRequested",
      });
      expect(result.state, kind).toMatchObject({
        cursorMs: kind === "paused" ? 375 : expectedCursors[kind], kind: "post_edit_waiting",
        postEdit: postEditIntent, readyDispatched: false, request: nonDuplicateRequest,
      });
      expect(result.effects, kind).toEqual([]);
    }
    expect(transitionHtmlAudioSession(accepted.state, {
      durationMs: 777, sourceFilename: "other.mp3", type: "GraphRenderedForSource",
    })).toEqual({ state: accepted.state, effects: [] });
    for (const type of ["GraphRenderedForSource", "PostEditReadyConfirmed"] as const) {
      expect(transitionHtmlAudioSession(accepted.state, { durationMs: 777, sourceFilename: source.sourceFilename, type })).toEqual({
        state: { cursorMs: 0, durationMs: 777, kind: "ready", ord: 0, source },
        effects: [{ type: "ClearMetadataTimer" }, { generation: 1, ord: 0, sourceFilename: source.sourceFilename, type: "DispatchPostEditReady" }],
      });
    }
    const dispatched = { ...accepted.state, graphDurationMs: 500, readyDispatched: true } as HtmlAudioSessionState;
    expect(transitionHtmlAudioSession(dispatched, {
      durationMs: 777, sourceFilename: source.sourceFilename, type: "PostEditReadyConfirmed",
    })).toEqual({ state: { ...dispatched, graphDurationMs: 777 }, effects: [] });
  });

  it("treats only field-for-field identical active post-edit requests as duplicates", () => {
    const event = { intent: postEditIntent, request: postEditRequest, type: "PostEditAutoplayRequested" } as const;
    for (const kind of ["starting", "playing", "paused", "repeat_waiting"] as const) {
      const active = { ...states[kind], request: postEditRequest } as HtmlAudioSessionState;
      expect(transitionHtmlAudioSession(active, event), kind).toEqual({ state: active, effects: [] });
    }
    const active: HtmlAudioSessionState = { ...states.starting, request: postEditRequest };
    const variants = [
      { ...postEditRequest, source: "user" as const }, { ...postEditRequest, cursorMs: 1 },
      { ...postEditRequest, endMs: 999 }, { ...postEditRequest, loop: true }, { ...postEditRequest, ord: 1 },
      { ...postEditRequest, regionMode: "selection" as const }, { ...postEditRequest, resetCursorMs: 4 },
    ];
    for (const changed of variants) {
      expect(transitionHtmlAudioSession(active, { ...event, request: changed }).state.kind, JSON.stringify(changed))
        .toBe("post_edit_waiting");
    }
    expect(transitionHtmlAudioSession({ ...states.starting, request }, event).state.kind).toBe("post_edit_waiting");
  });
});
