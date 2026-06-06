import { describe, expect, it } from "vitest";

import {
  normalizeSelectionShiftMarkers,
  resolveSelectionMarkerShift,
} from "../src/editor-inline/selection-marker-shift.js";

describe("selection marker shift", () => {
  it("moves each edge to the nearest marker in the requested direction", () => {
    expect(
      resolveSelectionMarkerShift({ startMs: 333, endMs: 667 }, "start", "previous", [0, 333, 500, 667], 1000),
    ).toMatchObject({
      disabledReason: null,
      nextRange: { startMs: 0, endMs: 667 },
      targetMarkerMs: 0,
    });
    expect(
      resolveSelectionMarkerShift({ startMs: 333, endMs: 667 }, "start", "next", [0, 333, 500, 667], 1000),
    ).toMatchObject({
      disabledReason: null,
      nextRange: { startMs: 500, endMs: 667 },
      targetMarkerMs: 500,
    });
    expect(
      resolveSelectionMarkerShift({ startMs: 333, endMs: 667 }, "end", "previous", [0, 333, 500, 667], 1000),
    ).toMatchObject({
      disabledReason: null,
      nextRange: { startMs: 333, endMs: 500 },
      targetMarkerMs: 500,
    });
    expect(
      resolveSelectionMarkerShift({ startMs: 333, endMs: 667 }, "end", "next", [0, 333, 500, 667, 1000], 1000),
    ).toMatchObject({
      disabledReason: null,
      nextRange: { startMs: 333, endMs: 1000 },
      targetMarkerMs: 1000,
    });
  });

  it("reports missing markers on the requested side", () => {
    expect(
      resolveSelectionMarkerShift({ startMs: 0, endMs: 500 }, "start", "previous", [0, 500, 1000], 1000),
    ).toMatchObject({
      disabledReason: "no_previous",
      nextRange: null,
      targetMarkerMs: null,
    });
    expect(
      resolveSelectionMarkerShift({ startMs: 500, endMs: 1000 }, "end", "next", [0, 500, 1000], 1000),
    ).toMatchObject({
      disabledReason: "no_next",
      nextRange: null,
      targetMarkerMs: null,
    });
  });

  it("distinguishes crossing the opposite edge from making the region too short", () => {
    expect(
      resolveSelectionMarkerShift({ startMs: 333, endMs: 667 }, "start", "next", [667], 1000),
    ).toMatchObject({
      disabledReason: "crosses_other_edge",
      nextRange: null,
      targetMarkerMs: 667,
    });
    expect(
      resolveSelectionMarkerShift({ startMs: 333, endMs: 667 }, "start", "next", [640], 1000),
    ).toMatchObject({
      disabledReason: "too_short",
      nextRange: null,
      targetMarkerMs: 640,
    });
    expect(
      resolveSelectionMarkerShift({ startMs: 333, endMs: 667 }, "end", "previous", [333], 1000),
    ).toMatchObject({
      disabledReason: "crosses_other_edge",
      nextRange: null,
      targetMarkerMs: 333,
    });
    expect(
      resolveSelectionMarkerShift({ startMs: 333, endMs: 667 }, "end", "previous", [360], 1000),
    ).toMatchObject({
      disabledReason: "too_short",
      nextRange: null,
      targetMarkerMs: 360,
    });
  });

  it("rounds, clamps, sorts, and deduplicates marker input", () => {
    expect(normalizeSelectionShiftMarkers([501.6, 500.6, 1001, -20, 502, 500.6], 1000)).toEqual([
      0,
      501,
      502,
      1000,
    ]);
  });
});
