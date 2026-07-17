import { describe, expect, it } from "vitest";

import {
  htmlAudioBoundaryMsForRequest,
  htmlAudioProgressDecision,
  htmlAudioProgressMs,
  type HtmlAudioProgressClock,
} from "../src/editor-inline/html-audio-session-progress.js";
import type { HtmlAudioSessionState, HtmlAudioStartRequest } from "../src/editor-inline/html-audio-session-types.js";

const source = {
  kind: "source" as const,
  sourceFilename: "clip.ogg",
};

const learnerSource = {
  attemptId: 3,
  kind: "learner_recording" as const,
  sourceFilename: "learner.ogg",
  startCursorMs: 1200,
};

const request: HtmlAudioStartRequest = {
  cursorMs: 0,
  endMs: 1000,
  loop: false,
  ord: 0,
  regionMode: "full",
  source: "user",
};

const clock: HtmlAudioProgressClock = {
  cursorMs: 200,
  endMs: 1000,
  startedAtMs: 5000,
};

describe("html audio session progress", () => {
  it("uses the farthest measured progress and clamps to the clock end", () => {
    expect(htmlAudioProgressMs(clock, 5300, 250)).toBe(500);
    expect(htmlAudioProgressMs(clock, 5100, 650)).toBe(650);
    expect(htmlAudioProgressMs(clock, 8000, 400)).toBe(1000);
  });

  it("keeps transport boundaries at the immutable pass end", () => {
    expect(htmlAudioBoundaryMsForRequest(request, 1000, 1000)).toBe(1000);
    expect(htmlAudioBoundaryMsForRequest({ ...request, loop: true }, 1000, 1000)).toBe(960);
    expect(htmlAudioBoundaryMsForRequest({ ...request, cursorMs: 100 }, 1000, 1000)).toBe(1000);
  });

  it("returns source progress until the computed boundary is reached", () => {
    const state = playingSourceState();
    const decision = htmlAudioProgressDecision({
      audioProgressMs: 400,
      clock,
      graphDurationMs: 1000,
      nowMs: 5200,
      state,
    });

    expect(decision).toEqual({
      kind: "source_progress",
      progressMs: 400,
    });
  });

  it("does not complete a pass from wall time while media currentTime is stalled", () => {
    const state = playingSourceState();
    const decision = htmlAudioProgressDecision({
      audioProgressMs: 400,
      clock,
      graphDurationMs: 1000,
      nowMs: 8000,
      state,
    });

    expect(decision).toEqual({
      kind: "source_progress",
      progressMs: 1000,
    });
  });

  it("returns a transport-only boundary event when source progress reaches the end", () => {
    const state = playingSourceState();
    const decision = htmlAudioProgressDecision({
      audioProgressMs: 1000,
      clock,
      graphDurationMs: 1000,
      nowMs: 5200,
      state,
    });

    expect(decision).toEqual({
      event: {
        cursorMs: 1000,
        resetCursorMs: 0,
        type: "BoundaryReached",
      },
      kind: "boundary",
      progressMs: 1000,
    });
  });

  it("projects learner playback progress onto the learner recording cursor", () => {
    const state: HtmlAudioSessionState = {
      durationMs: 700,
      kind: "playing",
      request: { ...request, endMs: 700, source: "learner_recording" },
      source: learnerSource,
      startedAtMs: 5000,
      ord: 0,
    };

    expect(htmlAudioProgressDecision({
      audioProgressMs: 300,
      clock: { cursorMs: 0, endMs: 700, startedAtMs: 5000 },
      graphDurationMs: 700,
      nowMs: 5250,
      state,
    })).toEqual({
      kind: "learner_progress",
      learnerCursorMs: 1500,
      progressMs: 300,
    });
  });
});

function playingSourceState(): Extract<HtmlAudioSessionState, { kind: "playing" }> {
  return {
    durationMs: 1000,
    kind: "playing",
    ord: 0,
    request,
    source,
    startedAtMs: 5000,
  };
}
