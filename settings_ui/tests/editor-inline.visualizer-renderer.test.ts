import { describe, expect, it, vi } from "vitest";

import { PLOT, xForMs } from "../src/editor-inline/plot.js";
import {
  renderCursor,
  renderPlaybackCursor,
  resetCursorProjection,
  startPlaybackCursorTransition,
} from "../src/editor-inline/visualizer-renderer.js";
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

    expect(cssCursor.style.transform).toBe("");
    expect(current.textContent).toBe("0 ms");

    renderPlaybackCursor(visualizer, 100, voicedTrack.durationMs, 17);

    expect(cssCursor.style.transform).toBe("");
    expect(current.textContent).toBe("0 ms");

    renderPlaybackCursor(visualizer, 200, voicedTrack.durationMs, 110);

    expect(cssCursor.style.transform).toBe("");
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
});

function mountVisualizer(track: NormalizedProsodyTrack): VisualizerElement {
  document.body.innerHTML = `
    <div class="aqe-visualizer" data-duration-ms="${track.durationMs}">
      <svg class="aqe-visualizer-svg"></svg>
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
  return visualizer;
}
