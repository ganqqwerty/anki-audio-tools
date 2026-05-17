import { describe, expect, it } from "vitest";

import {
  PLOT,
  cursorMsFromEvent,
  drawLabels,
  drawPitch,
  drawXAxis,
  formatTime,
  graphPixelBounds,
  pathForIntensity,
  pitchSegments,
  xForMs,
  yForPitch,
} from "../src/editor-inline/plot.js";
import type { NormalizedProsodyTrack } from "../src/editor-inline/types.js";

const track: NormalizedProsodyTrack = {
  analyzerName: "praat",
  durationMs: 1000,
  pitchMinHz: 100,
  pitchMaxHz: 300,
  sourceFilename: "clip.mp3",
  points: [
    [0, 120, 0.1, true],
    [100, 140, 0.5, true],
    [200, null, 0, false],
    [300, 240, 0.8, true],
    [400, 260, 1, true],
  ],
};

describe("editor inline plot helpers", () => {
  it("maps time and pitch into finite plot coordinates", () => {
    expect(xForMs(500, 1000)).toBeCloseTo(PLOT.left + (PLOT.width - PLOT.left - PLOT.right) / 2);
    expect(xForMs(1500, 1000)).toBe(PLOT.width - PLOT.right);
    expect(yForPitch(300, 100, 300)).toBe(PLOT.top);
    expect(yForPitch(null, 100, 300)).toBe(PLOT.height - PLOT.bottom);
    expect(formatTime(500, 1000)).toBe("500 ms");
    expect(formatTime(2500, 3000)).toBe("2.50s");
  });

  it("renders intensity and pitch segments without NaN", () => {
    const intensity = pathForIntensity(track.points, track.durationMs);
    const segments = pitchSegments(track.points, track.durationMs, track.pitchMinHz, track.pitchMaxHz);

    expect(intensity).toMatch(/^M /);
    expect(intensity).not.toContain("NaN");
    expect(segments).toHaveLength(2);
    expect(segments[0]).toHaveLength(2);
    expect(segments[1]).toHaveLength(2);
  });

  it("draws pitch paths, hertz labels, and x axis labels", () => {
    document.body.innerHTML = `
      <div class="aqe-visualizer">
        <svg>
          <g class="aqe-pitch"></g>
          <g class="aqe-labels"></g>
          <g class="aqe-x-axis"></g>
        </svg>
      </div>
    `;
    const visualizer = document.querySelector<HTMLElement>(".aqe-visualizer")!;

    drawPitch(visualizer, track);
    drawLabels(visualizer, track);
    drawXAxis(visualizer, track.durationMs);

    expect(visualizer.querySelectorAll(".aqe-pitch-path")).toHaveLength(2);
    expect(Array.from(visualizer.querySelectorAll(".aqe-hz-label")).map((node) => node.textContent)).toEqual([
      "300 Hz",
      "100 Hz",
    ]);
    expect(Array.from(visualizer.querySelectorAll(".aqe-x-label")).map((node) => node.textContent)).toEqual([
      "0 ms",
      "500 ms",
      "1000 ms",
    ]);
  });

  it("uses rendered SVG bounds for cursor hit testing", () => {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.getBoundingClientRect = () => ({
      bottom: 150,
      height: 150,
      left: 10,
      right: 770,
      top: 0,
      width: 760,
      x: 10,
      y: 0,
      toJSON: () => ({}),
    });

    const bounds = graphPixelBounds(svg);
    const ms = cursorMsFromEvent({ clientX: bounds.left + bounds.width * 0.75 }, svg, 2000);

    expect(ms).toBeCloseTo(1500);
  });
});
