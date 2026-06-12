import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  clearSelection,
  clearSelectionDraft,
  commitSelectionDraft,
  draftSelectionForVisualizer,
  effectivePlaybackRegion,
  getPlaybackRequest,
  playbackRequest,
  shouldTreatSelectionGestureAsClick,
  selectionForVisualizer,
  setRepeatEnabled,
  setSelection,
  setSelectionDraft,
  setRepeatEnabledForOrd,
} from "../src/editor-inline/actions.js";
import { disposeEditorRuntime } from "../src/editor-inline/runtime.js";
import { mountTrack } from "./editor-inline.actions.helpers.js";
import { readFieldState, updateFieldState } from "../src/editor-inline/field-state-store.js";

describe("editor inline selection workflows", () => {
  let warnSpy: ReturnType<typeof vi.spyOn>;
  let errorSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    warnSpy = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    errorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
  });

  afterEach(() => {
    disposeEditorRuntime();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("normalizes selection state and includes region fields in playback requests", async () => {
    const visualizer = await mountTrack(300);

    expect(selectionForVisualizer(visualizer)).toEqual({ startMs: 0, endMs: 1000, mode: "selection" });
    expect(effectivePlaybackRegion(visualizer)).toEqual({ startMs: 0, endMs: 1000, mode: "selection" });

    expect(setSelection(visualizer, 900, 200)).toBe(true);
    expect(selectionForVisualizer(visualizer)).toEqual({ startMs: 200, endMs: 900, mode: "selection" });
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: true,
      selectionStartMs: 200,
      selectionEndMs: 900,
      playbackRegionMode: "selection",
    });
    expect(playbackRequest(0)).toMatchObject({
      action: "start",
      cursorMs: 200,
      endMs: 900,
      loop: false,
      regionMode: "selection",
    });

    setRepeatEnabled(visualizer, true);
    expect(playbackRequest(0)).toMatchObject({ loop: true });
    clearSelection(visualizer);
    expect(effectivePlaybackRegion(visualizer)).toEqual({ startMs: 0, endMs: 1000, mode: "full" });
    expect(playbackRequest(0)).toMatchObject({ cursorMs: 200, endMs: 1000, regionMode: "full" });
  });

  it("rejects tiny selection gestures using pixel and time thresholds", () => {
    expect(shouldTreatSelectionGestureAsClick({ clientX: 10 }, { clientX: 12 }, 100, 250)).toBe(true);
    expect(shouldTreatSelectionGestureAsClick({ clientX: 10 }, { clientX: 60 }, 100, 125)).toBe(true);
    expect(shouldTreatSelectionGestureAsClick({ clientX: 10 }, { clientX: 60 }, 100, 250)).toBe(false);
  });

  it("keeps draft selection preview separate until it is committed", async () => {
    const visualizer = await mountTrack(300);
    expect(setSelection(visualizer, 100, 300)).toBe(true);

    expect(setSelectionDraft(visualizer, 800, 400)).toBe(true);
    expect(selectionForVisualizer(visualizer)).toEqual({ startMs: 100, endMs: 300, mode: "selection" });
    expect(draftSelectionForVisualizer(visualizer)).toEqual({ startMs: 400, endMs: 800, mode: "selection" });
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: true,
      selectionStartMs: 100,
      selectionEndMs: 300,
      selectionDraftActive: true,
      selectionDraftStartMs: 400,
      selectionDraftEndMs: 800,
    });
    expect(visualizer.querySelector(".aqe-selection")).toHaveClass("aqe-selection-draft");

    expect(commitSelectionDraft(visualizer)).toBe(true);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      cursorMs: 400,
      selectionActive: true,
      selectionStartMs: 400,
      selectionEndMs: 800,
      selectionDraftActive: false,
      selectionDraftStartMs: null,
      selectionDraftEndMs: null,
    });
    expect(visualizer.querySelector(".aqe-selection")).not.toHaveClass("aqe-selection-draft");

    expect(setSelectionDraft(visualizer, 200, 220)).toBe(false);
    expect(draftSelectionForVisualizer(visualizer)).toBeNull();
    expect(selectionForVisualizer(visualizer)).toEqual({ startMs: 400, endMs: 800, mode: "selection" });
    clearSelectionDraft(visualizer);
    expect(window.__aqeGraphStateForTest?.(0)?.selectionDraftActive).toBe(false);
  });

  it("handles selection guard branches and direct playback request reads", async () => {
    const visualizer = await mountTrack(300);

    expect(setRepeatEnabledForOrd(99, true)).toBe(false);
    expect(setSelection(visualizer, 100, 120)).toBe(false);
    expect(selectionForVisualizer(visualizer)).toBeNull();

    expect(setSelection(visualizer, 100, 300, { updateCursor: false })).toBe(true);
    expect(readFieldState(0).cursor.ms).toBe(300);
    window.__aqeActiveField = 0;
    const request = getPlaybackRequest();
    expect(request).toMatchObject({ cursorMs: 100, endMs: 300, regionMode: "selection" });
    expect(readFieldState(0).playback.engine).toBe(request.engine);

    visualizer.dataset.targetDurationMs = "0";
    updateFieldState(0, (state) => ({
      ...state,
      graph: { ...state.graph, durationMs: 0 },
    }));
    expect(setSelection(visualizer, 0, 200)).toBe(false);
  });
});
