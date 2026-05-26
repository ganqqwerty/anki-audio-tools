import { afterEach, describe, expect, it } from "vitest";
import {
  clearPendingNoteScopedBridgeRequests,
  popPendingGraphAnalysisRequest,
  popPendingPlaybackRequest,
  popPendingRegionDeleteRequest,
  popPendingSplitDefaultSaveRequest,
  sendGraphAnalysisRequest,
  sendSplitDefaultSaveRequest,
  setPendingPlaybackRequest,
  setPendingRegionDeleteRequest,
} from "../src/editor-inline/bridge.js";
import type { SplitDefaultSaveRequest } from "../src/editor-inline/split-default-save-types.js";
import type {
  GraphAnalysisRequest,
  PlaybackRequest,
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
  drainPending(popPendingPlaybackRequest);
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

  it("keeps playback requests in FIFO order while preserving the last request", () => {
    const first: PlaybackRequest = { action: "start", cursorMs: 0, ord: 0 };
    const second: PlaybackRequest = {
      action: "start",
      cursorMs: 500,
      endMs: 900,
      ord: 0,
      regionMode: "selection",
    };

    setPendingPlaybackRequest(first);
    setPendingPlaybackRequest(second);

    expect(window.__aqeLastPlaybackRequest).toEqual(second);
    expect(popPendingPlaybackRequest()).toEqual(first);
    expect(popPendingPlaybackRequest()).toEqual(second);
    expect(popPendingPlaybackRequest()).toBeNull();
  });

  it("clears note-scoped pending requests when the editor moves to a new note", () => {
    const graph: GraphAnalysisRequest = { ord: 0, sourceFilename: "a.mp3" };
    const playback: PlaybackRequest = { action: "start", cursorMs: 0, ord: 0 };
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
    setPendingPlaybackRequest(playback);
    setPendingRegionDeleteRequest(regionDelete);
    clearPendingNoteScopedBridgeRequests();

    expect(popPendingGraphAnalysisRequest()).toBeNull();
    expect(popPendingPlaybackRequest()).toBeNull();
    expect(popPendingRegionDeleteRequest()).toBeNull();
    expect(window.__aqePendingPlaybackRequest).toBeNull();
    expect(window.__aqeLastPlaybackRequest).toBeNull();
  });
});
