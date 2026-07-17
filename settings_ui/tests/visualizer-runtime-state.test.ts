import { afterEach, describe, expect, it, vi } from "vitest";

import type { VisualizerElement } from "../src/editor-inline/types.js";
import {
  clearVisualizerRuntimeStates,
  emptyVisualizerRuntimeState,
  readLearnerDurationMsForVisualizer,
  readRepeatPauseSecondsRuntime,
  readRuntimeTimeViewport,
  readTargetDurationMsForVisualizer,
  readVisualizerRuntimeState,
  resetVisualizerRuntimeState,
  setLearnerDurationMsForVisualizer,
  setRepeatPauseSecondsRuntime,
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
    node.dataset.repeatPauseSeconds = "9";

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

  it("stores repeat pause", () => {
    const node = visualizer();

    expect(setRepeatPauseSecondsRuntime(node, 25)).toBe(10);
    expect(readRepeatPauseSecondsRuntime(node)).toBe(10);
  });

  it("resets state and projection", () => {
    const node = visualizer();
    setTargetDurationMsForVisualizer(node, 700);

    resetVisualizerRuntimeState(0, node);

    expect(readVisualizerRuntimeState(0)).toEqual(emptyVisualizerRuntimeState());
    expect(node.dataset.targetDurationMs).toBe("0");
  });
});
