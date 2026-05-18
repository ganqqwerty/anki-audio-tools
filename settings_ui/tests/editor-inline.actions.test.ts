import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  audioClockReady,
  clearAudioClockSource,
  clearSelectionDraft,
  configureAudioClock,
  currentProgressMs,
  clearSelection,
  commitSelectionDraft,
  draftSelectionForVisualizer,
  effectivePlaybackRegion,
  getCursorMs,
  getCursorIntent,
  getPlaybackRequest,
  handleHtmlPlaybackCommand,
  installAudioClockHandlers,
  pauseAudioClock,
  playbackRequest,
  resetGraphAfterEdit,
  seekAudioClock,
  selectionForVisualizer,
  setRepeatEnabled,
  setRepeatEnabledForOrd,
  setSelection,
  setSelectionDraft,
  setPlaybackState,
  setVisualizerStatusFromPython,
  shouldTreatSelectionGestureAsClick,
  startManualProgressClock,
  stopEditorPlayback,
} from "../src/editor-inline/actions.js";
import { mediaUrlForFilename } from "../src/editor-inline/audio-clock.js";
import { processingMessage } from "../src/editor-inline/commands.js";
import { visualizerForOrd } from "../src/editor-inline/dom-selectors.js";
import { commandSlugsForTest } from "../src/editor-inline/test-contract.js";
import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import type { VisualizerElement } from "../src/editor-inline/types.js";
import { pycmdMock } from "./setup.js";

const track = {
  analyzerName: "praat",
  durationMs: 1000,
  pitchMaxHz: 300,
  pitchMinHz: 100,
  points: [
    [0, 120, 0.1, true],
    [500, 180, 0.8, true],
    [1000, 220, 0.6, true],
  ],
  sourceFilename: "nested/clip two.mp3",
};

async function mountTrack(cursorMs = 250): Promise<VisualizerElement> {
  document.body.innerHTML = `
    <div class="field-container" data-index="0">
      <div contenteditable="true" id="audio0">[sound:nested/clip two.mp3]</div>
    </div>
  `;
  initializeEditorRuntime({ audioFieldIndices: [0] });
  scan({ audioFieldIndices: [0] });
  await Promise.resolve();
  window.__aqeSetVisualizer?.(0, track, cursorMs);
  const visualizer = visualizerForOrd(0);
  if (!visualizer) throw new Error("visualizer not mounted");
  return visualizer;
}

function bridgeCommands(): string[] {
  return pycmdMock.mock.calls.map(([command]) => command);
}

