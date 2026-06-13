import { describe, expect, it, afterEach } from "vitest";

import { syncFieldStateToDom } from "../src/editor-inline/field-state-dom-sync.js";
import { initialFieldState, graphRendered } from "../src/editor-inline/field-state.js";
import { readFieldState, initFieldState } from "../src/editor-inline/field-state-store.js";
import type { VisualizerElement } from "../src/editor-inline/types.js";

function mountVisualizer(ord = 0, durationMs = 1000): VisualizerElement {
  document.body.innerHTML = `
    <div class="aqe-visualizer"
         data-aqe-field-ord="${ord}"
         data-duration-ms="${durationMs}"
         data-target-duration-ms="${durationMs}">
    </div>
  `;
  return document.querySelector<VisualizerElement>(".aqe-visualizer")!;
}

describe("field state DOM sync", () => {
  afterEach(() => {
    document.body.innerHTML = "";
  });

  it("projects graph state onto dataset attributes", () => {
    const vis = mountVisualizer(0, 1500);
    initFieldState(0, initialFieldState({ ord: 0 }));

    syncFieldStateToDom(0, graphRendered(readFieldState(0), {
      analyzerName: "praat",
      cursorMs: 500,
      durationMs: 1500,
      sourceFilename: "test.wav",
    }));

    expect(vis.dataset.graphActive).toBe("true");
    expect(vis.dataset.graphBusy).toBe("false");
    expect(vis.dataset.hasTrack).toBe("true");
    expect(vis.dataset.durationMs).toBe("1500");
    expect(vis.dataset.analyzerName).toBe("praat");
    expect(vis.dataset.sourceFilename).toBe("test.wav");
  });

  it("projects cursor state onto dataset attributes", () => {
    const vis = mountVisualizer(0);
    const state = {
      ...initialFieldState({ ord: 0 }),
      cursor: { anchorMs: 100, ms: 200, progressMs: 300 },
    };

    syncFieldStateToDom(0, state);

    expect(vis.dataset.anchorMs).toBe("100");
    expect(vis.dataset.cursorMs).toBe("200");
    expect(vis.dataset.progressMs).toBe("300");
  });

  it("projects playback state onto dataset attributes", () => {
    const vis = mountVisualizer(0);
    const state = {
      ...initialFieldState({ ord: 0 }),
      playback: {
        clockMode: "audio" as const,
        engine: "html" as const,
        endMs: 800,
        regionMode: "selection" as const,
        repeat: true,
        resumeRequiresRestart: false,
        startMs: 200,
        state: "playing" as const,
      },
    };

    syncFieldStateToDom(0, state);

    expect(vis.dataset.playbackState).toBe("playing");
    expect(vis.dataset.playbackEngine).toBe("html");
    expect(vis.dataset.playbackStartMs).toBe("200");
    expect(vis.dataset.playbackEndMs).toBe("800");
    expect(vis.dataset.playbackRegionMode).toBe("selection");
    expect(vis.dataset.resumeRequiresRestart).toBe("false");
    expect(vis.dataset.repeatEnabled).toBe("true");
    expect(vis.dataset.progressClockMode).toBe("audio");
  });

  it("projects selection state onto dataset attributes", () => {
    const vis = mountVisualizer(0);
    const state = {
      ...initialFieldState({ ord: 0 }),
      selection: {
        active: true,
        draftActive: true,
        draftEndMs: 700,
        draftStartMs: 200,
        endMs: 875,
        startMs: 125,
      },
    };

    syncFieldStateToDom(0, state);

    expect(vis.dataset.selectionActive).toBe("true");
    expect(vis.dataset.selectionStartMs).toBe("125");
    expect(vis.dataset.selectionEndMs).toBe("875");
    expect(vis.dataset.selectionDraftActive).toBe("true");
    expect(vis.dataset.selectionDraftStartMs).toBe("200");
    expect(vis.dataset.selectionDraftEndMs).toBe("700");
  });

  it("deletes null selection fields from dataset", () => {
    const vis = mountVisualizer(0);
    vis.dataset.selectionStartMs = "100";
    vis.dataset.selectionEndMs = "200";

    const state = initialFieldState({ ord: 0 });
    syncFieldStateToDom(0, state);

    expect(vis.dataset.selectionStartMs).toBeUndefined();
    expect(vis.dataset.selectionEndMs).toBeUndefined();
    expect(vis.dataset.selectionActive).toBe("false");
  });

  it("does nothing when visualizer element is not in the DOM", () => {
    document.body.innerHTML = "";
    const state = initialFieldState({ ord: 99 });
    expect(() => syncFieldStateToDom(99, state)).not.toThrow();
  });
});
