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

const postEditLoopRequest = {
  cursorMs: 0,
  endMs: 1000,
  loop: true,
  ord: 0,
  regionMode: "full" as const,
  source: "post_edit" as const,
};

describe("html audio post-edit repeat", () => {
  it("keeps starting when duplicate ready checks repeat before play resolves", () => {
    let state: HtmlAudioSessionState = initialHtmlAudioSessionState(0);
    const intent = {
      fieldOrd: 0,
      generation: 7,
      requireGraphRedraw: true,
      sourceFilename: "clip one.mp3",
      sourceKind: "generated_edit" as const,
    };

    state = transitionHtmlAudioSession(state, {
      cursorMs: 0,
      source,
      type: "SourceConfigured",
    }).state;
    state = transitionHtmlAudioSession(state, {
      intent,
      request: postEditLoopRequest,
      type: "PostEditAutoplayRequested",
    }).state;
    state = transitionHtmlAudioSession(state, {
      durationMs: 1000,
      sourceFilename: "clip one.mp3",
      type: "PostEditReadyConfirmed",
    }).state;
    state = transitionHtmlAudioSession(state, {
      request: postEditLoopRequest,
      type: "StartRequested",
    }).state;

    let transition = transitionHtmlAudioSession(state, {
      intent,
      request: postEditLoopRequest,
      type: "PostEditAutoplayRequested",
    });
    expect(transition).toEqual({ state, effects: [] });

    transition = transitionHtmlAudioSession(transition.state, {
      nowMs: 120,
      sourceFilename: "clip one.mp3",
      type: "PlayResolved",
    });
    expect(transition.state).toMatchObject({
      kind: "playing",
      request: postEditLoopRequest,
    });
  });

  it("seeks instead of reloading post-edit full-source repeat restarts", () => {
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
      request: postEditLoopRequest,
      type: "StartRequested",
    }).state;
    state = transitionHtmlAudioSession(state, {
      nowMs: 120,
      sourceFilename: "clip one.mp3",
      type: "PlayResolved",
    }).state;

    const restarting = transitionHtmlAudioSession(state, {
      cursorMs: 1000,
      repeatEnabled: true,
      repeatPauseMs: 0,
      resetCursorMs: 0,
      restartAudio: true,
      type: "BoundaryReached",
    });

    expect(restarting.state).toMatchObject({
      kind: "starting",
      request: postEditLoopRequest,
    });
    expect(restarting.effects).toContainEqual({ cursorMs: 0, type: "SeekAudio" });
    expect(restarting.effects).toContainEqual({ type: "PlayAudio" });
    expect(restarting.effects).not.toContainEqual({ type: "ReloadAudioSource" });
  });
});
