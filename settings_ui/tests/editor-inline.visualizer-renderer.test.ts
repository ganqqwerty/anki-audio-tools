import { describe, expect, it } from "vitest";

import { PLOT, xForMs, yForPitch } from "../src/editor-inline/plot.js";
import { renderCursor, resetCursorProjection } from "../src/editor-inline/visualizer-renderer.js";
import type { NormalizedProsodyTrack, VisualizerElement } from "../src/editor-inline/types.js";

const voicedTrack: NormalizedProsodyTrack = {
  analyzerName: "praat",
  durationMs: 1000,
  pitchMaxHz: 300,
  pitchMinHz: 100,
  points: [
    [0, 120, 0.1, true],
    [500, 180, 0.8, true],
    [1000, 220, 0.6, true],
  ],
  sourceFilename: "clip.wav",
};

const gappedTrack: NormalizedProsodyTrack = {
  ...voicedTrack,
  points: [
    [0, 120, 0.1, true],
    [200, null, 0, false],
    [400, 180, 0.6, true],
  ],
};

describe("editor inline visualizer renderer", () => {
  it("places the pitch marker on voiced cursor pitch and hides it across unvoiced gaps", () => {
    const visualizer = mountVisualizer(voicedTrack);
    const marker = visualizer.querySelector<SVGCircleElement>(".aqe-cursor-pitch-marker")!;

    renderCursor(visualizer, 500, voicedTrack.durationMs);

    expect(marker).toHaveAttribute("visibility", "visible");
    expect(marker).toHaveAttribute("cx", xForMs(500, voicedTrack.durationMs).toFixed(2));
    expect(marker).toHaveAttribute("cy", yForPitch(180, 100, 300).toFixed(2));

    visualizer.__aqeTrack = gappedTrack;
    renderCursor(visualizer, 250, gappedTrack.durationMs);

    expect(marker).toHaveAttribute("visibility", "hidden");
    expect(marker).toHaveAttribute("cx", String(PLOT.left));
    expect(marker).toHaveAttribute("cy", String(PLOT.height - PLOT.bottom));
  });

  it("clears the pitch marker when the cursor projection resets", () => {
    const visualizer = mountVisualizer(voicedTrack);
    const marker = visualizer.querySelector<SVGCircleElement>(".aqe-cursor-pitch-marker")!;

    renderCursor(visualizer, 500, voicedTrack.durationMs);
    resetCursorProjection(visualizer);

    expect(marker).toHaveAttribute("visibility", "hidden");
    expect(marker).toHaveAttribute("cx", String(PLOT.left));
    expect(marker).toHaveAttribute("cy", String(PLOT.height - PLOT.bottom));
  });

  it("aligns the cursor line with the current-position flag notch at the start", () => {
    const visualizer = mountVisualizer(voicedTrack);
    const cursor = visualizer.querySelector<SVGLineElement>(".aqe-cursor")!;
    const flag = visualizer.querySelector<SVGGElement>(".aqe-cursor-flag")!;
    const notch = visualizer.querySelector<SVGPathElement>(".aqe-cursor-flag-notch")!;

    renderCursor(visualizer, 0, voicedTrack.durationMs);

    expect(globalNotchX(flag, notch)).toBe(Number(cursor.getAttribute("x1")));
  });
});

function mountVisualizer(track: NormalizedProsodyTrack): VisualizerElement {
  document.body.innerHTML = `
    <div class="aqe-visualizer" data-duration-ms="${track.durationMs}">
      <svg>
        <line class="aqe-cursor" x1="${PLOT.left}" x2="${PLOT.left}"></line>
        <circle class="aqe-cursor-pitch-marker" cx="${PLOT.left}" cy="${PLOT.height - PLOT.bottom}" visibility="hidden"></circle>
        <g class="aqe-cursor-flag" visibility="hidden">
          <rect class="aqe-cursor-flag-box"></rect>
          <path class="aqe-cursor-flag-notch"></path>
          <text>
            <tspan class="aqe-cursor-flag-current">0 ms</tspan>
            <tspan class="aqe-cursor-flag-pitch"> / -- Hz</tspan>
          </text>
        </g>
      </svg>
      <span class="aqe-cursor-label"></span>
    </div>
  `;
  const visualizer = document.querySelector<VisualizerElement>(".aqe-visualizer");
  if (!visualizer) throw new Error("visualizer fixture did not mount");
  visualizer.__aqeTrack = track;
  return visualizer;
}

function globalNotchX(flag: SVGGElement, notch: SVGPathElement): number {
  return translateX(flag) + translateX(notch);
}

function translateX(element: SVGElement): number {
  const transform = element.getAttribute("transform") ?? "";
  const match = /translate\((-?\d+(?:\.\d+)?)/.exec(transform);
  return match ? Number(match[1]) : 0;
}
