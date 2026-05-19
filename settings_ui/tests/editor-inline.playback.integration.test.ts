import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import {
  bridgeCommands,
  dragGraphSelection,
  muteConsole,
  renderFields,
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
      cursorMs: 400,
      endMs: 1000,
      engine: "html",
      loop: false,
      ord: 0,
      regionMode: "full",
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

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-repeat-0"]')!.click();
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
      cursorMs: 700,
      endMs: 1000,
      engine: "native",
      loop: false,
      ord: 0,
      regionMode: "full",
    });
    expect(window.__aqeGraphStateForTest?.(0)?.playbackState).toBe("stopped");
  });

  it("does not claim native selected playback when HTML play rejects", async () => {
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

    expect(bridgeCommands()).not.toContain("aqe:play");
    expect(document.querySelector('[data-testid="aqe-status-0"]')).toHaveTextContent(
      "Repeat playback needs browser audio.",
    );
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "stopped",
      selectionStartMs: 250,
      selectionEndMs: 750,
      playbackRegionMode: "selection",
    });
  });

  it("commits cursor intents from rendered graph coordinates", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 0);
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

    const result = window.__aqeSetCursorByClientXForTest?.(0, 44 + 566 * 0.6, true);

    expect(result?.cursorMs).toBe(600);
    expect(window.__aqeGetCursorIntent?.()).toMatchObject({
      cursorMs: 600,
      previousPlaybackState: "stopped",
      restartPlayback: false,
    });
    expect(bridgeCommands()).toContain("aqe:set-cursor");
  });

  it("exposes editor frontend logs through a pop queue", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-show-file"]')!.click();

    const payloads = Array.from({ length: 20 }, () => window.__aqePopFrontendLog?.());
    const payload = payloads.find((item) => item?.message === "command dispatched");
    expect(payload).toMatchObject({
      level: "info",
      message: "command dispatched",
    });
  });
});
