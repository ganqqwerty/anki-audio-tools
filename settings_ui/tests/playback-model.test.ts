import { describe, expect, it } from "vitest";

import {
  planPlaybackBoundary,
  planPlaybackPass,
  planPlaybackRequest,
  playbackCompletionCursor,
  type PlaybackPass,
  type PlaybackSnapshot,
} from "../src/editor-inline/playback-model.js";

const baseSnapshot: PlaybackSnapshot = {
  anchorMs: 250,
  currentProgressMs: null,
  cursorMs: 250,
  durationMs: 1000,
  engine: "html",
  ord: 0,
  playbackState: "stopped",
  region: { startMs: 0, endMs: 1000, mode: "full" },
  repeat: false,
  resumeRequiresRestart: false,
};

describe("playback model", () => {
  it("starts stopped full playback from the anchor cursor", () => {
    expect(planPlaybackRequest(baseSnapshot)).toEqual({
      action: "start",
      cursorMs: 250,
      endMs: 1000,
      engine: "html",
      loop: false,
      ord: 0,
      regionMode: "full",
    });
  });

  it("starts stopped selected playback from the selection start", () => {
    expect(planPlaybackRequest({
      ...baseSnapshot,
      cursorMs: 650,
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

  it("starts full-cover selected playback from a moved cursor as full playback", () => {
    expect(planPlaybackRequest({
      ...baseSnapshot,
      anchorMs: 650,
      currentProgressMs: 650,
      cursorMs: 650,
      region: { startMs: 0, endMs: 1000, mode: "selection" },
    })).toMatchObject({
      action: "start",
      cursorMs: 650,
      endMs: 1000,
      regionMode: "full",
    });
  });

  it("turns playing playback into a pause request at current progress", () => {
    expect(planPlaybackRequest({
      ...baseSnapshot,
      currentProgressMs: 375.4,
      playbackState: "playing",
    })).toMatchObject({
      action: "pause",
      cursorMs: 375,
    });
  });

  it("resumes paused non-repeat playback from current progress", () => {
    expect(planPlaybackRequest({
      ...baseSnapshot,
      currentProgressMs: 500,
      playbackState: "paused",
      region: { startMs: 400, endMs: 800, mode: "selection" },
    })).toMatchObject({
      action: "resume",
      cursorMs: 500,
      regionMode: "selection",
    });
  });

  it("restarts paused selected repeat playback from the selection start", () => {
    expect(planPlaybackRequest({
      ...baseSnapshot,
      currentProgressMs: 650,
      cursorMs: 650,
      playbackState: "paused",
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

  it("restarts paused selected playback from the repositioned cursor clamped into the region", () => {
    expect(planPlaybackRequest({
      ...baseSnapshot,
      anchorMs: 900,
      cursorMs: 900,
      playbackState: "paused",
      region: { startMs: 400, endMs: 800, mode: "selection" },
      resumeRequiresRestart: true,
    })).toMatchObject({
      action: "start",
      cursorMs: 800,
      endMs: 800,
      regionMode: "selection",
    });
  });

  it("ignores a repositioned paused cursor when restarting selected repeat playback", () => {
    expect(planPlaybackRequest({
      ...baseSnapshot,
      anchorMs: 650,
      currentProgressMs: 650,
      cursorMs: 650,
      playbackState: "paused",
      region: { startMs: 400, endMs: 800, mode: "selection" },
      repeat: true,
      resumeRequiresRestart: true,
    })).toMatchObject({
      action: "start",
      cursorMs: 400,
      endMs: 800,
      loop: true,
      regionMode: "selection",
    });
  });

  it("restarts paused selected repeat from the selection start when progress is past the segment", () => {
    expect(planPlaybackRequest({
      ...baseSnapshot,
      currentProgressMs: 900,
      cursorMs: 650,
      playbackState: "paused",
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

  it("rounds selected repeat restart boundaries from fractional segment times", () => {
    expect(planPlaybackRequest({
      ...baseSnapshot,
      currentProgressMs: 650.4,
      cursorMs: 650.4,
      playbackState: "paused",
      region: { startMs: 400.6, endMs: 800.4, mode: "selection" },
      repeat: true,
    })).toMatchObject({
      action: "start",
      cursorMs: 401,
      endMs: 800,
      loop: true,
      regionMode: "selection",
    });
  });

  it("keeps full-cover selected repeat resume cursor semantics", () => {
    expect(planPlaybackRequest({
      ...baseSnapshot,
      currentProgressMs: 650,
      cursorMs: 650,
      playbackState: "paused",
      region: { startMs: 0, endMs: 1000, mode: "selection" },
      repeat: true,
    })).toMatchObject({
      action: "resume",
      cursorMs: 650,
      endMs: 1000,
      loop: true,
      regionMode: "full",
    });
  });

  it("preserves HTML playback engine when restarting paused selected repeat", () => {
    expect(planPlaybackRequest({
      ...baseSnapshot,
      currentProgressMs: 650,
      cursorMs: 650,
      engine: "html",
      playbackState: "paused",
      region: { startMs: 400, endMs: 800, mode: "selection" },
      repeat: true,
    })).toMatchObject({
      action: "start",
      cursorMs: 400,
      engine: "html",
      loop: true,
    });
  });

  it("restarts paused resume at selection start when progress left the selection", () => {
    expect(planPlaybackRequest({
      ...baseSnapshot,
      currentProgressMs: 900,
      playbackState: "paused",
      region: { startMs: 400, endMs: 800, mode: "selection" },
    })).toMatchObject({
      action: "start",
      cursorMs: 400,
      regionMode: "selection",
    });
  });

  it("plans an active playback pass with a selected completion reset cursor", () => {
    expect(planPlaybackPass({
      ...baseSnapshot,
      region: { startMs: 400, endMs: 800, mode: "selection" },
      repeat: true,
    }, 650)).toEqual({
      endMs: 800,
      loop: true,
      regionMode: "selection",
      resetCursorMs: 400,
      startMs: 650,
    });
  });

  it("keeps boundary playback active before pass end", () => {
    const pass = selectedPass();

    expect(planPlaybackBoundary({
      nextMs: 799,
      pass,
      repeat: true,
      repeatPauseMs: 0,
    })).toEqual({ kind: "continue" });
  });

  it("repeats at boundary from the pass reset cursor when repeat is enabled", () => {
    const pass = selectedPass();

    expect(planPlaybackBoundary({
      nextMs: 800,
      pass,
      repeat: true,
      repeatPauseMs: 250,
    })).toEqual({
      kind: "loop",
      pass: {
        ...pass,
        startMs: 400,
      },
      repeatPauseMs: 250,
    });
  });

  it("restarts a resumed selected loop from the selection start after the current pass", () => {
    const pass = planPlaybackPass({
      ...baseSnapshot,
      cursorMs: 650,
      region: { startMs: 400, endMs: 800, mode: "selection" },
      repeat: true,
    }, 650);

    expect(planPlaybackBoundary({
      nextMs: 800,
      pass,
      repeat: true,
      repeatPauseMs: 0,
    })).toEqual({
      kind: "loop",
      pass: {
        ...pass,
        startMs: 400,
      },
      repeatPauseMs: 0,
    });
  });

  it("completes selected playback at boundary and resets to selection start", () => {
    const pass = selectedPass();

    expect(planPlaybackBoundary({
      nextMs: 800,
      pass,
      repeat: false,
      repeatPauseMs: 0,
    })).toEqual({
      kind: "complete",
      resetCursorMs: 400,
    });
    expect(playbackCompletionCursor(pass)).toBe(400);
  });

  it("completes full playback at boundary and resets to anchor", () => {
    const pass = planPlaybackPass(baseSnapshot, 250);

    expect(planPlaybackBoundary({
      nextMs: 1000,
      pass,
      repeat: false,
      repeatPauseMs: 0,
    })).toEqual({
      kind: "complete",
      resetCursorMs: 250,
    });
    expect(playbackCompletionCursor(pass)).toBe(250);
  });
});

function selectedPass(): PlaybackPass {
  return planPlaybackPass({
    ...baseSnapshot,
    region: { startMs: 400, endMs: 800, mode: "selection" },
    repeat: true,
  }, 400);
}
