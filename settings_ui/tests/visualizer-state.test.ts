import { describe, expect, it } from "vitest";

import {
  clearVisualizerSelection,
  clearVisualizerSelectionDraft,
  readVisualizerCursorMs,
  readVisualizerDurationMs,
  readVisualizerRepeatEnabled,
  readVisualizerSelectionState,
  setVisualizerPlaybackRegion,
  setVisualizerResumeRequiresRestart,
  setVisualizerSelection,
  setVisualizerSelectionDraft,
} from "../src/editor-inline/visualizer-state.js";
import type { VisualizerElement } from "../src/editor-inline/types.js";

function visualizer(): VisualizerElement {
  return document.createElement("div") as VisualizerElement;
}

describe("visualizer state adapter", () => {
  it("reads numeric and boolean graph fields with safe defaults", () => {
    const node = visualizer();

    expect(readVisualizerDurationMs(node)).toBe(0);
    expect(readVisualizerCursorMs(node)).toBe(0);
    expect(readVisualizerRepeatEnabled(node)).toBe(false);

    node.dataset.durationMs = "1500";
    node.dataset.cursorMs = "250";
    node.dataset.repeatEnabled = "true";

    expect(readVisualizerDurationMs(node)).toBe(1500);
    expect(readVisualizerCursorMs(node)).toBe(250);
    expect(readVisualizerRepeatEnabled(node)).toBe(true);
  });

  it("round-trips committed and draft selection state", () => {
    const node = visualizer();

    setVisualizerSelection(node, { startMs: 125, endMs: 875 });
    setVisualizerSelectionDraft(node, { startMs: 200, endMs: 700 });

    expect(readVisualizerSelectionState(node)).toEqual({
      active: true,
      draftActive: true,
      draftEndMs: 700,
      draftStartMs: 200,
      endMs: 875,
      startMs: 125,
    });

    clearVisualizerSelectionDraft(node);
    clearVisualizerSelection(node);

    expect(readVisualizerSelectionState(node)).toEqual({
      active: false,
      draftActive: false,
      draftEndMs: null,
      draftStartMs: null,
      endMs: null,
      startMs: null,
    });
  });

  it("keeps playback region and restart flags behind typed writers", () => {
    const node = visualizer();

    setVisualizerPlaybackRegion(node, { startMs: 123.4, endMs: 987.6, mode: "selection" });
    setVisualizerResumeRequiresRestart(node, true);

    expect(node.dataset.playbackStartMs).toBe("123");
    expect(node.dataset.playbackEndMs).toBe("988");
    expect(node.dataset.playbackRegionMode).toBe("selection");
    expect(node.dataset.resumeRequiresRestart).toBe("true");

    setVisualizerResumeRequiresRestart(node, false);

    expect(node.dataset.resumeRequiresRestart).toBe("false");
  });

  it("treats invalid optional selection timestamps as absent", () => {
    const node = visualizer();
    node.dataset.selectionActive = "true";
    node.dataset.selectionStartMs = "not-a-number";
    node.dataset.selectionEndMs = "500";

    expect(readVisualizerSelectionState(node)).toMatchObject({
      active: true,
      startMs: null,
      endMs: 500,
    });
  });
});
