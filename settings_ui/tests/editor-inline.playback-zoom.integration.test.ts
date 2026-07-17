import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { completePlayback, setRepeatPauseSeconds, stopProgressClock } from "../src/editor-inline/actions.js";
import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import type { VisualizerElement } from "../src/editor-inline/types.js";
import {
  dragGraphSelection,
  mockAnimationFrames,
  muteConsole,
  prepareHtmlAudio,
  renderFields,
  setFullGraphViewport,
  setGraphBounds,
  setRepeatMode,
  track,
} from "./editor-inline.integration.helpers.js";

describe("editor inline zoom playback integration", () => {
  let restoreConsole: () => void;

  beforeEach(() => {
    restoreConsole = muteConsole();
    renderFields();
  });

  afterEach(() => {
    disposeEditorRuntime();
    restoreConsole();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("pans the zoomed viewport to an offscreen playback start", async () => {
    await setupGraph(400);
    prepareHtmlAudio();
    window.__aqeSetTimeViewportForTest?.(0, 500, 1000);
    window.__aqeSetCursorForTest?.(0, 0, false);

    await clickPlay();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      cursorMs: 0,
      playbackState: "playing",
      timecodeFlagVisible: true,
      viewportStartMs: 0,
      viewportEndMs: 500,
    });
  });

  it("follows the authoritative media clock near the visible edge", async () => {
    const frames = mockAnimationFrames();
    await setupGraph(450);
    window.__aqeSetTimeViewportForTest?.(0, 0, 500);
    const audio = prepareHtmlAudio();
    await clickPlay();
    audio.currentTime = 0.57;
    frames.shift()?.(performance.now() + 16);

    const state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBeGreaterThan(0);
    expect((state?.viewportEndMs ?? 0) - (state?.viewportStartMs ?? 0)).toBe(500);
    expect(state?.progressMs).toBe(570);
    expect(state?.timecodeFlagVisible).toBe(true);
  });

  it("pans back to the selected start when playback completes", async () => {
    const { svg, visualizer } = await setupGraph(0);
    dragGraphSelection(svg, 0.2, 0.8);
    window.__aqeSetTimeViewportForTest?.(0, 500, 1000);
    prepareHtmlAudio();
    await clickPlay();

    completePlayback(visualizer);

    const state = window.__aqeGraphStateForTest?.(0);
    expect(state).toMatchObject({
      cursorMs: 200,
      playbackState: "stopped",
      selectionStartMs: 200,
      timecodeFlagVisible: true,
    });
    expect(state?.viewportStartMs).toBeLessThanOrEqual(200);
    expect(state?.viewportEndMs).toBeGreaterThanOrEqual(200);
  });

  it("pans to the loop start during a repeat wait", async () => {
    vi.useFakeTimers();
    const frames = mockAnimationFrames();
    const { svg, visualizer } = await setupGraph(0);
    dragGraphSelection(svg, 0.2, 0.8);
    await setRepeatMode(true);
    setRepeatPauseSeconds(visualizer, 10);
    window.__aqeSetTimeViewportForTest?.(0, 500, 1000);
    const audio = prepareHtmlAudio();
    frames.length = 0;
    await clickPlay();
    audio.currentTime = 0.81;
    frames.shift()?.(performance.now() + 16);

    const state = window.__aqeGraphStateForTest?.(0);
    expect(state).toMatchObject({
      cursorMs: 200,
      playbackState: "playing",
      selectionStartMs: 200,
      timecodeFlagVisible: true,
    });
    expect(state?.viewportStartMs).toBeLessThanOrEqual(200);
    expect(state?.viewportEndMs).toBeGreaterThanOrEqual(200);
    stopProgressClock(visualizer);
  });
});

async function setupGraph(cursorMs: number): Promise<{ svg: SVGSVGElement; visualizer: VisualizerElement }> {
  initializeEditorRuntime({ audioFieldIndices: [0] });
  scan({ audioFieldIndices: [0] });
  await Promise.resolve();
  window.__aqeSetVisualizer?.(0, track, cursorMs);
  const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
  setGraphBounds(svg);
  setFullGraphViewport();
  const visualizer = document.querySelector<VisualizerElement>('[data-testid="aqe-graph-0"]')!;
  return { svg, visualizer };
}

async function clickPlay(): Promise<void> {
  document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
  await Promise.resolve();
  await Promise.resolve();
}
