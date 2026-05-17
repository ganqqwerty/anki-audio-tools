import { describe, expect, it } from "vitest";

import {
  clearDraftSelectionState,
  commitDraftSelectionState,
  draftSelectionRegion,
  emptySelectionState,
  normalizeSelectionRange,
  selectionRegion,
  setDraftSelectionRange,
  setSelectionRange,
  shouldTreatSelectionGestureAsClick,
} from "../src/editor-inline/selection-state.js";

describe("selection state", () => {
  it("normalizes reversed selections and clamps to duration", () => {
    expect(normalizeSelectionRange(900, 200, 1000)).toEqual({ startMs: 200, endMs: 900 });
    expect(normalizeSelectionRange(-100, 1200, 1000)).toEqual({ startMs: 0, endMs: 1000 });
  });

  it("rejects tiny or zero-duration selections", () => {
    expect(normalizeSelectionRange(100, 120, 1000)).toBeNull();
    expect(normalizeSelectionRange(0, 500, 0)).toBeNull();
  });

  it("keeps draft selection separate until commit", () => {
    const committed = setSelectionRange(emptySelectionState(), 100, 300, 1000);
    const draft = setDraftSelectionRange(committed, 800, 400, 1000);

    expect(selectionRegion(draft, 1000)).toEqual({ mode: "selection", startMs: 100, endMs: 300 });
    expect(draftSelectionRegion(draft, 1000)).toEqual({ mode: "selection", startMs: 400, endMs: 800 });
    expect(commitDraftSelectionState(draft, 1000)).toMatchObject({
      active: true,
      draftActive: false,
      startMs: 400,
      endMs: 800,
    });
  });

  it("cancels only the draft selection", () => {
    const state = setDraftSelectionRange(setSelectionRange(emptySelectionState(), 100, 300, 1000), 400, 800, 1000);

    expect(clearDraftSelectionState(state)).toMatchObject({
      active: true,
      draftActive: false,
      startMs: 100,
      endMs: 300,
    });
  });

  it("classifies click-like gestures by pixel or duration threshold", () => {
    expect(shouldTreatSelectionGestureAsClick({ clientX: 10 }, { clientX: 12 }, 100, 250)).toBe(true);
    expect(shouldTreatSelectionGestureAsClick({ clientX: 10 }, { clientX: 60 }, 100, 125)).toBe(true);
    expect(shouldTreatSelectionGestureAsClick({ clientX: 10 }, { clientX: 60 }, 100, 250)).toBe(false);
  });
});
