import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { currentProgressMs, startSourcePlayback } from "../src/editor-inline/actions.js";
import { readFieldState } from "../src/editor-inline/field-state-store.js";
import { disposeEditorRuntime } from "../src/editor-inline/runtime.js";
import type { VisualizerElement } from "../src/editor-inline/types.js";
import { mountTrack } from "./editor-inline.actions.helpers.js";

describe("editor inline transport progress projection", () => {
  beforeEach(() => {
    vi.spyOn(console, "warn").mockImplementation(() => undefined);
    vi.spyOn(console, "error").mockImplementation(() => undefined);
  });

  afterEach(() => {
    disposeEditorRuntime();
    vi.restoreAllMocks();
  });

  it("renders media progress and follows it while zoomed", async () => {
    const frames = mockFrames();
    const visualizer = await mountTrack(0);
    const audio = prepareAudio(visualizer);
    window.__aqeSetTimeViewportForTest?.(0, 0, 500);
    await startPlayback(visualizer, 450);
    audio.currentTime = 0.7;

    frames.shift()?.(performance.now() + 16);

    expect(visualizer.querySelector(".aqe-css-cursor-flag-current")?.textContent).toBe("700 ms");
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({ progressMs: 700 });
    expect(window.__aqeGraphStateForTest?.(0)?.viewportStartMs).toBeGreaterThan(0);
  });

  it("reports the authoritative media position while play is resolving", async () => {
    const frames = mockFrames();
    const visualizer = await mountTrack(0);
    const audio = prepareAudio(visualizer);
    let resolvePlay = (): void => undefined;
    audio.play = vi.fn(() => new Promise<void>((resolve) => {
      resolvePlay = resolve;
    }));

    startPlaybackWithoutFlush(visualizer, 100);
    audio.currentTime = 0.9;
    expect(currentProgressMs(visualizer)).toBe(900);

    resolvePlay();
    await flushPlayback();
    audio.currentTime = 0.2;
    frames.shift()?.(performance.now() + 16);
    expect(Math.round(currentProgressMs(visualizer) ?? 0)).toBe(200);
  });

  it("ignores a rejected play promise after a newer attempt starts", async () => {
    const visualizer = await mountTrack(0);
    const audio = prepareAudio(visualizer);
    let rejectFirst = (_error: Error): void => undefined;
    audio.play = vi.fn<() => Promise<void>>()
      .mockImplementationOnce(() => new Promise((_resolve, reject) => {
        rejectFirst = reject;
      }))
      .mockResolvedValueOnce();

    startPlaybackWithoutFlush(visualizer, 100);
    startPlaybackWithoutFlush(visualizer, 500);
    await flushPlayback();
    expect(audio.play).toHaveBeenCalledTimes(2);
    expect(readFieldState(0).playback.clockMode).toBe("audio");

    rejectFirst(new Error("blocked"));
    await flushPlayback();
    expect(readFieldState(0).playback.clockMode).toBe("audio");
  });
});

function prepareAudio(visualizer: VisualizerElement): HTMLAudioElement {
  const audio = visualizer.querySelector<HTMLAudioElement>(".aqe-audio-clock")!;
  Object.defineProperty(audio, "duration", { configurable: true, value: 1 });
  Object.defineProperty(audio, "readyState", { configurable: true, value: 1 });
  audio.play = vi.fn(() => Promise.resolve());
  audio.pause = vi.fn(() => undefined);
  audio.dispatchEvent(new Event("loadedmetadata"));
  return audio;
}

function startPlaybackWithoutFlush(visualizer: VisualizerElement, cursorMs: number): void {
  expect(startSourcePlayback(visualizer, {
    action: "start",
    cursorMs,
    endMs: 1000,
    engine: "html",
    loop: false,
    ord: 0,
    regionMode: "full",
    source: "user",
  })).toBe(true);
}

async function startPlayback(visualizer: VisualizerElement, cursorMs: number): Promise<void> {
  startPlaybackWithoutFlush(visualizer, cursorMs);
  await flushPlayback();
}

function mockFrames(): Array<(time: number) => void> {
  const frames: Array<(time: number) => void> = [];
  vi.spyOn(window, "requestAnimationFrame").mockImplementation((callback) => {
    frames.push(callback);
    return frames.length;
  });
  vi.spyOn(window, "cancelAnimationFrame").mockImplementation(() => undefined);
  return frames;
}

async function flushPlayback(): Promise<void> {
  await Promise.resolve();
  await Promise.resolve();
}
