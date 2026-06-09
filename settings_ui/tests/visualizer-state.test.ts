import { describe, expect, it, afterEach } from "vitest";

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
import { readFieldState } from "../src/editor-inline/field-state-store.js";
import type { VisualizerElement } from "../src/editor-inline/types.js";

function visualizer(): VisualizerElement {
  const el = document.createElement("div") as VisualizerElement;
  el.className = "aqe-visualizer";
  el.dataset.aqeFieldOrd = "0";
  document.body.append(el);
  return el;
}

describe("visualizer state adapter", () => {
  afterEach(() => {
    document.body.innerHTML = "";
  });
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
    node.dataset.durationMs = "1000";
    node.dataset.targetDurationMs = "1000";

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

    const s = readFieldState(0);
    expect(s.playback.startMs).toBe(123);
    expect(s.playback.endMs).toBe(988);
    expect(s.playback.regionMode).toBe("selection");
    expect(s.playback.resumeRequiresRestart).toBe(true);

    setVisualizerResumeRequiresRestart(node, false);

    expect(readFieldState(0).playback.resumeRequiresRestart).toBe(false);
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
