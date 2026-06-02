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
  pitchHzAtMs,
  pitchSegments,
  xForMs,
  yForPitch,
} from "../src/editor-inline/plot.js";
import { msVisibleInViewport } from "../src/editor-inline/time-viewport.js";
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

  it("interpolates the pitch under the cursor and returns no pitch across unvoiced gaps", () => {
    expect(pitchHzAtMs(track.points, -50)).toBe(120);
    expect(pitchHzAtMs(track.points, 100)).toBe(140);
    expect(pitchHzAtMs(track.points, 50)).toBeCloseTo(130);
    expect(pitchHzAtMs(track.points, 250)).toBeNull();
    expect(pitchHzAtMs(track.points, 350)).toBeCloseTo(250);
    expect(pitchHzAtMs(track.points, 1000)).toBe(260);
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
    svg.setAttribute("viewBox", "0 0 760 150");
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

    expect(bounds.left).toBeCloseTo(54);
    expect(bounds.width).toBeCloseTo(706);
    expect(ms).toBeCloseTo(1500);
  });

  it("maps time into the visible viewport when provided", () => {
    const viewport = { startMs: 1000, endMs: 3000, durationMs: 4000 };

    expect(xForMs(1000, 4000, viewport)).toBe(PLOT.left);
    expect(xForMs(2000, 4000, viewport)).toBeCloseTo(PLOT.left + (PLOT.width - PLOT.left - PLOT.right) / 2);
    expect(xForMs(3000, 4000, viewport)).toBe(PLOT.width - PLOT.right);
  });

  it("uses visible viewport bounds for pointer hit testing", () => {
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

    const viewport = { startMs: 1000, endMs: 3000, durationMs: 4000 };
    const bounds = graphPixelBounds(svg);

    expect(cursorMsFromEvent({ clientX: bounds.left }, svg, 4000, viewport)).toBe(1000);
    expect(cursorMsFromEvent({ clientX: bounds.left + bounds.width / 2 }, svg, 4000, viewport)).toBe(2000);
    expect(cursorMsFromEvent({ clientX: bounds.left + bounds.width }, svg, 4000, viewport)).toBe(3000);
  });

  it("clamps x coordinates separately from viewport cursor visibility", () => {
    const viewport = { startMs: 1000, endMs: 3000, durationMs: 4000 };

    expect(xForMs(500, 4000, viewport)).toBe(PLOT.left);
    expect(xForMs(3500, 4000, viewport)).toBe(PLOT.width - PLOT.right);
    expect(msVisibleInViewport(1000, viewport)).toBe(true);
    expect(msVisibleInViewport(3000, viewport)).toBe(true);
    expect(msVisibleInViewport(999, viewport)).toBe(false);
    expect(msVisibleInViewport(3001, viewport)).toBe(false);
  });

  it("draws visible x-axis labels from the viewport without changing default full-axis labels", () => {
    document.body.innerHTML = `
      <div class="aqe-visualizer">
        <svg>
          <g class="aqe-x-axis"></g>
        </svg>
      </div>
    `;
    const visualizer = document.querySelector<HTMLElement>(".aqe-visualizer")!;

    drawXAxis(visualizer, 4000, { startMs: 1000, endMs: 3000, durationMs: 4000 });

    expect(Array.from(visualizer.querySelectorAll(".aqe-x-label")).map((node) => node.textContent)).toEqual([
      "1.00s",
      "2.00s",
      "3.00s",
    ]);
  });
});
