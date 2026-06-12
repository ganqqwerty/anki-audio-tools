import { afterEach, describe, expect, it, vi } from "vitest";

import { initialFieldState } from "../src/editor-inline/field-state.js";
import { removeFieldState, writeFieldState } from "../src/editor-inline/field-state-store.js";
import { PLOT, xForMs } from "../src/editor-inline/plot.js";
import { applyVisualizerTimeViewport } from "../src/editor-inline/viewport-actions.js";
import {
  renderCursor,
  renderVisualizerTrack,
  renderPlaybackCursor,
  resetCursorProjection,
  startPlaybackCursorTransition,
} from "../src/editor-inline/visualizer-renderer.js";
import { renderSelection } from "../src/editor-inline/visualizer-selection-renderer.js";
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
  afterEach(() => {
    removeFieldState(0);
    document.body.innerHTML = "";
  });

  it("renders pitch text for voiced cursors and unvoiced gaps", () => {
    const visualizer = mountVisualizer(voicedTrack);
    const current = visualizer.querySelector<HTMLElement>(".aqe-css-cursor-flag-current")!;
    const pitch = visualizer.querySelector<HTMLElement>(".aqe-css-cursor-flag-pitch")!;

    renderCursor(visualizer, 500, voicedTrack.durationMs);

    expect(current.textContent).toBe("500 ms");
    expect(pitch.textContent).toBe(" / 180 Hz");
    expect(visualizer.querySelector(".aqe-cursor-label")).toHaveTextContent("500 ms / 180 Hz");

    visualizer.__aqeTrack = gappedTrack;
    renderCursor(visualizer, 250, gappedTrack.durationMs);

    expect(current.textContent).toBe("250 ms");
    expect(pitch.textContent).toBe(" / -- Hz");
  });

  it("resets the CSS cursor projection", () => {
    const visualizer = mountVisualizer(voicedTrack);
    const cssCursor = visualizer.querySelector<HTMLElement>(".aqe-css-cursor")!;
    const current = visualizer.querySelector<HTMLElement>(".aqe-css-cursor-flag-current")!;
    const pitch = visualizer.querySelector<HTMLElement>(".aqe-css-cursor-flag-pitch")!;

    renderCursor(visualizer, 500, voicedTrack.durationMs);
    resetCursorProjection(visualizer);

    expect(cssCursor.style.transform).toBe(`translate3d(${PLOT.left.toFixed(2)}px, 0, 0)`);
    expect(current.textContent).toBe("0 ms");
    expect(pitch.textContent).toBe(" / -- Hz");
  });

  it("clamps the CSS flag inside the plot", () => {
    const visualizer = mountVisualizer(voicedTrack);
    const flag = visualizer.querySelector<HTMLElement>(".aqe-css-cursor-flag")!;

    renderCursor(visualizer, 0, voicedTrack.durationMs);

    expect(flag.style.transform).toBe("translateX(0.00px)");

    renderCursor(visualizer, voicedTrack.durationMs, voicedTrack.durationMs);

    expect(flag.style.transform).toBe("translateX(-82.00px)");
  });

  it("throttles playback cursor text separately from cursor position", () => {
    const visualizer = mountVisualizer(voicedTrack);
    const cssCursor = visualizer.querySelector<HTMLElement>(".aqe-css-cursor")!;
    const current = visualizer.querySelector<HTMLElement>(".aqe-css-cursor-flag-current")!;

    renderPlaybackCursor(visualizer, 0, voicedTrack.durationMs, 0);
    renderPlaybackCursor(visualizer, 100, voicedTrack.durationMs, 10);

    expect(cssCursor.style.transform).toBe(`translate3d(${xForMs(100, voicedTrack.durationMs).toFixed(2)}px, 0, 0)`);
    expect(current.textContent).toBe("0 ms");

    renderPlaybackCursor(visualizer, 100, voicedTrack.durationMs, 17);

    expect(cssCursor.style.transform).toBe(`translate3d(${xForMs(100, voicedTrack.durationMs).toFixed(2)}px, 0, 0)`);
    expect(current.textContent).toBe("0 ms");

    renderPlaybackCursor(visualizer, 200, voicedTrack.durationMs, 110);

    expect(cssCursor.style.transform).toBe(`translate3d(${xForMs(200, voicedTrack.durationMs).toFixed(2)}px, 0, 0)`);
    expect(current.textContent).toBe("200 ms");
  });

  it("starts compositor cursor playback transitions without per-frame SVG geometry writes", () => {
    const visualizer = mountVisualizer(voicedTrack);
    const cssCursor = visualizer.querySelector<HTMLElement>(".aqe-css-cursor")!;

    startPlaybackCursorTransition(visualizer, 100, 900);

    expect(cssCursor.style.transition).toBe("transform 800ms linear");
    expect(cssCursor.style.transform).toBe(`translate3d(${xForMs(900, voicedTrack.durationMs).toFixed(2)}px, 0, 0)`);
  });

  it("keeps pitch state off the visible CSS cursor", () => {
    const visualizer = mountVisualizer(voicedTrack);
    const cssCursor = visualizer.querySelector<HTMLElement>(".aqe-css-cursor")!;

    renderCursor(visualizer, 500, voicedTrack.durationMs);

    expect(visualizer.querySelector(".aqe-css-cursor-pitch-marker")).toBeNull();
    expect(visualizer.querySelector(".aqe-cursor, .aqe-cursor-flag")).toBeNull();
    expect(visualizer.querySelector(".aqe-cursor-pitch-marker")).toBeNull();
    expect(cssCursor.style.transform).toBe(`translate3d(${xForMs(500, voicedTrack.durationMs).toFixed(2)}px, 0, 0)`);

    startPlaybackCursorTransition(visualizer, 500, 900);

    expect(visualizer.querySelector(".aqe-css-cursor-pitch-marker")).toBeNull();
    expect(cssCursor.style.transform).toBe(`translate3d(${xForMs(900, voicedTrack.durationMs).toFixed(2)}px, 0, 0)`);
  });

  it("reuses cached cursor nodes during repeated playback paints", () => {
    const visualizer = mountVisualizer(voicedTrack);
    const querySpy = vi.spyOn(visualizer, "querySelector");

    renderPlaybackCursor(visualizer, 100, voicedTrack.durationMs, 0);
    const firstPaintQueries = querySpy.mock.calls.length;
    renderPlaybackCursor(visualizer, 200, voicedTrack.durationMs, 110);

    expect(firstPaintQueries).toBeGreaterThan(0);
    expect(querySpy.mock.calls).toHaveLength(firstPaintQueries);
  });

  it("keeps direct cursor renders immediate after playback throttling", () => {
    const visualizer = mountVisualizer(voicedTrack);
    const current = visualizer.querySelector<HTMLElement>(".aqe-css-cursor-flag-current")!;

    renderPlaybackCursor(visualizer, 100, voicedTrack.durationMs, 0);
    renderPlaybackCursor(visualizer, 200, voicedTrack.durationMs, 40);
    renderCursor(visualizer, 700, voicedTrack.durationMs);

    expect(current.textContent).toBe("700 ms");
  });

  it("redraws graph x positions through the visualizer viewport without changing pitch y scale", () => {
    const visualizer = mountVisualizer(voicedTrack);

    renderVisualizerTrack(visualizer, voicedTrack);
    const fullPath = visualizer.querySelector<SVGPathElement>(".aqe-pitch-path")?.getAttribute("d") || "";
    applyVisualizerTimeViewport(visualizer, { startMs: 0, endMs: 500, durationMs: 1000 });
    const zoomedPath = visualizer.querySelector<SVGPathElement>(".aqe-pitch-path")?.getAttribute("d") || "";

    expect(fullPath).toContain("L 310.00 80.80");
    expect(zoomedPath).toContain("L 610.00 80.80");
  });

  it("syncs the plot clip and x-axis to the rendered SVG width", () => {
    const visualizer = mountVisualizer(voicedTrack);
    const svg = visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg")!;
    setSvgBounds(svg, 1240);

    renderVisualizerTrack(visualizer, voicedTrack);

    const intensity = visualizer.querySelector<SVGPathElement>(".aqe-intensity")!;
    const clipRect = visualizer.querySelector<SVGRectElement>("clipPath > rect")!;
    const lastTick = Array.from(visualizer.querySelectorAll<SVGLineElement>(".aqe-x-tick")).at(-1)!;
    expect(svg.getAttribute("viewBox")).toBe("0 0 1240 150");
    expect(clipRect.getAttribute("width")).toBe("1220");
    expect(intensity.getAttribute("d")).toContain("L 1230.00 116.00 Z");
    expect(lastTick.getAttribute("x1")).toBe("1230.00");
  });

  it("clips selection rendering to the visible viewport while preserving selected milliseconds", () => {
    const visualizer = mountVisualizer(voicedTrack);
    visualizer.dataset.targetDurationMs = "1000";
    visualizer.dataset.viewportStartMs = "250";
    visualizer.dataset.viewportEndMs = "750";

    renderSelection(visualizer, { startMs: 100, endMs: 500, mode: "selection" }, null);

    const band = visualizer.querySelector<SVGRectElement>(".aqe-selection")!;
    expect(band.getAttribute("visibility")).toBe("visible");
    expect(band.getAttribute("x")).toBe(PLOT.left.toFixed(2));
    expect(Number(band.getAttribute("width"))).toBeGreaterThan(0);
    const plot = visualizer.querySelector<HTMLElement>(".aqe-visualizer-plot")!;
    expect(plot.dataset.selectionOverlayReady).toBe("true");
    expect(plot.dataset.selectionStartEdgeVisible).toBe("false");
    expect(plot.dataset.selectionEndEdgeVisible).toBe("true");
    expect(plot.style.getPropertyValue("--aqe-selection-end-edge-px")).not.toBe("");
  });

  it("flags narrow selections to hide the inner marker-shift buttons", () => {
    const visualizer = mountVisualizer(voicedTrack);

    renderSelection(visualizer, { startMs: 480, endMs: 530, mode: "selection" }, null);

    const plot = visualizer.querySelector<HTMLElement>(".aqe-visualizer-plot")!;
    expect(plot.dataset.selectionShiftHideInner).toBe("true");
  });

  it("hides the visible cursor when the cursor is outside the zoomed viewport", () => {
    const visualizer = mountVisualizer(voicedTrack);
    const cssCursor = visualizer.querySelector<HTMLElement>(".aqe-css-cursor")!;
    visualizer.dataset.viewportStartMs = "250";
    visualizer.dataset.viewportEndMs = "750";

    renderCursor(visualizer, 900, voicedTrack.durationMs);

    expect(cssCursor.style.display).toBe("none");
  });
});

