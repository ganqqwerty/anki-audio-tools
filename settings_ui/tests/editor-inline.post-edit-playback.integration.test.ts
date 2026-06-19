import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { setEditorRuntimeConfig } from "../src/editor-inline/editor-runtime-config.js";
import { notifyPostEditPlaybackReady } from "../src/editor-inline/post-edit-playback.js";
import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import {
  bridgeCommands,
  consumePendingCommandPayload,
  muteConsole,
  prepareHtmlAudio,
  renderFields,
  setRepeatMode,
  track,
} from "./editor-inline.integration.helpers.js";

describe("editor inline post-edit playback integration", () => {
  let restoreConsole: () => void;

  beforeEach(() => {
    restoreConsole = muteConsole();
    consumePendingCommandPayload();
    renderFields();
  });

  afterEach(() => {
    disposeEditorRuntime();
    restoreConsole();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("autoplays after processing commands with the captured repeat flag", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    await setRepeatMode(true);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-volume-up"]')!.click();

    expect(window.__aqePostEditPlaybackIntents?.[0]).toMatchObject({ repeat: true });

    disposeEditorRuntime();
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    const audio = prepareHtmlAudio(0);
    Object.defineProperty(audio, "duration", { configurable: true, value: 1 });
    audio.dispatchEvent(new Event("loadedmetadata"));

    expect(window.__aqePlayAfterEdit?.(0)).toBe(true);
    await Promise.resolve();

    expect(window.__aqeGetPlaybackRequest?.()).toEqual({
      action: "start",
      cursorMs: 0,
      endMs: 1000,
      engine: "html",
      loop: true,
      ord: 0,
      regionMode: "full",
      source: "post_edit",
    });
    expect(window.__aqePostEditPlaybackIntents?.[0]).toBeUndefined();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "playing",
      repeatEnabled: true,
    });
  });

  it("does not repeat post-edit autoplay when repeat was turned off", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0], repeatPlaybackByDefault: true });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    await setRepeatMode(false);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-volume-up"]')!.click();

    expect(window.__aqePostEditPlaybackIntents?.[0]).toMatchObject({ repeat: false });

    disposeEditorRuntime();
    initializeEditorRuntime({ audioFieldIndices: [0], repeatPlaybackByDefault: true });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    const audio = prepareHtmlAudio(0);
    Object.defineProperty(audio, "duration", { configurable: true, value: 1 });
    audio.dispatchEvent(new Event("loadedmetadata"));

    expect(window.__aqePlayAfterEdit?.(0)).toBe(true);
    await Promise.resolve();

    expect(window.__aqeGetPlaybackRequest?.()).toMatchObject({
      engine: "html",
      loop: false,
      ord: 0,
      regionMode: "full",
    });
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackEngine: "html",
      playbackState: "playing",
      repeatEnabled: false,
    });
  });

  it("preserves the edit status when post-edit browser playback rejects", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetBusy?.(0, false, "Increased speed to x1.5.", "aqe:faster");
    const audio = prepareHtmlAudio(0);
    Object.defineProperty(audio, "duration", { configurable: true, value: 1 });
    audio.play = vi.fn<() => Promise<void>>(() => Promise.reject(new Error("blocked")));
    audio.dispatchEvent(new Event("loadedmetadata"));

    expect(window.__aqePlayAfterEdit?.(0)).toBe(true);
    await Promise.resolve();
    await Promise.resolve();

    expect(window.__aqePendingPlaybackRequest).toBeNull();
    expect(bridgeCommands()).not.toContain("aqe:play");
    expect(document.querySelector('[data-testid="aqe-status-0"]')).toHaveTextContent(
      "Increased speed to x1.5.",
    );
    const playbackWarning = document.querySelector('[data-testid="aqe-playback-warning-0"]');
    expect(playbackWarning).toHaveTextContent("Browser audio is unavailable.");
    expect(playbackWarning).not.toHaveAttribute("hidden");
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackEngine: "html",
      playbackState: "stopped",
    });
  });

  it("waits while another edit is busy before consuming post-edit playback", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-volume-up"]')!.click();
    window.__aqeSetBusy?.(0, true, "Processing");

    expect(window.__aqePlayAfterEdit?.(0)).toBe(false);

    expect(window.__aqePostEditPlaybackIntents?.[0]).toBeDefined();
    expect(bridgeCommands()).not.toContain("aqe:play");

    const audio = document.querySelector<HTMLAudioElement>('[data-testid="aqe-audio-clock-0"]')!;
    Object.defineProperty(audio, "duration", { configurable: true, value: 1 });
    prepareHtmlAudio(0);
    window.__aqeSetBusy?.(0, false);

    expect(window.__aqePlayAfterEdit?.(0)).toBe(true);
    await Promise.resolve();
    await Promise.resolve();
    expect(window.__aqePostEditPlaybackIntents?.[0]).toBeUndefined();
    expect(bridgeCommands()).toContain("aqe:play");
  });

  it("notifies Python when a pending post-edit playback field is mounted", async () => {
    initializeEditorRuntime({
      audioFieldIndices: [0],
      pendingPostEditPlayback: {
        fieldOrd: 0,
        generation: 3,
        sourceFilename: "clip one.mp3",
      },
    });
    scan(window.__AQE_EDITOR_CONFIG__!);
    await Promise.resolve();

    expect(consumePendingCommandPayload()).toBeNull();
    expect(bridgeCommands()).not.toContain("aqe:command-payload");

    prepareHtmlAudio(0);
    await Promise.resolve();

    expect(consumePendingCommandPayload()).toEqual({
      command: "aqe:post-edit-playback-ready",
      fieldOrd: 0,
      generation: 3,
      sourceFilename: "clip one.mp3",
    });
    expect(bridgeCommands()).toContain("aqe:command-payload");
  });

  it("suppresses duplicate ready notifications for the same post-edit generation", async () => {
    initializeEditorRuntime({
      audioFieldIndices: [0],
      pendingPostEditPlayback: {
        fieldOrd: 0,
        generation: 12,
        sourceFilename: "clip one.mp3",
      },
    });
    scan(window.__AQE_EDITOR_CONFIG__!);
    await Promise.resolve();

    prepareHtmlAudio(0);
    await Promise.resolve();

    expect(consumePendingCommandPayload()).toEqual({
      command: "aqe:post-edit-playback-ready",
      fieldOrd: 0,
      generation: 12,
      sourceFilename: "clip one.mp3",
    });

    notifyPostEditPlaybackReady(0, "clip one.mp3");
    await Promise.resolve();

    expect(consumePendingCommandPayload()).toBeNull();
    expect(bridgeCommands().filter((command) => command === "aqe:command-payload")).toHaveLength(1);
  });

  it("defers the post-edit ready notification until controls are not busy", async () => {
    initializeEditorRuntime({
      audioFieldIndices: [0],
      pendingPostEditPlayback: {
        fieldOrd: 0,
        generation: 4,
        sourceFilename: "clip one.mp3",
      },
    });
    window.__aqeSetBusy?.(0, true);
    scan(window.__AQE_EDITOR_CONFIG__!);
    await Promise.resolve();

    expect(consumePendingCommandPayload()).toBeNull();
    expect(bridgeCommands()).not.toContain("aqe:command-payload");

    prepareHtmlAudio(0);
    window.__aqeSetBusy?.(0, false);
    await Promise.resolve();

    expect(consumePendingCommandPayload()).toEqual({
      command: "aqe:post-edit-playback-ready",
      fieldOrd: 0,
      generation: 4,
      sourceFilename: "clip one.mp3",
    });
    expect(bridgeCommands()).toContain("aqe:command-payload");
  });

  it("defers the post-edit ready notification until a pending graph redraw finishes", async () => {
    initializeEditorRuntime({
      audioFieldIndices: [0],
      pendingPostEditPlayback: {
        fieldOrd: 0,
        generation: 5,
        requireGraphRedraw: true,
        sourceFilename: "clip one.mp3",
      },
    });
    scan(window.__AQE_EDITOR_CONFIG__!);
    await Promise.resolve();

    expect(consumePendingCommandPayload()).toBeNull();
    expect(bridgeCommands()).not.toContain("aqe:command-payload");

    window.__aqeSetVisualizer?.(0, track, 0);
    prepareHtmlAudio(0);
    await Promise.resolve();

    expect(consumePendingCommandPayload()).toEqual({
      command: "aqe:post-edit-playback-ready",
      fieldOrd: 0,
      generation: 5,
      sourceFilename: "clip one.mp3",
    });
    expect(bridgeCommands()).toContain("aqe:command-payload");
  });

  it("keeps post-edit playback deferred while learner pitch is preserved during graph redraw", async () => {
    initializeEditorRuntime({
      audioFieldIndices: [0],
      pendingPostEditPlayback: {
        fieldOrd: 0,
        generation: 7,
        requireGraphRedraw: true,
        sourceFilename: "updated.mp3",
      },
    });
    scan(window.__AQE_EDITOR_CONFIG__!);
    window.__aqeSetVisualizer?.(0, track, 0);
    window.__aqeSetLearnerVisualizer?.(0, {
      ...track,
      sourceFilename: "learner.wav",
    });

    expect(window.__aqeResetGraphAfterEdit?.(0, "updated.mp3", true)).toBe(false);

    document.getElementById("f0")!.innerHTML = "[sound:updated.mp3]";
    scan({
      ...window.__AQE_EDITOR_CONFIG__!,
      audioFieldSources: { 0: "updated.mp3" },
    });
    await Promise.resolve();

    expect(window.__aqeGraphStateForTest?.(0)?.learnerPitchPaths).toBeGreaterThan(0);
    expect(consumePendingCommandPayload()).toBeNull();
    expect(bridgeCommands()).not.toContain("aqe:command-payload");

    window.__aqeSetVisualizer?.(0, { ...track, sourceFilename: "updated.mp3" }, 0);
    prepareHtmlAudio(0);
    await Promise.resolve();

    expect(consumePendingCommandPayload()).toEqual({
      command: "aqe:post-edit-playback-ready",
      fieldOrd: 0,
      generation: 7,
      sourceFilename: "updated.mp3",
    });
    expect(window.__aqeGraphStateForTest?.(0)?.learnerPitchPaths).toBeGreaterThan(0);
    expect(bridgeCommands()).toContain("aqe:command-payload");
  });

  it("does not require a new redraw when the matching post-edit graph is already rendered", async () => {
    initializeEditorRuntime({
      audioFieldIndices: [0],
      pendingPostEditPlayback: {
        fieldOrd: 0,
        generation: 6,
        requireGraphRedraw: true,
        sourceFilename: "clip one.mp3",
      },
    });
    scan(window.__AQE_EDITOR_CONFIG__!);
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 0);
    prepareHtmlAudio(0);

    window.__aqeSetBusy?.(0, false);
    await Promise.resolve();

    expect(consumePendingCommandPayload()).toEqual({
      command: "aqe:post-edit-playback-ready",
      fieldOrd: 0,
      generation: 6,
      sourceFilename: "clip one.mp3",
    });
    expect(bridgeCommands()).toContain("aqe:command-payload");
  });

  it("defers post-edit ready notification until browser audio metadata loads", async () => {
    initializeEditorRuntime({
      audioFieldIndices: [0],
      pendingPostEditPlayback: {
        fieldOrd: 0,
        generation: 8,
        sourceFilename: "clip one.mp3",
      },
    });
    scan(window.__AQE_EDITOR_CONFIG__!);
    await Promise.resolve();

    expect(consumePendingCommandPayload()).toBeNull();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      htmlAudioReadinessState: "loading_metadata",
    });

    prepareHtmlAudio(0);
    await Promise.resolve();

    expect(consumePendingCommandPayload()).toEqual({
      command: "aqe:post-edit-playback-ready",
      fieldOrd: 0,
      generation: 8,
      sourceFilename: "clip one.mp3",
    });
  });

  it("requests a rendered graph for the generated source while browser metadata is still loading", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan(window.__AQE_EDITOR_CONFIG__!);
    window.__aqeSetVisualizer?.(0, track, 0);
    document.getElementById("f0")!.innerHTML = "[sound:updated__aqe_123.mp3]";
    const config = {
      ...window.__AQE_EDITOR_CONFIG__!,
      audioFieldSources: { 0: "updated__aqe_123.mp3" },
      pendingPostEditPlayback: {
        fieldOrd: 0,
        generation: 11,
        sourceFilename: "updated__aqe_123.mp3",
      },
    };
    setEditorRuntimeConfig(config);
    scan(config);
    notifyPostEditPlaybackReady(0, "updated__aqe_123.mp3");
    await Promise.resolve();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      busy: true,
    });
    expect(window.__aqePopPendingGraphAnalysisRequest?.()).toEqual({
      graphSettings: {
        connectShortDropoutsMs: 240,
        recordingCondition: "auto",
        smoothness: "very_smooth",
        voiceLock: "balanced",
        voiceRange: "general",
      },
      ord: 0,
      sourceFilename: "updated__aqe_123.mp3",
    });
    expect(consumePendingCommandPayload()).toBeNull();
  });

  it("notifies post-edit ready from the rendered graph while browser metadata is still loading", async () => {
    initializeEditorRuntime({
      audioFieldIndices: [0],
      pendingPostEditPlayback: {
        fieldOrd: 0,
        generation: 10,
        requireGraphRedraw: true,
        sourceFilename: "updated.mp3",
      },
    });
    scan(window.__AQE_EDITOR_CONFIG__!);
    await Promise.resolve();

    window.__aqeSetVisualizer?.(0, { ...track, sourceFilename: "updated.mp3" }, 0);
    await Promise.resolve();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      htmlAudioReadinessState: "loading_metadata",
      sourceFilename: "updated.mp3",
    });
    expect(consumePendingCommandPayload()).toEqual({
      command: "aqe:post-edit-playback-ready",
      fieldOrd: 0,
      generation: 10,
      sourceFilename: "updated.mp3",
    });
  });

  it("starts post-edit HTML playback from the rendered graph while browser metadata is still loading", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, { ...track, sourceFilename: "updated.mp3" }, 0);
    const audio = document.querySelector<HTMLAudioElement>('[data-testid="aqe-audio-clock-0"]')!;
    Object.defineProperty(audio, "readyState", { configurable: true, value: 0 });
    audio.play = vi.fn<() => Promise<void>>(() => Promise.resolve());
    audio.pause = vi.fn<() => void>(() => undefined);

    expect(window.__aqePlayAfterEdit?.(0)).toBe(true);
    await Promise.resolve();
    await Promise.resolve();

    expect(audio.play).toHaveBeenCalledTimes(1);
    expect(window.__aqePendingPlaybackRequest).toEqual({
      action: "start",
      cursorMs: 0,
      endMs: 1000,
      engine: "html",
      loop: false,
      ord: 0,
      regionMode: "selection",
      source: "post_edit",
    });
    expect(document.querySelector('[data-testid="aqe-playback-warning-0"]')).toHaveAttribute("hidden");
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackEngine: "html",
      playbackState: "playing",
      sourceFilename: "updated.mp3",
    });
  });

});
