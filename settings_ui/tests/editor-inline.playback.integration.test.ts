import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { completePlayback, startSourcePlayback } from "../src/editor-inline/actions.js";
import { dispatchHtmlAudioSessionEvent } from "../src/editor-inline/html-audio-session-controller.js";
import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import {
  bridgeCommands,
  dragGraphSelection,
  muteConsole,
  prepareHtmlAudio,
  peekPendingCommandPayload,
  renderFields,
  setFullGraphViewport,
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
  vi.useRealTimers();
  vi.restoreAllMocks();
});

  it("disables controls during processing commands and resets note state", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();

    const playButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!;
    expect(playButton.getAttribute("data-aqe-tooltip-content")).toContain("Loading audio metadata...");

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-volume-up"]')!.click();

    expect(bridgeCommands()).toContain("aqe:command-payload");
    expect(peekPendingCommandPayload()?.command).toBe("aqe:volume-up");
    expect(window.__aqeGraphStateForTest?.(0)?.allButtonsDisabled).toBe(true);
    expect(window.__aqeGraphStateForTest?.(0)?.repeatControlDisabled).toBe(true);
    expect(playButton).toHaveAttribute(
      "data-aqe-tooltip-content",
      "Play\nPlay or pause the current audio\n\nWait for the current audio operation to finish.",
    );
    expect(document.querySelector('[data-testid="aqe-status-0"]')).toHaveTextContent("Processing...");

    window.__aqePrepareForNewNote?.();

    expect(window.__aqeGraphStateForTest?.(0)?.allButtonsDisabled).toBe(false);
    expect(window.__aqeGraphStateForTest?.(0)?.repeatControlDisabled).toBe(false);
    expect(playButton.getAttribute("data-aqe-tooltip-content")).toContain("Loading audio metadata...");
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

  it("keeps post-edit playback blocked when the legacy busy attribute is corrupted", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 400);
    window.__aqeSetBusy?.(0, true, "Still processing. Please wait.");

    document.body.dataset.aqeBusy = "false";

    expect(window.__aqePlayAfterEdit?.(0)).toBe(false);
    expect(bridgeCommands()).not.toContain("aqe:play");
  });

  it("keeps the final edit summary after a successful graph redraw", async () => {
    initializeEditorRuntime({
      audioFieldIndices: [0],
      initialStatusByField: {
        0: { kind: "info", message: "Increased volume by 15 dB." },
      },
    });
    scan({
      audioFieldIndices: [0],
      initialStatusByField: {
        0: { kind: "info", message: "Increased volume by 15 dB." },
      },
    });

    await Promise.resolve();
    window.__aqeSetVisualizerStatus?.(0, "Analyzing...", "processing");
    expect(document.querySelector('[data-testid="aqe-status-0"]')).toHaveTextContent("Analyzing...");

    window.__aqeSetVisualizer?.(0, track, 400);

    expect(document.querySelector('[data-testid="aqe-status-0"]')).toHaveTextContent(
      "Increased volume by 15 dB.",
    );
  });

  it("restores the stable status after post-edit playback completes", async () => {
    initializeEditorRuntime({
      audioFieldIndices: [0],
      initialStatusByField: {
        0: { kind: "info", message: "Undid: Increased speed to x1.5." },
      },
    });
    scan({
      audioFieldIndices: [0],
      initialStatusByField: {
        0: { kind: "info", message: "Undid: Increased speed to x1.5." },
      },
    });

    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 400);
    prepareHtmlAudio(0);

    expect(window.__aqePlayAfterEdit?.(0)).toBe(true);

    const visualizer = document.querySelector('[data-testid="aqe-graph-0"]') as Parameters<typeof completePlayback>[0] | null;
    expect(visualizer).not.toBeNull();

    completePlayback(visualizer!);

    expect(document.querySelector('[data-testid="aqe-status-0"]')).toHaveTextContent(
      "Undid: Increased speed to x1.5.",
    );
    expect(bridgeCommands()).toContain("aqe:play-ended");
  });

  it("clears playback-owned warning without erasing edit-owned status", async () => {
    const config = {
      audioFieldIndices: [0],
      initialStatusByField: {
        0: { kind: "info", message: "Closed settings." },
      },
    };
    initializeEditorRuntime(config);
    scan(config);
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 400);

    const status = document.querySelector<HTMLElement>('[data-testid="aqe-status-0"]')!;
    const visualizer = document.querySelector('[data-testid="aqe-graph-0"]') as Parameters<typeof completePlayback>[0] | null;
    expect(visualizer).not.toBeNull();

    window.__aqeSetStatus?.("Selected repeat playback needs browser audio.", "warning", "playback");
    expect(status).toHaveTextContent("Selected repeat playback needs browser audio.");
    expect(status.dataset.statusOwner).toBe("playback");

    completePlayback(visualizer!);

    expect(status).toHaveTextContent("Closed settings.");
    expect(status.dataset.statusOwner).toBe("edit");
  });

  it("uses HTML audio playback without queueing a Python bridge request", async () => {
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

    expect(audio.play).toHaveBeenCalledTimes(1);
    expect(window.__aqePendingPlaybackRequest).toBeNull();
    expect(bridgeCommands()).not.toContain("aqe:play");
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

    expect(audio.loop).toBe(false);
    expect(audio.play).toHaveBeenCalledTimes(1);
    expect(window.__aqePendingPlaybackRequest).toBeNull();
    expect(bridgeCommands()).not.toContain("aqe:play");
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      hidden: true,
      hasTrack: false,
      playbackEngine: "html",
      playbackState: "playing",
      repeatEnabled: true,
    });

    await setRepeatMode(false);

    expect(audio.loop).toBe(false);
  });

  it("blocks hidden playback until audio metadata is ready", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();

    const playButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!;
    const audio = document.querySelector<HTMLAudioElement>('[data-testid="aqe-audio-clock-0"]')!;
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      durationMs: 0,
      hidden: true,
      htmlAudioReadinessState: "loading_metadata",
    });
    expect(playButton.disabled).toBe(true);
    expect(playButton.getAttribute("data-aqe-tooltip-content")).toContain("Loading audio metadata...");

    playButton.click();

    expect(bridgeCommands()).not.toContain("aqe:play");

    Object.defineProperty(audio, "duration", { configurable: true, value: 1 });
    Object.defineProperty(audio, "readyState", { configurable: true, value: 1 });
    audio.play = vi.fn<() => Promise<void>>(() => Promise.resolve());
    audio.pause = vi.fn<() => void>(() => undefined);
    audio.dispatchEvent(new Event("loadedmetadata"));

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      durationMs: 1000,
      hidden: true,
      htmlAudioReadinessState: "ready",
    });
    expect(playButton.disabled).toBe(false);

    playButton.click();
    await Promise.resolve();

    expect(audio.play).toHaveBeenCalledTimes(1);
    expect(window.__aqePendingPlaybackRequest).toBeNull();
    expect(bridgeCommands()).not.toContain("aqe:play");
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackEngine: "html",
      playbackState: "playing",
    });
  });

  it("starts HTML playback from an explicit selected region", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 400);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    setFullGraphViewport();
    dragGraphSelection(svg, 0.25, 0.75);
    const audio = document.querySelector<HTMLAudioElement>('[data-testid="aqe-audio-clock-0"]')!;
    Object.defineProperty(audio, "readyState", { configurable: true, value: 1 });
    audio.play = vi.fn<() => Promise<void>>(() => Promise.resolve());
    audio.pause = vi.fn<() => void>(() => undefined);
    audio.dispatchEvent(new Event("loadedmetadata"));

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();

    expect(audio.play).toHaveBeenCalledTimes(1);
    expect(window.__aqePendingPlaybackRequest).toBeNull();
    expect(bridgeCommands()).not.toContain("aqe:play");
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

  it("stops and warns without backend fallback when HTML play rejects", async () => {
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

    expect(bridgeCommands()).not.toContain("aqe:play");
    expect(window.__aqeLastPlaybackRequest).toBeNull();
    expect(document.querySelector('[data-testid="aqe-status-0"]')).toHaveTextContent(
      "Browser audio is unavailable.",
    );
    expect(window.__aqeGraphStateForTest?.(0)?.playbackState).toBe("stopped");
  });

  it("fails immediately when source audio readiness is already failed before play", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    const audio = document.querySelector<HTMLAudioElement>('[data-testid="aqe-audio-clock-0"]')!;
    audio.pause = vi.fn<() => void>(() => undefined);
    audio.dispatchEvent(new Event("error"));

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();
    await Promise.resolve();

    expect(bridgeCommands()).not.toContain("aqe:play");
    expect(document.querySelector('[data-testid="aqe-status-0"]')).toHaveTextContent(
      "Browser audio is unavailable.",
    );
    expect(window.__aqeGraphStateForTest?.(0)?.playbackState).toBe("stopped");
  });

  it("starts a same-source loading HTML session once graph duration is known", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 0);
    const visualizer = document.querySelector('[data-testid="aqe-graph-0"]') as Parameters<typeof startSourcePlayback>[0];
    const audio = document.querySelector<HTMLAudioElement>('[data-testid="aqe-audio-clock-0"]')!;
    Object.defineProperty(audio, "readyState", { configurable: true, value: 0 });
    let resolvePlay!: () => void;
    audio.play = vi.fn<() => Promise<void>>(() => new Promise((resolve) => {
      resolvePlay = resolve;
    }));
    audio.pause = vi.fn<() => void>(() => undefined);
    dispatchHtmlAudioSessionEvent(0, {
      cursorMs: 0,
      source: { kind: "source", sourceFilename: "clip one.mp3" },
      type: "SourceConfigured",
    });

    expect(startSourcePlayback(visualizer, {
      action: "start",
      cursorMs: 0,
      endMs: 1000,
      engine: "html",
      loop: false,
      ord: 0,
      regionMode: "full",
    })).toBe(true);
    await Promise.resolve();
    await Promise.resolve();

    expect(audio.play).toHaveBeenCalledTimes(1);
    expect(window.__aqePendingPlaybackRequest).toBeNull();
    resolvePlay();
    await Promise.resolve();
    await Promise.resolve();

    expect(window.__aqePendingPlaybackRequest).toBeNull();
    expect(bridgeCommands()).not.toContain("aqe:play");
  });

  it("keeps selected playback state without backend fallback when HTML one-shot play rejects", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 700);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    setFullGraphViewport();
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
    expect(window.__aqeLastPlaybackRequest).toBeNull();
    expect(document.querySelector('[data-testid="aqe-status-0"]')).toHaveTextContent(
      "Browser audio is unavailable.",
    );
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "stopped",
      selectionStartMs: 250,
      selectionEndMs: 750,
      playbackRegionMode: "selection",
    });
  });

  it("warns without selected repeat fallback when HTML play rejects", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 700);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    setFullGraphViewport();
    dragGraphSelection(svg, 0.25, 0.75);
    await setRepeatMode(true);
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
      "Browser audio is unavailable.",
    );
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "stopped",
      repeatEnabled: true,
    });
  });

});
