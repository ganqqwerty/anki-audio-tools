import { describe, expect, it } from "vitest";

import { resolveSelectionAutoAdvanceBoundary } from "../src/editor-inline/selection-auto-advance.js";

describe("selection auto-advance", () => {
  it("counts repeats until the configured threshold", () => {
    expect(resolveSelectionAutoAdvanceBoundary({
      autoAdvance: true,
      markersMs: [0, 500],
      repeatCount: 2,
      repeatPassesCompleted: 0,
      selection: { startMs: 500, endMs: 1000 },
    })).toEqual({
      action: "repeat",
      nextRepeatPassesCompleted: 1,
      nextSelection: null,
    });
  });

  it("moves the selection start to the nearest marker on threshold", () => {
    expect(resolveSelectionAutoAdvanceBoundary({
      autoAdvance: true,
      markersMs: [0, 250, 500],
      repeatCount: 2,
      repeatPassesCompleted: 1,
      selection: { startMs: 500, endMs: 1000 },
    })).toEqual({
      action: "advance",
      nextRepeatPassesCompleted: 0,
      nextSelection: { startMs: 250, endMs: 1000 },
    });
  });

  it("stops at the leftmost marker instead of wrapping", () => {
    expect(resolveSelectionAutoAdvanceBoundary({
      autoAdvance: true,
      markersMs: [0, 500],
      repeatCount: 2,
      repeatPassesCompleted: 1,
      selection: { startMs: 0, endMs: 1000 },
    })).toEqual({
      action: "complete",
      nextRepeatPassesCompleted: 0,
      nextSelection: null,
    });
  });

  it("ignores full playback or disabled auto-advance", () => {
    expect(resolveSelectionAutoAdvanceBoundary({
      autoAdvance: false,
      markersMs: [0, 500],
      repeatCount: 2,
      repeatPassesCompleted: 1,
      selection: { startMs: 500, endMs: 1000 },
    })).toEqual({
      action: "ignore",
      nextRepeatPassesCompleted: 1,
      nextSelection: null,
    });
  });
});
