import { describe, expect, it, afterEach } from "vitest";

import { visualizerForOrd } from "../src/editor-inline/dom-selectors.js";
import { initialFieldState } from "../src/editor-inline/field-state.js";
import {
  hasFieldState,
  initFieldState,
  readFieldState,
  removeFieldState,
  updateFieldState,
  writeFieldState,
} from "../src/editor-inline/field-state-store.js";

function mountVisualizer(ord = 0, durationMs = 1000): void {
  document.body.innerHTML = `
    <div class="aqe-visualizer"
         data-aqe-field-ord="${ord}"
         data-duration-ms="${durationMs}"
         data-target-duration-ms="${durationMs}">
    </div>
  `;
}

describe("field state store", () => {
  afterEach(() => {
    document.body.innerHTML = "";
  });

  it("initFieldState stores and syncs initial state to DOM", () => {
    mountVisualizer(1, 1500);
    const state = initialFieldState({ ord: 1 });
    const result = initFieldState(1, state);

    expect(result.ord).toBe(1);
    expect(result.graph.durationMs).toBe(0);

    const visualizer = visualizerForOrd(1);
    expect(visualizer?.dataset.graphActive).toBe("false");
    expect(visualizer?.dataset.hasTrack).toBe("false");
    expect(visualizer?.dataset.playbackState).toBe("stopped");
    expect(visualizer?.dataset.sourceFilename).toBe("");
  });

  it("readFieldState rebuilds from DOM dataset", () => {
    mountVisualizer(1, 2000);
    const visualizer = visualizerForOrd(1);
    visualizer!.dataset.graphActive = "true";
    visualizer!.dataset.graphBusy = "false";
    visualizer!.dataset.hasTrack = "true";
    visualizer!.dataset.cursorMs = "500";
    visualizer!.dataset.playbackState = "playing";
    visualizer!.dataset.sourceFilename = "test.wav";
    visualizer!.dataset.selectionActive = "true";
    visualizer!.dataset.selectionStartMs = "100";
    visualizer!.dataset.selectionEndMs = "900";

    const state = readFieldState(1);
    expect(state.graph.active).toBe(true);
    expect(state.graph.hasTrack).toBe(true);
    expect(state.graph.durationMs).toBe(2000);
    expect(state.cursor.ms).toBe(500);
    expect(state.playback.state).toBe("playing");
    expect(state.sourceFilename).toBe("test.wav");
    expect(state.selection.active).toBe(true);
    expect(state.selection.startMs).toBe(100);
    expect(state.selection.endMs).toBe(900);
  });

  it("readFieldState returns default state when visualizer not found", () => {
    const state = readFieldState(99);
    expect(state.ord).toBe(99);
    expect(state.graph.hasTrack).toBe(false);
    expect(state.playback.state).toBe("stopped");
  });

  it("writeFieldState updates store and syncs to DOM", () => {
    mountVisualizer(2, 3000);
    initFieldState(2, initialFieldState({ ord: 2 }));

    const state = readFieldState(2);
    const updated = {
      ...state,
      graph: { ...state.graph, active: true, hasTrack: true },
      playback: { ...state.playback, state: "playing" as const },
      cursor: { ...state.cursor, ms: 750 },
    };
    writeFieldState(2, updated);

    const reread = readFieldState(2);
    expect(reread.graph.active).toBe(true);
    expect(reread.playback.state).toBe("playing");
    expect(reread.cursor.ms).toBe(750);

    const visualizer = visualizerForOrd(2);
    expect(visualizer?.dataset.graphActive).toBe("true");
    expect(visualizer?.dataset.playbackState).toBe("playing");
    expect(visualizer?.dataset.cursorMs).toBe("750");
  });

  it("updateFieldState applies a reducer and syncs to DOM", () => {
    mountVisualizer(3, 1000);
    initFieldState(3, initialFieldState({ ord: 3 }));

    updateFieldState(3, (state) => ({
      ...state,
      graph: { ...state.graph, hasTrack: true },
      sourceFilename: "updated.wav",
    }));

    const state = readFieldState(3);
    expect(state.graph.hasTrack).toBe(true);
    expect(state.sourceFilename).toBe("updated.wav");

    const visualizer = visualizerForOrd(3);
    expect(visualizer?.dataset.hasTrack).toBe("true");
    expect(visualizer?.dataset.sourceFilename).toBe("updated.wav");
  });

  it("removeFieldState removes state from the store", () => {
    mountVisualizer(4);
    initFieldState(4, initialFieldState({ ord: 4 }));
    expect(hasFieldState(4)).toBe(true);

    removeFieldState(4);
    expect(hasFieldState(4)).toBe(false);
  });

  it("hasFieldState returns false for unknown ordinals", () => {
    expect(hasFieldState(999)).toBe(false);
  });
});
