import { describe, expect, it } from "vitest";

import {
  MAX_ZOOMED_OUT_TIME_MS_PER_PIXEL,
  fullTimeViewport,
  hasScrollableTimeRange,
  isFullTimeViewport,
  maxZoomedOutViewportSpan,
  msVisibleInViewport,
  normalizeTimeViewport,
  panTimeViewport,
  timeViewportSpan,
  zoomTimeViewport,
  zoomTimeViewportAroundRatio,
  zoomTimeViewportToRange,
} from "../src/editor-inline/time-viewport.js";

describe("editor inline time viewport", () => {
  it("keeps full fit as an explicit duration-clamped viewport", () => {
    expect(fullTimeViewport(2000)).toEqual({ startMs: 0, endMs: 2000, durationMs: 2000 });
    expect(fullTimeViewport(Number.NaN)).toEqual({ startMs: 0, endMs: 0, durationMs: 0 });
  });

  it("caps zoomed-out viewports from rendered plot width", () => {
    expect(MAX_ZOOMED_OUT_TIME_MS_PER_PIXEL).toBe(25);
    expect(maxZoomedOutViewportSpan(600)).toBe(15000);
  });

  it("normalizes visible timeline windows without clamping end to duration", () => {
    expect(normalizeTimeViewport(-500, 5000, 2000)).toEqual({ startMs: 0, endMs: 5500, durationMs: 2000 });
    expect(normalizeTimeViewport(900, 100, 1000)).toEqual({ startMs: 100, endMs: 900, durationMs: 1000 });
    expect(normalizeTimeViewport(0, 0, 1000)).toEqual({ startMs: 0, endMs: 250, durationMs: 1000 });
    expect(normalizeTimeViewport(0, 0, 100)).toEqual({ startMs: 0, endMs: 250, durationMs: 100 });
    expect(normalizeTimeViewport(0, 0, 0)).toEqual({ startMs: 0, endMs: 0, durationMs: 0 });
  });

  it("zooms horizontally around an anchor and respects a supplied max span", () => {
    const viewport = fullTimeViewport(4000);

    expect(zoomTimeViewport(viewport, 1000, 2)).toEqual({ startMs: 500, endMs: 2500, durationMs: 4000 });
    expect(zoomTimeViewport(viewport, 3000, 2)).toEqual({ startMs: 1500, endMs: 3500, durationMs: 4000 });
    expect(zoomTimeViewport({ startMs: 0, endMs: 500, durationMs: 500 }, 250, 0.1, { maxSpanMs: 1000 })).toEqual({
      startMs: 0,
      endMs: 1000,
      durationMs: 500,
    });
  });

  it("zooms around a pointer ratio and clamps at clip edges when span is narrower than audio", () => {
    const viewport = fullTimeViewport(4000);

    expect(zoomTimeViewportAroundRatio(viewport, 0.25, 2)).toEqual({ startMs: 500, endMs: 2500, durationMs: 4000 });
    expect(zoomTimeViewportAroundRatio({ startMs: 0, endMs: 1000, durationMs: 4000 }, 0, 2)).toEqual({
      startMs: 0,
      endMs: 500,
      durationMs: 4000,
    });
  });

  it("pans only when the visible span is narrower than the audio duration", () => {
    const viewport = { startMs: 1000, endMs: 2000, durationMs: 4000 };

    expect(panTimeViewport(viewport, 500)).toEqual({ startMs: 1500, endMs: 2500, durationMs: 4000 });
    expect(panTimeViewport(viewport, -5000)).toEqual({ startMs: 0, endMs: 1000, durationMs: 4000 });
    expect(panTimeViewport(viewport, 5000)).toEqual({ startMs: 3000, endMs: 4000, durationMs: 4000 });
    expect(panTimeViewport({ startMs: 0, endMs: 1875, durationMs: 500 }, 500)).toEqual({
      startMs: 0,
      endMs: 1875,
      durationMs: 500,
    });
  });

  it("zooms to a selected range with padding while respecting min and max spans", () => {
    expect(zoomTimeViewportToRange(1000, 1400, 4000)).toEqual({ startMs: 960, endMs: 1440, durationMs: 4000 });
    expect(zoomTimeViewportToRange(1000, 1050, 4000)).toEqual({ startMs: 900, endMs: 1150, durationMs: 4000 });
    expect(zoomTimeViewportToRange(0, 4000, 4000, { maxSpanMs: 1000 })).toEqual({
      startMs: 1500,
      endMs: 2500,
      durationMs: 4000,
    });
  });

  it("reports full coverage, scrollability, span, and visibility", () => {
    const full = fullTimeViewport(1200);
    const canonicalShort = { startMs: 0, endMs: 1875, durationMs: 500 };
    const zoomed = { startMs: 200, endMs: 800, durationMs: 1200 };

    expect(isFullTimeViewport(full)).toBe(true);
    expect(isFullTimeViewport(canonicalShort)).toBe(true);
    expect(isFullTimeViewport(zoomed)).toBe(false);
    expect(hasScrollableTimeRange(full)).toBe(false);
    expect(hasScrollableTimeRange(canonicalShort)).toBe(false);
    expect(hasScrollableTimeRange(zoomed)).toBe(true);
    expect(timeViewportSpan(zoomed)).toBe(600);
    expect(msVisibleInViewport(200, zoomed)).toBe(true);
    expect(msVisibleInViewport(800, zoomed)).toBe(true);
    expect(msVisibleInViewport(801, zoomed)).toBe(false);
  });
});
