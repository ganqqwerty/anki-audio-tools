import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  audioClockReady,
  clearAudioClockSource,
  configureAudioClock,
  currentProgressMs,
  handleHtmlPlaybackCommand,
  pauseAudioClock,
  playbackRequest,
  seekAudioClock,
  setPlaybackState,
  startManualProgressClock,
  stopEditorPlayback,
} from "../src/editor-inline/actions.js";
import { disposeEditorRuntime } from "../src/editor-inline/runtime.js";
import { bridgeCommands, mountTrack } from "./editor-inline.actions.helpers.js";

describe("editor inline audio-clock workflows", () => {
  let warnSpy: ReturnType<typeof vi.spyOn>;
  let errorSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    warnSpy = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    errorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
  });

  afterEach(() => {
    disposeEditorRuntime();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("handles audio clock setup, seek, clear, and failure branches", async () => {
    const visualizer = await mountTrack();
    const audio = visualizer.querySelector<HTMLAudioElement>(".aqe-audio-clock")!;
    Object.defineProperty(audio, "readyState", { configurable: true, value: 1 });
    audio.dispatchEvent(new Event("loadedmetadata"));

    expect(audioClockReady(visualizer)).toBe(true);
    expect(seekAudioClock(visualizer, 500)).toBe(true);
    expect(Math.round(audio.currentTime * 1000)).toBe(500);

    audio.pause = vi.fn<() => void>(() => {
      throw new Error("pause failed");
    });
    pauseAudioClock(visualizer);
    expect(visualizer.__aqeAudioClockFallback).toBe(true);

    audio.load = vi.fn<() => void>(() => {
      throw new Error("load failed");
    });
    configureAudioClock(visualizer, "");
    expect(visualizer.__aqeAudioClockFallback).toBe(true);
    clearAudioClockSource(visualizer);
    expect(audio.getAttribute("src")).toBe("");
  });

  it("moves audio errors to the manual playback clock and completes on ended", async () => {
    const frames: Array<(time: number) => void> = [];
    vi.spyOn(window, "requestAnimationFrame").mockImplementation((callback) => {
      frames.push(callback);
      return frames.length;
    });
    vi.spyOn(window, "cancelAnimationFrame").mockImplementation(() => undefined);
    const visualizer = await mountTrack(100);
    const audio = visualizer.querySelector<HTMLAudioElement>(".aqe-audio-clock")!;
    Object.defineProperty(audio, "readyState", { configurable: true, value: 1 });
    audio.pause = vi.fn<() => void>(() => undefined);
    audio.dispatchEvent(new Event("loadedmetadata"));

    setPlaybackState(0, "playing", 100);
    expect(visualizer.dataset.progressClockMode).toBe("audio");

    audio.dispatchEvent(new Event("error"));
    expect(visualizer.dataset.progressClockMode).toBe("manual");

    visualizer.__aqeAudioClockAvailable = true;
    visualizer.dataset.progressClockMode = "audio";
    visualizer.dataset.playbackState = "playing";
    audio.dispatchEvent(new Event("ended"));
    expect(bridgeCommands()).toContain("aqe:play-ended");
    expect(visualizer.dataset.playbackState).toBe("stopped");
  });

  it("computes pause/resume playback requests and stop hooks", async () => {
    const visualizer = await mountTrack(300);
    visualizer.dataset.hasTrack = "true";
    visualizer.dataset.playbackEngine = "native";
    visualizer.dataset.playbackState = "playing";
    visualizer.dataset.progressClockMode = "manual";
    visualizer.dataset.playStartedAt = String(performance.now() - 125);
    visualizer.dataset.playStartMs = "300";

    const pause = playbackRequest(0);
    expect(pause.action).toBe("pause");
    expect(pause.engine).toBe("native");
    expect(pause.cursorMs).toBeGreaterThanOrEqual(300);

    visualizer.dataset.playbackState = "paused";
    visualizer.dataset.resumeRequiresRestart = "false";
    expect(playbackRequest(0).action).toBe("resume");
    visualizer.dataset.resumeRequiresRestart = "true";
    expect(playbackRequest(0).action).toBe("start");
    expect(stopEditorPlayback(0)).toBe(true);
    expect(stopEditorPlayback(9)).toBe(false);
  });

  it("supports pause and resume commands while HTML audio is active", async () => {
    const visualizer = await mountTrack(200);
    const audio = visualizer.querySelector<HTMLAudioElement>(".aqe-audio-clock")!;
    Object.defineProperty(audio, "readyState", { configurable: true, value: 1 });
    audio.play = vi.fn<() => Promise<void>>(() => Promise.resolve());
    audio.pause = vi.fn<() => void>(() => undefined);
    audio.dispatchEvent(new Event("loadedmetadata"));

    setPlaybackState(0, "playing", 200);
    await Promise.resolve();
    expect(handleHtmlPlaybackCommand(0)).toBe(true);
    expect(window.__aqeGetPlaybackRequest?.()).toMatchObject({ action: "pause", engine: "html", ord: 0 });

    visualizer.dataset.playbackState = "paused";
    visualizer.dataset.resumeRequiresRestart = "false";
    expect(handleHtmlPlaybackCommand(0)).toBe(true);
    await Promise.resolve();
    expect(window.__aqeGetPlaybackRequest?.()).toMatchObject({ action: "resume", engine: "html", ord: 0 });
  });

  it("advances manual clocks and exposes current progress", async () => {
    const frames: Array<(time: number) => void> = [];
    vi.spyOn(window, "requestAnimationFrame").mockImplementation((callback) => {
      frames.push(callback);
      return frames.length;
    });
    vi.spyOn(window, "cancelAnimationFrame").mockImplementation(() => undefined);
    const visualizer = await mountTrack(0);
    const audio = visualizer.querySelector<HTMLAudioElement>(".aqe-audio-clock")!;
    audio.pause = vi.fn<() => void>(() => undefined);
    startManualProgressClock(visualizer, 900);

    expect(visualizer.dataset.playbackState).toBe("playing");
    expect(currentProgressMs(visualizer)).toBeGreaterThanOrEqual(900);
    frames.shift()?.(performance.now() + 50);
    expect(Number(visualizer.dataset.progressMs)).toBeGreaterThanOrEqual(900);
  });
});
