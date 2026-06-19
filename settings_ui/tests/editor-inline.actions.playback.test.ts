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
  setRepeatEnabled,
  setPlaybackState,
  startManualProgressClock,
  stopEditorPlayback,
} from "../src/editor-inline/actions.js";
import { readFieldState, updateFieldState } from "../src/editor-inline/field-state-store.js";
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
    Object.defineProperty(audio, "duration", { configurable: true, value: 1 });
    audio.pause = vi.fn<() => void>(() => undefined);
    audio.dispatchEvent(new Event("loadedmetadata"));

    setPlaybackState(0, "playing", 100);
    expect(readFieldState(0).playback.clockMode).toBe("audio");

    audio.dispatchEvent(new Event("error"));
    expect(readFieldState(0).playback.clockMode).toBe("manual");

    visualizer.__aqeAudioClockAvailable = true;
    updateFieldState(0, (state) => ({
      ...state,
      playback: { ...state.playback, clockMode: "audio", state: "playing" },
    }));
    audio.dispatchEvent(new Event("ended"));
    expect(bridgeCommands()).toContain("aqe:play-ended");
    expect(readFieldState(0).playback.state).toBe("stopped");
  });

  it("uses media duration when an ended event repeats with stale graph duration state", async () => {
    vi.spyOn(window, "requestAnimationFrame").mockImplementation(() => 1);
    vi.spyOn(window, "cancelAnimationFrame").mockImplementation(() => undefined);
    const visualizer = await mountTrack(0);
    const audio = visualizer.querySelector<HTMLAudioElement>(".aqe-audio-clock")!;
    Object.defineProperty(audio, "readyState", { configurable: true, value: 1 });
    Object.defineProperty(audio, "duration", { configurable: true, value: 1 });
    audio.play = vi.fn<() => Promise<void>>(() => Promise.resolve());
    audio.pause = vi.fn<() => void>(() => undefined);
    audio.dispatchEvent(new Event("loadedmetadata"));
    setRepeatEnabled(visualizer, true);
    updateFieldState(0, (state) => ({
      ...state,
      playback: { ...state.playback, engine: "html" },
    }));

    setPlaybackState(0, "playing", 0);
    await Promise.resolve();
    await Promise.resolve();
    expect(audio.play).toHaveBeenCalledTimes(1);

    updateFieldState(0, (state) => ({
      ...state,
      graph: { ...state.graph, durationMs: 0 },
    }));
    audio.dispatchEvent(new Event("ended"));
    await Promise.resolve();
    await Promise.resolve();

    expect(audio.play).toHaveBeenCalledTimes(2);
  });

  it("uses media current time when an audio error falls back with stale cursor state", async () => {
    const frames: Array<(time: number) => void> = [];
    vi.spyOn(window, "requestAnimationFrame").mockImplementation((callback) => {
      frames.push(callback);
      return frames.length;
    });
    vi.spyOn(window, "cancelAnimationFrame").mockImplementation(() => undefined);
    const visualizer = await mountTrack(0);
    const audio = visualizer.querySelector<HTMLAudioElement>(".aqe-audio-clock")!;
    Object.defineProperty(audio, "readyState", { configurable: true, value: 1 });
    Object.defineProperty(audio, "duration", { configurable: true, value: 1 });
    audio.play = vi.fn<() => Promise<void>>(() => Promise.resolve());
    audio.pause = vi.fn<() => void>(() => undefined);
    audio.dispatchEvent(new Event("loadedmetadata"));
    updateFieldState(0, (state) => ({
      ...state,
      playback: { ...state.playback, engine: "html" },
    }));

    setPlaybackState(0, "playing", 0);
    await Promise.resolve();
    await Promise.resolve();
    audio.currentTime = 0.4;
    updateFieldState(0, (state) => ({
      ...state,
      cursor: { ...state.cursor, ms: 0, progressMs: 0 },
    }));

    audio.dispatchEvent(new Event("error"));

    expect(readFieldState(0).playback.clockMode).toBe("manual");
    expect(readFieldState(0).cursor.progressMs).toBe(400);
  });

  it("computes pause/resume playback requests and stop hooks", async () => {
    const visualizer = await mountTrack(300);
    updateFieldState(0, (state) => ({
      ...state,
      graph: { ...state.graph, hasTrack: true },
      playback: { ...state.playback, clockMode: "manual", engine: "native", state: "playing" },
    }));
    visualizer.dataset.playStartedAt = String(performance.now() - 125);
    visualizer.dataset.playStartMs = "300";

    const pause = playbackRequest(0);
    expect(pause.action).toBe("pause");
    expect(pause.engine).toBe("native");
    expect(pause.cursorMs).toBeGreaterThanOrEqual(300);

    updateFieldState(0, (state) => ({
      ...state,
      playback: { ...state.playback, resumeRequiresRestart: false, state: "paused" },
    }));
    expect(playbackRequest(0).action).toBe("resume");
    updateFieldState(0, (state) => ({
      ...state,
      playback: { ...state.playback, resumeRequiresRestart: true },
    }));
    expect(playbackRequest(0).action).toBe("start");
    expect(stopEditorPlayback(0)).toBe(true);
    expect(stopEditorPlayback(9)).toBe(false);
  });

  it("logs selected playback engine and native reason for playback requests", async () => {
    const visualizer = await mountTrack(100);
    visualizer.__aqeHtmlAudioFailureReason = "audio_error";
    warnSpy.mockClear();

    const request = playbackRequest(0);

    expect(request.engine).toBe("native");
    expect(warnSpy).toHaveBeenCalledWith(
      "[editor] playback.engine_selected",
      expect.objectContaining({
        action: "start",
        audioClockReady: false,
        engine: "native",
        graphHasTrack: true,
        htmlAudioReadinessReason: "audio_error",
        htmlAudioReadinessState: "failed",
        reason: "audio_readiness_failed",
        trigger: "playback_request",
      }),
    );
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

    updateFieldState(0, (state) => ({
      ...state,
      playback: { ...state.playback, resumeRequiresRestart: false, state: "paused" },
    }));
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

    expect(readFieldState(0).playback.state).toBe("playing");
    expect(currentProgressMs(visualizer)).toBeGreaterThanOrEqual(900);
    frames.shift()?.(performance.now() + 50);
    expect(readFieldState(0).cursor.progressMs).toBeGreaterThanOrEqual(900);
  });
});
