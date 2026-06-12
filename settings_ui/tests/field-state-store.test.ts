import { describe, expect, it, afterEach, vi } from "vitest";

import { visualizerForOrd } from "../src/editor-inline/dom-selectors.js";
import { initialFieldState } from "../src/editor-inline/field-state.js";
import {
  hasFieldState,
  initFieldState,
  invalidateFieldState,
  readFieldState,
  removeFieldState,
  setCachedProgressMs,
  updateFieldState,
  writeFieldState,
} from "../src/editor-inline/field-state-store.js";
import { syncFieldStateToDom } from "../src/editor-inline/field-state-dom-sync.js";

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
    vi.restoreAllMocks();
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

  it("readFieldState initializes a default state and ignores DOM field-state attributes", () => {
    mountVisualizer(1, 2000);
    const visualizer = visualizerForOrd(1);
    invalidateFieldState(1);
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
    expect(state.graph.active).toBe(false);
    expect(state.graph.hasTrack).toBe(false);
    expect(state.graph.durationMs).toBe(0);
    expect(state.cursor.ms).toBe(0);
    expect(state.playback.state).toBe("stopped");
    expect(state.sourceFilename).toBe("");
    expect(state.selection.active).toBe(false);
    expect(state.selection.startMs).toBeNull();
    expect(state.selection.endMs).toBeNull();
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

  it("does not use direct DOM writes as source of truth after invalidate", () => {
    mountVisualizer(0, 1000);
    initFieldState(0, initialFieldState({ ord: 0 }));

    const vis = visualizerForOrd(0)!;
    vis.dataset.cursorMs = "900";
    vis.dataset.progressMs = "900";
    invalidateFieldState(0);

    expect(readFieldState(0).cursor.ms).toBe(0);
    expect(readFieldState(0).cursor.progressMs).toBe(0);
    expect(vis.dataset.cursorMs).toBe("900");
  });

  it("writeFieldState remains canonical when DOM is stale", () => {
    mountVisualizer(0, 1000);
    initFieldState(0, initialFieldState({ ord: 0 }));

    const vis = visualizerForOrd(0)!;

    // write through store — cache = 300
    writeFieldState(0, {
      ...readFieldState(0),
      cursor: { ...readFieldState(0).cursor, ms: 300 },
    });
    expect(readFieldState(0).cursor.ms).toBe(300);

    // direct DOM write bypasses store
    vis.dataset.cursorMs = "900";
    vis.dataset.progressMs = "900";

    // cached read returns stale value
    expect(readFieldState(0).cursor.ms).toBe(300);

    invalidateFieldState(0);
    expect(readFieldState(0).cursor.ms).toBe(0);
  });

  it("syncFieldStateToDom projects all fields including ones unchanged since init", () => {
    mountVisualizer(0, 1000);
    const state = initialFieldState({ ord: 0 });
    syncFieldStateToDom(0, state);

    const vis = visualizerForOrd(0)!;
    // Even fields that were never explicitly set are written
    expect(vis.dataset.graphActive).toBe("false");
    expect(vis.dataset.cursorMs).toBe("0");
    expect(vis.dataset.selectionActive).toBe("false");
    expect(vis.dataset.playbackRegionMode).toBe("full");
  });

  it("setCachedProgressMs updates progressMs in both cache and DOM", () => {
    mountVisualizer(0, 1000);
    initFieldState(0, initialFieldState({ ord: 0 }));

    setCachedProgressMs(0, 420.6);

    expect(readFieldState(0).cursor.progressMs).toBe(421);
    expect(visualizerForOrd(0)!.dataset.progressMs).toBe("421");
  });

  it("setCachedProgressMs keeps the cache warm — no DOM rebuild on next read", () => {
    mountVisualizer(0, 1000);
    // Warm the cache with a distinctive sourceFilename via the store.
    writeFieldState(0, {
      ...readFieldState(0),
      sourceFilename: "warm.wav",
    });

    const vis = visualizerForOrd(0)!;
    // A direct DOM write that a rebuild WOULD pick up. If setCachedProgressMs
    // invalidated the entry, the next read would rebuild and observe this.
    vis.dataset.sourceFilename = "stale-from-dom.wav";

    setCachedProgressMs(0, 250);

    // progressMs reflects the update...
    expect(readFieldState(0).cursor.progressMs).toBe(250);
    // ...but the cache was NOT re-cooled: the direct-DOM sourceFilename change
    // is not observed, proving no rebuildFieldStateFromDom occurred.
    expect(readFieldState(0).sourceFilename).toBe("warm.wav");
  });

  it("setCachedProgressMs writes DOM even when no cache entry exists", () => {
    mountVisualizer(0, 1000);
    invalidateFieldState(0);

    setCachedProgressMs(0, 333);

    expect(visualizerForOrd(0)!.dataset.progressMs).toBe("333");
    expect(readFieldState(0).cursor.progressMs).toBe(333);
  });

  it("setCachedProgressMs uses a supplied visualizer without querying the DOM", () => {
    mountVisualizer(0, 1000);
    initFieldState(0, initialFieldState({ ord: 0 }));
    const visualizer = visualizerForOrd(0)!;
    const querySelector = vi.spyOn(document, "querySelector");

    setCachedProgressMs(0, 125.4, visualizer);

    expect(querySelector).not.toHaveBeenCalled();
    expect(visualizer.dataset.progressMs).toBe("125");
    expect(readFieldState(0).cursor.progressMs).toBe(125);
  });

  it("hasFieldState returns false for unknown ordinals", () => {
    expect(hasFieldState(999)).toBe(false);
  });
});
