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

describe("html audio post-edit pass", () => {
  it("reports post-edit pass completion without transport-owned repeat", () => {
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

    const completed = transitionHtmlAudioSession(state, {
      cursorMs: 1000,
      resetCursorMs: 0,
      type: "BoundaryReached",
    });

    expect(completed.state).toMatchObject({ cursorMs: 0, kind: "ready" });
    expect(completed.effects).toContainEqual({ request: postEditLoopRequest, type: "ReportPassCompleted" });
    expect(completed.effects).not.toContainEqual({ type: "PlayAudio" });
  });
});
