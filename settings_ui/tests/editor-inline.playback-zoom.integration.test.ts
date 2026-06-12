import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  completePlayback,
  setRepeatPauseSeconds,
  startManualProgressClock,
  stopProgressClock,
} from "../src/editor-inline/actions.js";
import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import {
  dragGraphSelection,
  muteConsole,
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

  it("pans the zoomed viewport to the playback start when the cursor is offscreen", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 400);
    const audio = document.querySelector<HTMLAudioElement>('[data-testid="aqe-audio-clock-0"]')!;
    Object.defineProperty(audio, "readyState", { configurable: true, value: 1 });
    audio.play = vi.fn<() => Promise<void>>(() => Promise.resolve());
    audio.pause = vi.fn<() => void>(() => undefined);
    audio.dispatchEvent(new Event("loadedmetadata"));
    window.__aqeSetTimeViewportForTest?.(0, 500, 1000);
    window.__aqeSetCursorForTest?.(0, 0, false);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      cursorMs: 0,
      timecodeFlagVisible: false,
    });

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      cursorMs: 0,
      playbackState: "playing",
      timecodeFlagVisible: true,
      viewportStartMs: 0,
      viewportEndMs: 500,
    });
  });

  it("pans the zoomed viewport as manual playback approaches the visible edge", async () => {
    const frames: Array<(time: number) => void> = [];
    vi.spyOn(window, "requestAnimationFrame").mockImplementation((callback) => {
      frames.push(callback);
      return frames.length;
    });
    vi.spyOn(window, "cancelAnimationFrame").mockImplementation(() => undefined);
    let now = 1000;
    vi.spyOn(performance, "now").mockImplementation(() => now);
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 0);
    window.__aqeSetTimeViewportForTest?.(0, 0, 500);
    const visualizer = document.querySelector<HTMLElement>('[data-testid="aqe-graph-0"]')!;
    const audio = document.querySelector<HTMLAudioElement>('[data-testid="aqe-audio-clock-0"]')!;
    audio.pause = vi.fn<() => void>(() => undefined);

    startManualProgressClock(visualizer as Parameters<typeof startManualProgressClock>[0], 450);
    now = 1120;
    frames.shift()?.(now);

    const state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBeGreaterThan(0);
    expect((state?.viewportEndMs ?? 0) - (state?.viewportStartMs ?? 0)).toBe(500);
    expect(state?.progressMs).toBeGreaterThanOrEqual(450);
    expect(state?.timecodeFlagVisible).toBe(true);

    window.__aqeSetTimeViewportForTest?.(0, 0, 500);
    now = 1140;
    frames.shift()?.(now);

    const followedState = window.__aqeGraphStateForTest?.(0);
    expect(followedState?.viewportStartMs).toBeGreaterThan(0);
    expect(followedState?.progressMs).toBeGreaterThanOrEqual(state?.progressMs ?? 0);
    expect(followedState?.timecodeFlagVisible).toBe(true);
  });

  it("pans back to the selected start cursor when playback completes while zoomed", async () => {
    const frames: Array<(time: number) => void> = [];
    vi.spyOn(window, "requestAnimationFrame").mockImplementation((callback) => {
      frames.push(callback);
      return frames.length;
    });
    vi.spyOn(window, "cancelAnimationFrame").mockImplementation(() => undefined);
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 0);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    setFullGraphViewport();
    dragGraphSelection(svg, 0.2, 0.8);
    window.__aqeSetTimeViewportForTest?.(0, 500, 1000);
    const visualizer = document.querySelector<HTMLElement>('[data-testid="aqe-graph-0"]')!;
    const audio = document.querySelector<HTMLAudioElement>('[data-testid="aqe-audio-clock-0"]')!;
    audio.pause = vi.fn<() => void>(() => undefined);

    startManualProgressClock(visualizer as Parameters<typeof startManualProgressClock>[0], 790);
    completePlayback(visualizer as Parameters<typeof completePlayback>[0]);

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

  it("pans back to the loop start cursor during repeat pause while zoomed", async () => {
    const frames: Array<(time: number) => void> = [];
    vi.spyOn(window, "requestAnimationFrame").mockImplementation((callback) => {
      frames.push(callback);
      return frames.length;
    });
    vi.spyOn(window, "cancelAnimationFrame").mockImplementation(() => undefined);
    let now = 1000;
    vi.spyOn(performance, "now").mockImplementation(() => now);
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 0);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    setFullGraphViewport();
    dragGraphSelection(svg, 0.2, 0.8);
    await setRepeatMode(true);
    window.__aqeSetTimeViewportForTest?.(0, 500, 1000);
    const visualizer = document.querySelector<HTMLElement>('[data-testid="aqe-graph-0"]')!;
    setRepeatPauseSeconds(visualizer as Parameters<typeof setRepeatPauseSeconds>[0], 10);
    const audio = document.querySelector<HTMLAudioElement>('[data-testid="aqe-audio-clock-0"]')!;
    audio.pause = vi.fn<() => void>(() => undefined);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      repeatEnabled: true,
      repeatPauseSeconds: 10,
    });

    frames.length = 0;
    startManualProgressClock(visualizer as Parameters<typeof startManualProgressClock>[0], 790);
    now = 1120;
    frames.shift()?.(now);

    const state = window.__aqeGraphStateForTest?.(0);
    expect(state).toMatchObject({
      cursorMs: 200,
      playbackState: "playing",
      repeatPauseWaiting: true,
      selectionStartMs: 200,
      timecodeFlagVisible: true,
    });
    expect(state?.viewportStartMs).toBeLessThanOrEqual(200);
    expect(state?.viewportEndMs).toBeGreaterThanOrEqual(200);
    stopProgressClock(visualizer as Parameters<typeof stopProgressClock>[0]);
  });
});
