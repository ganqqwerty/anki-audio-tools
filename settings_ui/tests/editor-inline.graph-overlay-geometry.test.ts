import { describe, expect, it } from "vitest";

import { PLOT, graphPixelBounds } from "../src/editor-inline/plot.js";
import {
  markerClickFromEvent,
  markerProjections,
  visibleRangeProjection,
} from "../src/editor-inline/graph-overlay-geometry.js";
import type { TimeViewport } from "../src/editor-inline/time-viewport.js";

const viewport: TimeViewport = {
  durationMs: 4000,
  endMs: 3000,
  startMs: 1000,
};

function testSvg(): SVGSVGElement {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.getBoundingClientRect = () => ({
    bottom: 150,
    height: 150,
    left: 10,
    right: 630,
    top: 0,
    width: 620,
    x: 10,
    y: 0,
    toJSON: () => ({}),
  });
  return svg;
}

describe("editor inline graph overlay geometry", () => {
  it("maps marker-row clicks through the current viewport", () => {
    const svg = testSvg();
    const bounds = graphPixelBounds(svg);

    expect(markerClickFromEvent({ clientX: bounds.left }, svg, viewport, { startMs: 1000, endMs: 3000 })).toEqual({
      insideVisibleBaseRegion: true,
      ms: 1000,
    });
    expect(markerClickFromEvent(
      { clientX: bounds.left + bounds.width / 2 },
      svg,
      viewport,
      { startMs: 1500, endMs: 2500 },
    )).toEqual({
      insideVisibleBaseRegion: true,
      ms: 2000,
    });
    expect(markerClickFromEvent({ clientX: bounds.left }, svg, viewport, { startMs: 1500, endMs: 2500 })).toEqual({
      insideVisibleBaseRegion: false,
      ms: 1000,
    });
  });

  it("projects markers by viewport and hides off-viewport markers without deleting them", () => {
    expect(markerProjections([500, 1000, 2000, 3000, 3500], viewport, PLOT)).toEqual([
      { ms: 500, visible: false, x: PLOT.left },
      { ms: 1000, visible: true, x: PLOT.left },
      { ms: 2000, visible: true, x: PLOT.left + (PLOT.width - PLOT.left - PLOT.right) / 2 },
      { ms: 3000, visible: true, x: PLOT.width - PLOT.right },
      { ms: 3500, visible: false, x: PLOT.width - PLOT.right },
    ]);
  });

  it("clips range projection to the visible viewport", () => {
    expect(visibleRangeProjection({ startMs: 1500, endMs: 2500 }, viewport, PLOT)).toEqual({
      endMs: 2500,
      endX: PLOT.left + ((PLOT.width - PLOT.left - PLOT.right) * 0.75),
      startMs: 1500,
      startX: PLOT.left + ((PLOT.width - PLOT.left - PLOT.right) * 0.25),
    });
    expect(visibleRangeProjection({ startMs: 500, endMs: 1500 }, viewport, PLOT)).toEqual({
      endMs: 1500,
      endX: PLOT.left + ((PLOT.width - PLOT.left - PLOT.right) * 0.25),
      startMs: 1000,
      startX: PLOT.left,
    });
    expect(visibleRangeProjection({ startMs: 3200, endMs: 3500 }, viewport, PLOT)).toBeNull();
  });
});
