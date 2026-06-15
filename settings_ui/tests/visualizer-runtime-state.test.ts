import { afterEach, describe, expect, it, vi } from "vitest";

import type { VisualizerElement } from "../src/editor-inline/types.js";
import {
  clearVisualizerRuntimeStates,
  emptyVisualizerRuntimeState,
  isRepeatPauseWaitingRuntime,
  preserveStatusOnPlaybackEndRuntime,
  readLearnerDurationMsForVisualizer,
  readPlaybackClockRuntime,
  readPlaybackPassRuntime,
  readRepeatPauseSecondsRuntime,
  readRuntimeTimeViewport,
  readTargetDurationMsForVisualizer,
  readVisualizerRuntimeState,
  resetVisualizerRuntimeState,
  setLearnerDurationMsForVisualizer,
  setPlaybackClockRuntime,
  setPlaybackPassRuntime,
  setPreserveStatusOnPlaybackEndRuntime,
  setRepeatPauseSecondsRuntime,
  setRepeatPauseWaitingRuntime,
  setTargetDurationMsForVisualizer,
  writeRuntimeTimeViewport,
} from "../src/editor-inline/visualizer-runtime-state.js";

function visualizer(ord = 0): VisualizerElement {
  const node = document.createElement("div") as VisualizerElement;
  node.className = "aqe-visualizer";
  node.dataset.aqeFieldOrd = String(ord);
  document.body.append(node);
  return node;
}

describe("visualizer runtime state", () => {
  afterEach(() => {
    clearVisualizerRuntimeStates();
    document.body.innerHTML = "";
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("returns typed defaults without reading DOM projection", () => {
    const node = visualizer();
    node.dataset.targetDurationMs = "900";
    node.dataset.playbackLoop = "true";

    expect(readVisualizerRuntimeState(0)).toEqual(emptyVisualizerRuntimeState());
    expect(readTargetDurationMsForVisualizer(node, 1000)).toBe(1000);
  });

  it("stores target and learner durations and projects them to DOM", () => {
    const node = visualizer();

    setTargetDurationMsForVisualizer(node, 999.6);
    setLearnerDurationMsForVisualizer(node, 501.2);

    expect(readTargetDurationMsForVisualizer(node, 100)).toBe(1000);
    expect(readLearnerDurationMsForVisualizer(node)).toBe(501);
    expect(node.dataset.targetDurationMs).toBe("1000");
    expect(node.dataset.learnerDurationMs).toBe("501");
  });

  it("round-trips viewport state independently from DOM corruption", () => {
    const node = visualizer();

    writeRuntimeTimeViewport(node, { durationMs: 2000, startMs: 250.4, endMs: 1750.6 });
    node.dataset.viewportStartMs = "0";
    node.dataset.viewportEndMs = "2000";

    expect(readRuntimeTimeViewport(node, 2000)).toEqual({
      durationMs: 2000,
      endMs: 1751,
      startMs: 250,
    });
  });

  it("stores playback pass and clock metadata", () => {
    const node = visualizer();
    vi.spyOn(performance, "now").mockReturnValue(12345);

    setPlaybackPassRuntime(node, {
      endMs: 900,
      loop: true,
      regionMode: "selection",
      resetCursorMs: 250,
      startMs: 100,
    });
    setPlaybackClockRuntime(node, 100);
    node.dataset.playbackLoop = "false";
    node.dataset.playbackResetCursorMs = "0";

    expect(readPlaybackPassRuntime(node, 10)).toEqual({
      loop: true,
      resetCursorMs: 250,
    });
    expect(readPlaybackClockRuntime(node)).toEqual({
      playStartedAt: 12345,
      playStartMs: 100,
    });
  });

  it("stores repeat pause and preserve-status flags", () => {
    const node = visualizer();

    expect(setRepeatPauseSecondsRuntime(node, 25)).toBe(10);
    setRepeatPauseWaitingRuntime(node, true);
    setPreserveStatusOnPlaybackEndRuntime(node, true);

    expect(readRepeatPauseSecondsRuntime(node)).toBe(10);
    expect(isRepeatPauseWaitingRuntime(node)).toBe(true);
    expect(preserveStatusOnPlaybackEndRuntime(node)).toBe(true);
  });

  it("resets state and projection", () => {
    const node = visualizer();
    setTargetDurationMsForVisualizer(node, 700);
    setPlaybackPassRuntime(node, {
      endMs: 700,
      loop: true,
      regionMode: "full",
      resetCursorMs: 111,
      startMs: 0,
    });

    resetVisualizerRuntimeState(0, node);

    expect(readVisualizerRuntimeState(0)).toEqual(emptyVisualizerRuntimeState());
    expect(node.dataset.targetDurationMs).toBe("0");
    expect(node.dataset.playbackLoop).toBe("false");
    expect(node.dataset.playbackResetCursorMs).toBe("0");
  });
});
