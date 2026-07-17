import { afterEach, describe, expect, it } from "vitest";
import {
  clearPendingNoteScopedBridgeRequests,
  popPendingGraphAnalysisRequest,
  popPendingRegionDeleteRequest,
  popPendingSplitDefaultSaveRequest,
  sendGraphAnalysisRequest,
  sendSplitDefaultSaveRequest,
  setPendingRegionDeleteRequest,
} from "../src/editor-inline/bridge.js";
import type { SplitDefaultSaveRequest } from "../src/editor-inline/split-default-save-types.js";
import type {
  GraphAnalysisRequest,
  RegionDeleteRequest,
} from "../src/editor-inline/types.js";
import { pycmdMock } from "./setup.js";

function drainPending<T>(pop: () => T | null): void {
  let next = pop();
  while (next !== null) {
    next = pop();
  }
}

afterEach(() => {
  drainPending(popPendingGraphAnalysisRequest);
  drainPending(popPendingRegionDeleteRequest);
  drainPending(popPendingSplitDefaultSaveRequest);
});

describe("editor bridge pending request queues", () => {
  it("keeps graph analysis requests in FIFO order", () => {
    const first: GraphAnalysisRequest = { ord: 0, sourceFilename: "a.mp3" };
    const second: GraphAnalysisRequest = { ord: 1, sourceFilename: "b.mp3" };

    sendGraphAnalysisRequest(first);
    sendGraphAnalysisRequest(second);

    expect(pycmdMock).toHaveBeenCalledTimes(2);
    expect(popPendingGraphAnalysisRequest()).toEqual(first);
    expect(popPendingGraphAnalysisRequest()).toEqual(second);
    expect(popPendingGraphAnalysisRequest()).toBeNull();
  });

  it("keeps region delete requests in FIFO order", () => {
    const first: RegionDeleteRequest = {
      ord: 0,
      sourceFilename: "a.mp3",
      selectionStartMs: 100,
      selectionEndMs: 200,
      cursorMs: 100,
      durationMs: 1000,
      trigger: "button",
      playbackActive: false,
      operation: "delete-selection",
    };
    const second: RegionDeleteRequest = {
      ord: 0,
      sourceFilename: "a.mp3",
      selectionStartMs: 300,
      selectionEndMs: 400,
      cursorMs: 300,
      durationMs: 1000,
      trigger: "backspace",
      playbackActive: true,
      operation: "delete-rest",
    };

    setPendingRegionDeleteRequest(first);
    setPendingRegionDeleteRequest(second);

    expect(popPendingRegionDeleteRequest()).toEqual(first);
    expect(popPendingRegionDeleteRequest()).toEqual(second);
    expect(popPendingRegionDeleteRequest()).toBeNull();
  });

  it("keeps split default save requests in FIFO order", () => {
    const first: SplitDefaultSaveRequest = { fieldOrd: 0, defaults: { speedStep: 0.1 } };
    const second: SplitDefaultSaveRequest = { fieldOrd: 1, defaults: { volumeStepDb: 3 } };

    sendSplitDefaultSaveRequest(first);
    sendSplitDefaultSaveRequest(second);

    expect(pycmdMock).toHaveBeenCalledTimes(2);
    expect(popPendingSplitDefaultSaveRequest()).toEqual(first);
    expect(popPendingSplitDefaultSaveRequest()).toEqual(second);
    expect(popPendingSplitDefaultSaveRequest()).toBeNull();
  });

  it("clears note-scoped pending requests when the editor moves to a new note", () => {
    const graph: GraphAnalysisRequest = { ord: 0, sourceFilename: "a.mp3" };
    const regionDelete: RegionDeleteRequest = {
      ord: 0,
      sourceFilename: "a.mp3",
      selectionStartMs: 100,
      selectionEndMs: 200,
      cursorMs: 100,
      durationMs: 1000,
      trigger: "button",
      playbackActive: false,
      operation: "delete-selection",
    };

    sendGraphAnalysisRequest(graph);
    setPendingRegionDeleteRequest(regionDelete);
    clearPendingNoteScopedBridgeRequests();

    expect(popPendingGraphAnalysisRequest()).toBeNull();
    expect(popPendingRegionDeleteRequest()).toBeNull();
  });
});
