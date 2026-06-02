import { describe, expect, it } from "vitest";

import {
  fullTimeViewport,
  isFullTimeViewport,
  msVisibleInViewport,
  normalizeTimeViewport,
  panTimeViewport,
  timeViewportSpan,
  zoomTimeViewport,
  zoomTimeViewportAroundRatio,
  zoomTimeViewportToRange,
} from "../src/editor-inline/time-viewport.js";

describe("editor inline time viewport", () => {
  it("normalizes invalid and oversized ranges to the full duration", () => {
    expect(fullTimeViewport(2000)).toEqual({ startMs: 0, endMs: 2000, durationMs: 2000 });
    expect(normalizeTimeViewport(-500, 5000, 2000)).toEqual({ startMs: 0, endMs: 2000, durationMs: 2000 });
    expect(normalizeTimeViewport(900, 100, 1000)).toEqual({ startMs: 100, endMs: 900, durationMs: 1000 });
    expect(normalizeTimeViewport(0, 0, 1000)).toEqual({ startMs: 0, endMs: 250, durationMs: 1000 });
  });

  it("zooms horizontally around an anchor without changing duration", () => {
    const viewport = fullTimeViewport(4000);

    expect(zoomTimeViewport(viewport, 1000, 2)).toEqual({ startMs: 500, endMs: 2500, durationMs: 4000 });
    expect(zoomTimeViewport(viewport, 3000, 2)).toEqual({ startMs: 1500, endMs: 3500, durationMs: 4000 });
  });

  it("zooms around a pointer ratio and clamps at clip edges", () => {
    const viewport = fullTimeViewport(4000);

    expect(zoomTimeViewportAroundRatio(viewport, 0.25, 2)).toEqual({ startMs: 500, endMs: 2500, durationMs: 4000 });
    expect(zoomTimeViewportAroundRatio({ startMs: 0, endMs: 1000, durationMs: 4000 }, 0, 2)).toEqual({
      startMs: 0,
      endMs: 500,
      durationMs: 4000,
    });
  });

  it("pans by milliseconds and clamps to the full duration", () => {
    const viewport = { startMs: 1000, endMs: 2000, durationMs: 4000 };

    expect(panTimeViewport(viewport, 500)).toEqual({ startMs: 1500, endMs: 2500, durationMs: 4000 });
    expect(panTimeViewport(viewport, -5000)).toEqual({ startMs: 0, endMs: 1000, durationMs: 4000 });
    expect(panTimeViewport(viewport, 5000)).toEqual({ startMs: 3000, endMs: 4000, durationMs: 4000 });
  });

  it("zooms to a selected range with padding while respecting the minimum window", () => {
    expect(zoomTimeViewportToRange(1000, 1400, 4000)).toEqual({ startMs: 960, endMs: 1440, durationMs: 4000 });
    expect(zoomTimeViewportToRange(1000, 1050, 4000)).toEqual({ startMs: 900, endMs: 1150, durationMs: 4000 });
  });

  it("reports full state, span, and visibility", () => {
    const full = fullTimeViewport(1200);
    const zoomed = { startMs: 200, endMs: 800, durationMs: 1200 };

    expect(isFullTimeViewport(full)).toBe(true);
    expect(isFullTimeViewport(zoomed)).toBe(false);
    expect(timeViewportSpan(zoomed)).toBe(600);
    expect(msVisibleInViewport(200, zoomed)).toBe(true);
    expect(msVisibleInViewport(800, zoomed)).toBe(true);
    expect(msVisibleInViewport(801, zoomed)).toBe(false);
  });
});
