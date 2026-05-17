import { describe, expect, it } from "vitest";

import {
  buildPlaybackRequestForPython,
  clampMsToRegion,
  playbackRegionForCompletion,
  shouldLoopAtBoundary,
  type PlaybackRequestState,
} from "../src/editor-inline/playback-state.js";

const baseState: PlaybackRequestState = {
  anchorMs: 250,
  currentProgressMs: null,
  cursorMs: 250,
  engine: "html",
  ord: 0,
  playbackState: "stopped",
  region: { startMs: 0, endMs: 1000, mode: "full" },
  repeat: false,
  resumeRequiresRestart: false,
};

describe("playback state", () => {
  it("builds a full-region start request from the anchor", () => {
    expect(buildPlaybackRequestForPython(baseState)).toEqual({
      action: "start",
      cursorMs: 250,
      endMs: 1000,
      engine: "html",
      loop: false,
      ord: 0,
      regionMode: "full",
    });
  });

  it("starts selected-region playback from the selection start", () => {
    expect(buildPlaybackRequestForPython({
      ...baseState,
      region: { startMs: 400, endMs: 800, mode: "selection" },
      repeat: true,
    })).toMatchObject({
      action: "start",
      cursorMs: 400,
      endMs: 800,
      loop: true,
      regionMode: "selection",
    });
  });

  it("turns playing into a pause request at current progress", () => {
    expect(buildPlaybackRequestForPython({
      ...baseState,
      currentProgressMs: 375,
      playbackState: "playing",
    })).toMatchObject({
      action: "pause",
      cursorMs: 375,
    });
  });

  it("resumes paused playback unless restart is required or progress left selection", () => {
    expect(buildPlaybackRequestForPython({
      ...baseState,
      currentProgressMs: 500,
      playbackState: "paused",
      region: { startMs: 400, endMs: 800, mode: "selection" },
    })).toMatchObject({ action: "resume", cursorMs: 500 });

    expect(buildPlaybackRequestForPython({
      ...baseState,
      currentProgressMs: 900,
      playbackState: "paused",
      region: { startMs: 400, endMs: 800, mode: "selection" },
    })).toMatchObject({ action: "start", cursorMs: 400 });

    expect(buildPlaybackRequestForPython({
      ...baseState,
      playbackState: "paused",
      resumeRequiresRestart: true,
      region: { startMs: 400, endMs: 800, mode: "selection" },
    })).toMatchObject({ action: "start", cursorMs: 400 });
  });

  it("keeps small completion and loop decisions pure", () => {
    const region = { startMs: 400, endMs: 800, mode: "selection" as const };

    expect(clampMsToRegion(900, region)).toBe(800);
    expect(playbackRegionForCompletion(region, 250, "selection")).toBe(400);
    expect(playbackRegionForCompletion(region, 250, "full")).toBe(250);
    expect(shouldLoopAtBoundary(800, 800, true)).toBe(true);
    expect(shouldLoopAtBoundary(799, 800, true)).toBe(false);
  });
});
