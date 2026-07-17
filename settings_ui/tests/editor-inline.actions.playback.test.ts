import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  audioClockReady,
  clearAudioClockSource,
  configureAudioClock,
  handleHtmlPlaybackCommand,
  pauseAudioClock,
  playbackRequest,
  seekAudioElementForCursorPreview,
  startSourcePlayback,
  stopEditorPlayback,
} from "../src/editor-inline/actions.js";
import { htmlAudioReadinessFor } from "../src/editor-inline/audio-readiness.js";
import { readFieldState, updateFieldState } from "../src/editor-inline/field-state-store.js";
import { disposeEditorRuntime } from "../src/editor-inline/runtime.js";
import type { VisualizerElement } from "../src/editor-inline/types.js";
import { bridgeCommands, mountTrack } from "./editor-inline.actions.helpers.js";

describe("editor inline audio-clock workflows", () => {
  let warnSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    warnSpy = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    vi.spyOn(console, "error").mockImplementation(() => undefined);
  });

  afterEach(() => {
    disposeEditorRuntime();
    vi.restoreAllMocks();
  });

  it("handles audio-port setup, preview seek, clear, and failure branches", async () => {
    const visualizer = await mountTrack();
    const audio = prepareAudio(visualizer);

    expect(audioClockReady(visualizer)).toBe(true);
    expect(seekAudioElementForCursorPreview(visualizer, 500)).toBe(true);
    expect(Math.round(audio.currentTime * 1000)).toBe(500);

    audio.pause = vi.fn<() => void>(() => {
      throw new Error("pause failed");
    });
    pauseAudioClock(visualizer);
    expect(htmlAudioReadinessFor(visualizer).failed).toBe(true);

    audio.load = vi.fn<() => void>(() => {
      throw new Error("load failed");
    });
    configureAudioClock(visualizer, "");
    expect(htmlAudioReadinessFor(visualizer).state).toBe("source_missing");
    clearAudioClockSource(visualizer);
    expect(audio.getAttribute("src") ?? "").toBe("");
  });

  it("stops an active attempt on a source error and ignores ended without an attempt", async () => {
    const visualizer = await mountTrack(100);
    const audio = prepareAudio(visualizer);
    await startPlayback(visualizer, 100);

    expect(readFieldState(0).playback.clockMode).toBe("audio");
    audio.dispatchEvent(new Event("error"));
    expect(readFieldState(0).playback).toMatchObject({ clockMode: "stopped", state: "stopped" });

    updateFieldState(0, (state) => ({
      ...state,
      playback: { ...state.playback, clockMode: "audio", state: "playing" },
    }));
    audio.dispatchEvent(new Event("ended"));
    expect(bridgeCommands()).not.toContain("aqe:play-ended");
    expect(readFieldState(0).playback.state).toBe("playing");
  });

  it("uses the media position when an audio error stops a stale cursor projection", async () => {
    const visualizer = await mountTrack(0);
    const audio = prepareAudio(visualizer);
    await startPlayback(visualizer, 0);
    audio.currentTime = 0.4;
    updateFieldState(0, (state) => ({
      ...state,
      cursor: { ...state.cursor, ms: 0, progressMs: 0 },
    }));

    audio.dispatchEvent(new Event("error"));

    expect(readFieldState(0).playback.clockMode).toBe("stopped");
    expect(readFieldState(0).cursor.progressMs).toBe(400);
  });

  it("derives pause, resume, and stop commands from the transport snapshot", async () => {
    const visualizer = await mountTrack(300);
    prepareAudio(visualizer);
    await startPlayback(visualizer, 300);

    expect(playbackRequest(0)).toMatchObject({ action: "pause", cursorMs: 300, engine: "html" });
    expect(handleHtmlPlaybackCommand(0)).toBe(true);
    expect(playbackRequest(0).action).toBe("resume");

    expect(handleHtmlPlaybackCommand(0)).toBe(true);
    await flushPlayback();
    expect(playbackRequest(0).action).toBe("pause");
    expect(stopEditorPlayback(0)).toBe(true);
    expect(stopEditorPlayback(0)).toBe(false);
    expect(stopEditorPlayback(9)).toBe(false);
  });

  it("logs the typed browser failure reason for playback requests", async () => {
    const visualizer = await mountTrack(100);
    const audio = prepareAudio(visualizer);
    audio.dispatchEvent(new Event("error"));
    warnSpy.mockClear();

    const request = playbackRequest(0);

    expect(request.engine).toBe("html");
    expect(warnSpy).toHaveBeenCalledWith(
      "[editor] playback.readiness_described",
      expect.objectContaining({
        action: "start",
        audioClockReady: false,
        engine: "html",
        htmlAudioReadinessReason: "audio_error",
        htmlAudioReadinessState: "failed",
        reason: "audio_readiness_failed",
      }),
    );
  });
});

function prepareAudio(visualizer: VisualizerElement): HTMLAudioElement {
  const audio = visualizer.querySelector<HTMLAudioElement>(".aqe-audio-clock")!;
  Object.defineProperty(audio, "duration", { configurable: true, value: 1 });
  Object.defineProperty(audio, "readyState", { configurable: true, value: 1 });
  audio.play = vi.fn<() => Promise<void>>(() => Promise.resolve());
  audio.pause = vi.fn<() => void>(() => undefined);
  audio.dispatchEvent(new Event("loadedmetadata"));
  return audio;
}

async function startPlayback(visualizer: VisualizerElement, cursorMs: number): Promise<void> {
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
  await flushPlayback();
}

async function flushPlayback(): Promise<void> {
  await Promise.resolve();
  await Promise.resolve();
}