function mountVisualizer(track: NormalizedProsodyTrack): VisualizerElement {
  document.body.innerHTML = `
    <div class="aqe-visualizer" data-aqe-field-ord="0" data-duration-ms="${track.durationMs}" data-target-duration-ms="${track.durationMs}">
      <div class="aqe-visualizer-plot">
        <svg class="aqe-visualizer-svg" viewBox="0 0 ${PLOT.width} ${PLOT.height}">
          <defs>
            <clipPath>
              <rect
                x="${PLOT.left}"
                y="${PLOT.top}"
                width="${PLOT.width - PLOT.left - PLOT.right}"
                height="${PLOT.height - PLOT.top - PLOT.bottom}"
              ></rect>
            </clipPath>
          </defs>
          <rect class="aqe-selection" x="${PLOT.left}" y="${PLOT.top}" width="0" height="${PLOT.height - PLOT.top - PLOT.bottom}" visibility="hidden"></rect>
          <path class="aqe-intensity"></path>
          <g class="aqe-pitch"></g>
          <g class="aqe-learner-pitch"></g>
          <rect class="aqe-selection-outside-preview-before" visibility="hidden"></rect>
          <rect class="aqe-selection-outside-preview-after" visibility="hidden"></rect>
          <g class="aqe-labels"></g>
          <g class="aqe-x-axis"></g>
          <line class="aqe-selection-start" visibility="hidden"></line>
          <line class="aqe-selection-end" visibility="hidden"></line>
          <rect class="aqe-selection-resize-start" visibility="hidden"></rect>
          <rect class="aqe-selection-resize-end" visibility="hidden"></rect>
          <g class="aqe-selection-resize-grip-start" visibility="hidden"></g>
          <g class="aqe-selection-resize-grip-end" visibility="hidden"></g>
        </svg>
      </div>
      <div class="aqe-css-cursor">
        <div class="aqe-css-cursor-line"></div>
        <div class="aqe-css-cursor-flag">
          <div class="aqe-css-cursor-flag-box">
            <span class="aqe-css-cursor-flag-current">0 ms</span>
            <span class="aqe-css-cursor-flag-pitch"> / -- Hz</span>
          </div>
        </div>
      </div>
      <span class="aqe-cursor-label"></span>
    </div>
  `;
  const visualizer = document.querySelector<VisualizerElement>(".aqe-visualizer");
  if (!visualizer) throw new Error("visualizer fixture did not mount");
  visualizer.__aqeTrack = track;
  const initial = initialFieldState({ ord: 0, sourceFilename: track.sourceFilename });
  writeFieldState(0, {
    ...initial,
    graph: {
      ...initial.graph,
      active: true,
      analyzerName: track.analyzerName,
      durationMs: track.durationMs,
      hasTrack: true,
    },
    playback: {
      ...initial.playback,
      endMs: track.durationMs,
    },
  });
  return visualizer;
}

function setSvgBounds(svg: SVGSVGElement, width: number): void {
  svg.getBoundingClientRect = () => ({
    bottom: PLOT.height,
    height: PLOT.height,
    left: 0,
    right: width,
    top: 0,
    width,
    x: 0,
    y: 0,
    toJSON: () => ({}),
  });
}