describe("editor inline action workflows", () => {
  let warnSpy: ReturnType<typeof vi.spyOn>;
  let errorSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    warnSpy = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    errorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
  });

  afterEach(() => {
    disposeEditorRuntime();
    vi.restoreAllMocks();
  });

  it("encodes media names while preserving nested Anki media paths", () => {
    expect(mediaUrlForFilename("hello world.mp3")).toBe("hello%20world.mp3");
    expect(mediaUrlForFilename("かな.wav")).toBe("%E3%81%8B%E3%81%AA.wav");
    expect(mediaUrlForFilename("nested/clip.mp3")).toBe("nested/clip.mp3");
    expect(commandSlugsForTest()["aqe:denoise-standard"]).toBe("denoise-standard");
    expect(commandSlugsForTest()["aqe:rnnoise"]).toBe("rnnoise");
    expect(commandSlugsForTest()["aqe:redo"]).toBe("redo");
    expect(commandSlugsForTest()["aqe:settings"]).toBe("settings");
    expect(processingMessage("aqe:denoise-standard")).toBe("Denoising with Standard...");
    expect(processingMessage("aqe:rnnoise")).toBe("Denoising with RNNoise...");
    expect(processingMessage("aqe:faster")).toBe("Processing...");
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

  it("normalizes selection state and includes region fields in playback requests", async () => {
    const visualizer = await mountTrack(300);

    expect(selectionForVisualizer(visualizer)).toBeNull();
    expect(effectivePlaybackRegion(visualizer)).toEqual({ startMs: 0, endMs: 1000, mode: "full" });

    expect(setSelection(visualizer, 900, 200)).toBe(true);
    expect(selectionForVisualizer(visualizer)).toEqual({ startMs: 200, endMs: 900, mode: "selection" });
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: true,
      selectionStartMs: 200,
      selectionEndMs: 900,
      playbackRegionMode: "selection",
    });
    expect(playbackRequest(0)).toMatchObject({
      action: "start",
      cursorMs: 200,
      endMs: 900,
      loop: false,
      regionMode: "selection",
    });

    setRepeatEnabled(visualizer, true);
    expect(playbackRequest(0)).toMatchObject({ loop: true });
    clearSelection(visualizer);
    expect(effectivePlaybackRegion(visualizer)).toEqual({ startMs: 0, endMs: 1000, mode: "full" });
    expect(playbackRequest(0)).toMatchObject({ cursorMs: 200, endMs: 1000, regionMode: "full" });
  });

  it("rejects tiny selection gestures using pixel and time thresholds", () => {
    expect(shouldTreatSelectionGestureAsClick({ clientX: 10 }, { clientX: 12 }, 100, 250)).toBe(true);
    expect(shouldTreatSelectionGestureAsClick({ clientX: 10 }, { clientX: 60 }, 100, 125)).toBe(true);
    expect(shouldTreatSelectionGestureAsClick({ clientX: 10 }, { clientX: 60 }, 100, 250)).toBe(false);
  });

  it("keeps draft selection preview separate until it is committed", async () => {
    const visualizer = await mountTrack(300);
    expect(setSelection(visualizer, 100, 300)).toBe(true);

    expect(setSelectionDraft(visualizer, 800, 400)).toBe(true);
    expect(selectionForVisualizer(visualizer)).toEqual({ startMs: 100, endMs: 300, mode: "selection" });
    expect(draftSelectionForVisualizer(visualizer)).toEqual({ startMs: 400, endMs: 800, mode: "selection" });
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: true,
      selectionStartMs: 100,
      selectionEndMs: 300,
      selectionDraftActive: true,
      selectionDraftStartMs: 400,
      selectionDraftEndMs: 800,
    });
    expect(visualizer.querySelector(".aqe-selection")).toHaveClass("aqe-selection-draft");

    expect(commitSelectionDraft(visualizer)).toBe(true);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      cursorMs: 400,
      selectionActive: true,
      selectionStartMs: 400,
      selectionEndMs: 800,
      selectionDraftActive: false,
      selectionDraftStartMs: null,
      selectionDraftEndMs: null,
    });
    expect(visualizer.querySelector(".aqe-selection")).not.toHaveClass("aqe-selection-draft");

    expect(setSelectionDraft(visualizer, 200, 220)).toBe(false);
    expect(draftSelectionForVisualizer(visualizer)).toBeNull();
    expect(selectionForVisualizer(visualizer)).toEqual({ startMs: 400, endMs: 800, mode: "selection" });
    clearSelectionDraft(visualizer);
    expect(window.__aqeGraphStateForTest?.(0)?.selectionDraftActive).toBe(false);
  });

  it("handles selection guard branches and direct playback request reads", async () => {
    const visualizer = await mountTrack(300);

    expect(setRepeatEnabledForOrd(99, true)).toBe(false);
    expect(setSelection(visualizer, 100, 120)).toBe(false);
    expect(selectionForVisualizer(visualizer)).toBeNull();

    expect(setSelection(visualizer, 100, 300, { updateCursor: false })).toBe(true);
    expect(visualizer.dataset.cursorMs).toBe("300");
    window.__aqeActiveField = 0;
    const request = getPlaybackRequest();
    expect(request).toMatchObject({ cursorMs: 100, endMs: 300, regionMode: "selection" });
    expect(visualizer.dataset.playbackEngine).toBe(request.engine);

    visualizer.dataset.durationMs = "0";
    expect(setSelection(visualizer, 0, 200)).toBe(false);
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

  it("updates visualizer status, redraw state, cursor helpers, and test driver", async () => {
    const visualizer = await mountTrack(0);

    setVisualizerStatusFromPython(0, "Analyzing...", "processing");
    expect(visualizer.dataset.hasTrack).toBe("false");
    expect(window.__aqeGraphStateForTest?.(0)?.spinnerVisible).toBe(true);

    window.__aqeActiveField = 0;
    expect(window.__aqeSetCursorForTest?.(0, 450, false)).toBe(true);
    expect(getCursorMs()).toBe(450);
    expect(window.__aqeSetCursorForTest?.(99, 450, false)).toBe(false);
    expect(window.__aqeInstallAudioPlaybackTestDriverForTest?.(0)).toBe(true);
    expect(window.__aqeGraphStateForTest?.(0)?.audioPlaybackTestDriver).toBe(true);
    const audio = visualizer.querySelector<HTMLAudioElement>(".aqe-audio-clock")!;
    const frames: Array<(time: number) => void> = [];
    vi.spyOn(window, "requestAnimationFrame").mockImplementation((callback) => {
      frames.push(callback);
      return frames.length;
    });
    vi.spyOn(window, "cancelAnimationFrame").mockImplementation(() => undefined);
    await audio.play();
    expect(frames).toHaveLength(1);
    audio.currentTime = 1;
    frames.shift()?.(performance.now() + 1100);
    const testAudio = audio as HTMLAudioElement & { __aqeTestPlaying?: boolean };
    expect(testAudio.__aqeTestPlaying).toBe(false);
    expect(window.__aqeInstallAudioPlaybackTestDriverForTest?.(99)).toBe(false);
    window.__aqeLastCursorIntent = null;
    expect(getCursorIntent()).toMatchObject({
      cursorMs: 450,
      previousPlaybackState: "stopped",
      restartPlayback: false,
    });
    expect(resetGraphAfterEdit(0)).toBe(true);
    expect(resetGraphAfterEdit(99)).toBe(false);
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
    frames.shift()?.(performance.now() + 200);
    expect(Number(visualizer.dataset.progressMs)).toBeGreaterThanOrEqual(900);
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
});
