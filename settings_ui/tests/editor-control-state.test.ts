import { afterEach, describe, expect, it } from "vitest";

import {
  clearStatusState,
  currentStatusState,
  emptyHistorySnapshot,
  hasStableStatusState,
  historyAvailabilityState,
  historySnapshotState,
  isEditorBusy,
  resetEditorControlState,
  restoreStableStatusState,
  setEditorBusy,
  setHistoryAvailabilityState,
  setHistorySnapshotState,
  setStatusState,
  setTransientStatusState,
  stableStatusState,
} from "../src/editor-inline/editor-control-state.js";

describe("editor control state", () => {
  afterEach(() => {
    resetEditorControlState();
  });

  it("tracks global busy state without DOM", () => {
    expect(isEditorBusy()).toBe(false);

    setEditorBusy(true);
    expect(isEditorBusy()).toBe(true);

    setEditorBusy(false);
    expect(isEditorBusy()).toBe(false);
  });

  it("stores stable edit statuses and restores them after transients", () => {
    setStatusState(0, "Closed settings.", "info", "", "edit");
    setTransientStatusState(0, "Analyzing...", "processing", "graph");

    expect(currentStatusState(0)).toMatchObject({
      kind: "processing",
      message: "Analyzing...",
      owner: "graph",
    });
    expect(stableStatusState(0)).toMatchObject({
      kind: "info",
      message: "Closed settings.",
      owner: "edit",
    });

    expect(restoreStableStatusState(0)).toMatchObject({
      kind: "info",
      message: "Closed settings.",
      owner: "edit",
    });
  });

  it("keeps user-facing error payloads as typed status values", () => {
    const error = { code: "AQE-MEDIA-001", message: "No audio." };

    setStatusState(1, error, "error", "", "error");

    expect(hasStableStatusState(1)).toBe(true);
    expect(stableStatusState(1).message).toEqual(error);
    expect(restoreStableStatusState(1)).toMatchObject({
      kind: "error",
      owner: "error",
    });
  });

  it("clears stable and current status together", () => {
    setStatusState(0, "Done.", "info", "", "edit");
    clearStatusState(0);

    expect(hasStableStatusState(0)).toBe(false);
    expect(currentStatusState(0)).toMatchObject({
      command: "",
      kind: "info",
      message: "",
      owner: "edit",
    });
  });

  it("normalizes and caps history snapshots", () => {
    const snapshot = setHistorySnapshotState(2, {
      canRedo: true,
      canUndo: true,
      redoItems: [{ id: "redo-1", label: "Redo 1" }, { id: "redo-2", label: "Redo 2" }],
      undoItems: [{ id: "undo-1", label: "Undo 1" }, { id: "undo-2", label: "Undo 2" }],
    }, 1);

    expect(snapshot).toEqual({
      canRedo: true,
      canUndo: true,
      redoItems: [{ id: "redo-1", label: "Redo 1" }],
      undoItems: [{ id: "undo-1", label: "Undo 1" }],
    });
    expect(historyAvailabilityState(2)).toEqual({ canRedo: true, canUndo: true });
  });

  it("stores availability as an empty history snapshot", () => {
    setHistoryAvailabilityState(3, true, false);

    expect(historySnapshotState(3)).toEqual({
      canRedo: false,
      canUndo: true,
      redoItems: [],
      undoItems: [],
    });
  });

  it("resets all control state", () => {
    setEditorBusy(true);
    setStatusState(0, "Done.", "info", "", "edit");
    setHistoryAvailabilityState(0, true, true);

    resetEditorControlState();

    expect(isEditorBusy()).toBe(false);
    expect(currentStatusState(0).message).toBe("");
    expect(historySnapshotState(0)).toEqual(emptyHistorySnapshot());
  });
});
