import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  currentProgressMs,
  setPlaybackState,
  setRepeatEnabled,
  setSelection,
  startManualProgressClock,
} from "../src/editor-inline/actions.js";
import { disposeEditorRuntime } from "../src/editor-inline/runtime.js";
import { xForMs, yForPitch } from "../src/editor-inline/plot.js";
import { bridgeCommands, mountTrack } from "./editor-inline.actions.helpers.js";

describe("editor inline action progress clocks", () => {
  let warnSpy: ReturnType<typeof vi.spyOn>;
  let errorSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    warnSpy = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    errorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
  });

  afterEach(() => {
    disposeEditorRuntime();
    warnSpy.mockRestore();
    errorSpy.mockRestore();
    vi.restoreAllMocks();
  });

  it("updates the timecode flag during progress clock ticks", async () => {
    const frames: Array<(time: number) => void> = [];
    vi.spyOn(window, "requestAnimationFrame").mockImplementation((callback) => {
      frames.push(callback);
      return frames.length;
    });
    vi.spyOn(window, "cancelAnimationFrame").mockImplementation(() => undefined);
    let now = 1000;
    vi.spyOn(performance, "now").mockImplementation(() => now);
    const visualizer = await mountTrack(0);
    const audio = visualizer.querySelector<HTMLAudioElement>(".aqe-audio-clock")!;
    const flag = visualizer.querySelector<SVGGElement>(".aqe-cursor-flag")!;
    audio.pause = vi.fn<() => void>(() => undefined);

    startManualProgressClock(visualizer, 300);
    now = 1400;
    frames.shift()?.(now);

    expect(flag.querySelector(".aqe-cursor-flag-current")?.textContent).toBe("700 ms");
    expect(flag.querySelector(".aqe-cursor-flag-pitch")?.textContent).toBe(" / 196 Hz");
    const state = window.__aqeGraphStateForTest?.(0);
    expect(state).toMatchObject({ pitchMarkerVisible: false, progressMs: 700 });
    expect(state?.pitchMarkerX).toBeCloseTo(xForMs(700, 1000));
    expect(state?.pitchMarkerY).toBeCloseTo(yForPitch(196, 100, 300));
  });

  it("loops manual progress clocks at the selected region boundary without play-ended", async () => {
    const frames: Array<(time: number) => void> = [];
    vi.spyOn(window, "requestAnimationFrame").mockImplementation((callback) => {
      frames.push(callback);
      return frames.length;
    });
    vi.spyOn(window, "cancelAnimationFrame").mockImplementation(() => undefined);
    let now = 1000;
    vi.spyOn(performance, "now").mockImplementation(() => now);
    const visualizer = await mountTrack(0);
    const audio = visualizer.querySelector<HTMLAudioElement>(".aqe-audio-clock")!;
    audio.pause = vi.fn<() => void>(() => undefined);
    setSelection(visualizer, 200, 400);
    setRepeatEnabled(visualizer, true);

    startManualProgressClock(visualizer, 350);
    now = 1100;
    frames.shift()?.(now);

    expect(visualizer.dataset.playbackState).toBe("playing");
    expect(visualizer.dataset.cursorMs).toBe("200");
    expect(bridgeCommands()).not.toContain("aqe:play-ended");
  });

  it("starts HTML visual progress after play resolves and does not follow stale currentTime ticks", async () => {
    const frames: Array<(time: number) => void> = [];
    vi.spyOn(window, "requestAnimationFrame").mockImplementation((callback) => {
      frames.push(callback);
      return frames.length;
    });
    vi.spyOn(window, "cancelAnimationFrame").mockImplementation(() => undefined);
    let now = 1000;
    vi.spyOn(performance, "now").mockImplementation(() => now);
    const visualizer = await mountTrack(0);
    const audio = visualizer.querySelector<HTMLAudioElement>(".aqe-audio-clock")!;
    let resolvePlay: () => void = () => undefined;
    Object.defineProperty(audio, "readyState", { configurable: true, value: 1 });
    audio.play = vi.fn<() => Promise<void>>(() => new Promise((resolve) => {
      resolvePlay = resolve;
    }));
    audio.pause = vi.fn<() => void>(() => undefined);
    audio.dispatchEvent(new Event("loadedmetadata"));
    visualizer.dataset.playbackEngine = "html";

    setPlaybackState(0, "playing", 100);
    audio.currentTime = 0.9;
    now = 1300;

    expect(currentProgressMs(visualizer)).toBe(100);

    resolvePlay();
    await Promise.resolve();
    await Promise.resolve();
    now = 1400;
    frames.shift()?.(now);

    expect(Math.round(currentProgressMs(visualizer) ?? 0)).toBe(200);
    expect(window.__aqeGraphStateForTest?.(0)?.progressMs).toBe(200);
  });

  it("ignores stale HTML play rejections after a newer playback plan starts", async () => {
    const frames: Array<(time: number) => void> = [];
    vi.spyOn(window, "requestAnimationFrame").mockImplementation((callback) => {
      frames.push(callback);
      return frames.length;
    });
    vi.spyOn(window, "cancelAnimationFrame").mockImplementation(() => undefined);
    let now = 1000;
    vi.spyOn(performance, "now").mockImplementation(() => now);
    const visualizer = await mountTrack(0);
    const audio = visualizer.querySelector<HTMLAudioElement>(".aqe-audio-clock")!;
    let rejectFirstPlay: (error: Error) => void = () => undefined;
    Object.defineProperty(audio, "readyState", { configurable: true, value: 1 });
    audio.play = vi.fn<() => Promise<void>>()
      .mockImplementationOnce(() => new Promise((_resolve, reject) => {
        rejectFirstPlay = reject;
      }))
      .mockImplementationOnce(() => Promise.resolve());
    audio.pause = vi.fn<() => void>(() => undefined);
    audio.dispatchEvent(new Event("loadedmetadata"));
    visualizer.dataset.playbackEngine = "html";

    setPlaybackState(0, "playing", 100);
    setPlaybackState(0, "playing", 500);
    await Promise.resolve();
    await Promise.resolve();
    expect(audio.play).toHaveBeenCalledTimes(2);
    expect(visualizer.dataset.progressClockMode).toBe("audio");

    rejectFirstPlay(new Error("blocked"));
    await Promise.resolve();
    await Promise.resolve();
    now = 1150;
    frames.shift()?.(now);

    expect(visualizer.dataset.progressClockMode).toBe("audio");
    expect(Math.round(currentProgressMs(visualizer) ?? 0)).toBe(650);
  });
});
