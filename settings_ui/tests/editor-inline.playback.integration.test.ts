import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { completePlayback } from "../src/editor-inline/actions.js";
import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import {
  bridgeCommands,
  dragGraphSelection,
  muteConsole,
  renderFields,
  setRepeatMode,
  setGraphBounds,
  track,
} from "./editor-inline.integration.helpers.js";

describe("editor inline playback integration", () => {

let restoreConsole: () => void;

beforeEach(() => {
  restoreConsole = muteConsole();
  renderFields();
});

afterEach(() => {
  disposeEditorRuntime();
  restoreConsole();
  vi.restoreAllMocks();
});

  it("disables controls during processing commands and resets note state", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-volume-up"]')!.click();

    expect(bridgeCommands()).toContain("aqe:command-payload");
    expect(window.__aqePendingCommandPayload?.command).toBe("aqe:volume-up");
    expect(window.__aqeGraphStateForTest?.(0)?.allButtonsDisabled).toBe(true);
    expect(window.__aqeGraphStateForTest?.(0)?.repeatControlDisabled).toBe(true);
    expect(document.querySelector('[data-testid="aqe-status-0"]')).toHaveTextContent("Processing...");

    window.__aqePrepareForNewNote?.();

    expect(window.__aqeGraphStateForTest?.(0)?.allButtonsDisabled).toBe(false);
    expect(window.__aqeGraphStateForTest?.(0)?.repeatControlDisabled).toBe(false);
    expect(document.querySelector('[data-testid="aqe-status-0"]')).toHaveTextContent("");
  });

  it("restores the last final status when busy processing clears", () => {
    initializeEditorRuntime({
      audioFieldIndices: [0],
      initialStatusByField: {
        0: { kind: "info", message: "Closed settings." },
      },
    });
    scan({
      audioFieldIndices: [0],
      initialStatusByField: {
        0: { kind: "info", message: "Closed settings." },
      },
    });

    window.__aqeSetBusy?.(0, true, "Still processing. Please wait.");
    expect(document.querySelector('[data-testid="aqe-status-0"]')).toHaveTextContent("Still processing. Please wait.");

    window.__aqeSetBusy?.(0, false);

    expect(document.querySelector('[data-testid="aqe-status-0"]')).toHaveTextContent("Closed settings.");
  });

  it("keeps the final edit summary after a successful graph redraw", async () => {
    initializeEditorRuntime({
      audioFieldIndices: [0],
      initialStatusByField: {
        0: { kind: "info", message: "Increased volume by 3 dB." },
      },
    });
    scan({
      audioFieldIndices: [0],
      initialStatusByField: {
        0: { kind: "info", message: "Increased volume by 3 dB." },
      },
    });

    await Promise.resolve();
    window.__aqeSetVisualizerStatus?.(0, "Analyzing...", "processing");
    expect(document.querySelector('[data-testid="aqe-status-0"]')).toHaveTextContent("Analyzing...");

    window.__aqeSetVisualizer?.(0, track, 400);

    expect(document.querySelector('[data-testid="aqe-status-0"]')).toHaveTextContent(
      "Increased volume by 3 dB.",
    );
  });

  it("restores the stable status after post-edit playback completes", async () => {
    initializeEditorRuntime({
      audioFieldIndices: [0],
      initialStatusByField: {
        0: { kind: "info", message: "Undid: Increased speed to x1.05." },
      },
    });
    scan({
      audioFieldIndices: [0],
      initialStatusByField: {
        0: { kind: "info", message: "Undid: Increased speed to x1.05." },
      },
    });

    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 400);

    expect(window.__aqePlayAfterEdit?.(0)).toBe(true);

    const visualizer = document.querySelector('[data-testid="aqe-graph-0"]') as Parameters<typeof completePlayback>[0] | null;
    expect(visualizer).not.toBeNull();

    completePlayback(visualizer!);

    expect(document.querySelector('[data-testid="aqe-status-0"]')).toHaveTextContent(
      "Undid: Increased speed to x1.05.",
    );
    expect(bridgeCommands()).toContain("aqe:play-ended");
  });

  it("uses HTML audio playback and queues the Python bridge request", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 400);
    const audio = document.querySelector<HTMLAudioElement>('[data-testid="aqe-audio-clock-0"]')!;
    Object.defineProperty(audio, "readyState", { configurable: true, value: 1 });
    audio.play = vi.fn<() => Promise<void>>(() => Promise.resolve());
    audio.pause = vi.fn<() => void>(() => undefined);
    audio.dispatchEvent(new Event("loadedmetadata"));

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();

    const request = window.__aqeGetPlaybackRequest?.();
    expect(request).toEqual({
      action: "start",
      cursorMs: 0,
      endMs: 1000,
      engine: "html",
      loop: false,
      ord: 0,
      regionMode: "selection",
    });
    expect(window.__aqeGraphStateForTest?.(0)?.playbackState).toBe("playing");
    expect(window.__aqeGraphStateForTest?.(0)?.playbackEngine).toBe("html");
  });

  it("uses hidden HTML audio playback for full-file repeat before the graph is shown", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    const visualizer = document.querySelector<HTMLElement>('[data-testid="aqe-graph-0"]')!;
    const audio = document.querySelector<HTMLAudioElement>('[data-testid="aqe-audio-clock-0"]')!;
    expect(audio.getAttribute("src")).toBe("clip%20one.mp3");
    Object.defineProperty(audio, "duration", { configurable: true, value: 1 });
    Object.defineProperty(audio, "readyState", { configurable: true, value: 1 });
    audio.play = vi.fn<() => Promise<void>>(() => Promise.resolve());
    audio.pause = vi.fn<() => void>(() => undefined);
    audio.dispatchEvent(new Event("loadedmetadata"));
    expect(window.__aqeGraphStateForTest?.(0)?.durationMs).toBe(1000);

    await setRepeatMode(true);
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();

    expect(window.__aqeGetPlaybackRequest?.()).toEqual({
      action: "start",
      cursorMs: 0,
      endMs: 1000,
      engine: "html",
      loop: true,
      ord: 0,
      regionMode: "full",
    });
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      hidden: true,
      hasTrack: false,
      playbackEngine: "html",
      playbackState: "playing",
      repeatEnabled: true,
    });
  });

  it("shows pause for native playback before the hidden audio duration is known", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();

    const playButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!;
    playButton.click();

    expect(window.__aqeGetPlaybackRequest?.()).toMatchObject({
      action: "start",
      cursorMs: 0,
      engine: "native",
      ord: 0,
      regionMode: "full",
    });

    window.__aqeSetPlaybackState?.(0, "playing", 0);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      durationMs: 0,
      hidden: true,
      playbackEngine: "native",
      playbackState: "playing",
      playButtonLabel: "Pause",
    });

    window.__aqeSetPlaybackState?.(0, "stopped", 0);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "stopped",
      playButtonLabel: "Play",
    });
  });

  it("starts HTML playback from an explicit selected region", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 400);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    svg.getBoundingClientRect = () => ({
      bottom: 150,
      height: 150,
      left: 0,
      right: 620,
      top: 0,
      width: 620,
      x: 0,
      y: 0,
      toJSON: () => ({}),
    });
    dragGraphSelection(svg, 0.25, 0.75);
    const audio = document.querySelector<HTMLAudioElement>('[data-testid="aqe-audio-clock-0"]')!;
    Object.defineProperty(audio, "readyState", { configurable: true, value: 1 });
    audio.play = vi.fn<() => Promise<void>>(() => Promise.resolve());
    audio.pause = vi.fn<() => void>(() => undefined);
    audio.dispatchEvent(new Event("loadedmetadata"));

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();

    expect(window.__aqeGetPlaybackRequest?.()).toEqual({
      action: "start",
      cursorMs: 250,
      endMs: 750,
      engine: "html",
      loop: false,
      ord: 0,
      regionMode: "selection",
    });
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackStartMs: 250,
      playbackEndMs: 750,
      playbackRegionMode: "selection",
    });
  });

  it("stops HTML playback immediately before processing commands", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 400);
    const audio = document.querySelector<HTMLAudioElement>('[data-testid="aqe-audio-clock-0"]')!;
    Object.defineProperty(audio, "readyState", { configurable: true, value: 1 });
    audio.play = vi.fn<() => Promise<void>>(() => Promise.resolve());
    audio.pause = vi.fn<() => void>(() => undefined);
    audio.dispatchEvent(new Event("loadedmetadata"));

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)?.playbackState).toBe("playing");

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-volume-up"]')!.click();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "stopped",
      playButtonLabel: "Play",
      allButtonsDisabled: true,
    });
    expect(bridgeCommands()).not.toContain("aqe:play-ended");
  });

  it("falls back to native playback when HTML play rejects", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 700);
    const audio = document.querySelector<HTMLAudioElement>('[data-testid="aqe-audio-clock-0"]')!;
    Object.defineProperty(audio, "readyState", { configurable: true, value: 1 });
    audio.play = vi.fn<() => Promise<void>>(() => Promise.reject(new Error("blocked")));
    audio.pause = vi.fn<() => void>(() => undefined);
    audio.dispatchEvent(new Event("loadedmetadata"));

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();
    await Promise.resolve();

    expect(window.__aqeGetPlaybackRequest?.()).toEqual({
      action: "start",
      cursorMs: 0,
      endMs: 1000,
      engine: "native",
      loop: false,
      ord: 0,
      regionMode: "selection",
    });
    expect(window.__aqeGraphStateForTest?.(0)?.playbackState).toBe("stopped");
  });

  it("falls back to native selected playback when HTML one-shot play rejects", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 700);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.25, 0.75);
    const audio = document.querySelector<HTMLAudioElement>('[data-testid="aqe-audio-clock-0"]')!;
    Object.defineProperty(audio, "readyState", { configurable: true, value: 1 });
    audio.play = vi.fn<() => Promise<void>>(() => Promise.reject(new Error("blocked")));
    audio.pause = vi.fn<() => void>(() => undefined);
    audio.dispatchEvent(new Event("loadedmetadata"));

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();
    await Promise.resolve();

    expect(bridgeCommands()).toContain("aqe:play");
    expect(window.__aqeGetPlaybackRequest?.()).toEqual({
      action: "start",
      cursorMs: 250,
      endMs: 750,
      engine: "native",
      loop: false,
      ord: 0,
      regionMode: "selection",
    });
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "stopped",
      selectionStartMs: 250,
      selectionEndMs: 750,
      playbackRegionMode: "selection",
    });
  });

});
