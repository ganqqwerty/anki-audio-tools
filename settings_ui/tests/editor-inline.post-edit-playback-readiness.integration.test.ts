import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { setEditorRuntimeConfig } from "../src/editor-inline/editor-runtime-config.js";
import { notifyPostEditPlaybackReady } from "../src/editor-inline/post-edit-playback.js";
import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import type { EditorRuntimeConfig } from "../src/editor-inline/types.js";
import {
  bridgeCommands,
  consumePendingCommandPayload,
  muteConsole,
  prepareHtmlAudio,
  renderFields,
  track,
} from "./editor-inline.integration.helpers.js";

describe("editor inline post-edit playback readiness integration", () => {
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

  it("requests a rendered graph for the generated source while browser metadata is still loading", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan(window.__AQE_EDITOR_CONFIG__!);
    window.__aqeSetVisualizer?.(0, track, 0);
    document.getElementById("f0")!.innerHTML = "[sound:updated__aqe_123.mp3]";
    const config: EditorRuntimeConfig = {
      ...window.__AQE_EDITOR_CONFIG__!,
      audioFieldSources: { 0: "updated__aqe_123.mp3" },
      pendingPostEditPlayback: {
        fieldOrd: 0,
        generation: 11,
        sourceKind: "generated_edit",
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

  it("does not infer generated post-edit playback from the filename", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan(window.__AQE_EDITOR_CONFIG__!);
    window.__aqeSetVisualizer?.(0, track, 0);
    document.getElementById("f0")!.innerHTML = "[sound:restored__aqe_123.mp3]";
    const config: EditorRuntimeConfig = {
      ...window.__AQE_EDITOR_CONFIG__!,
      audioFieldSources: { 0: "restored__aqe_123.mp3" },
      pendingPostEditPlayback: {
        fieldOrd: 0,
        generation: 15,
        sourceKind: "existing_media",
        sourceFilename: "restored__aqe_123.mp3",
      },
    };
    setEditorRuntimeConfig(config);
    scan(config);
    notifyPostEditPlaybackReady(0, "restored__aqe_123.mp3");
    await Promise.resolve();

    expect(window.__aqePopPendingGraphAnalysisRequest?.()).toBeNull();
    expect(consumePendingCommandPayload()).toBeNull();
  });

  it("notifies post-edit ready from the rendered graph while browser metadata is still loading", async () => {
    initializeEditorRuntime({
      audioFieldIndices: [0],
      pendingPostEditPlayback: {
        fieldOrd: 0,
        generation: 10,
        sourceKind: "generated_edit",
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

  it("starts current source playback when pending post-edit source is stale", async () => {
    initializeEditorRuntime({
      audioFieldIndices: [0],
      pendingPostEditPlayback: {
        fieldOrd: 0,
        generation: 12,
        sourceKind: "generated_edit",
        requireGraphRedraw: true,
        sourceFilename: "stale-edit.mp3",
      },
    });
    scan(window.__AQE_EDITOR_CONFIG__!);
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, { ...track, sourceFilename: "current-edit.mp3" }, 0);
    const audio = prepareHtmlAudio(0);

    expect(window.__aqePlayAfterEdit?.(0)).toBe(true);
    await Promise.resolve();
    await Promise.resolve();

    expect(audio.play).toHaveBeenCalledTimes(1);
    expect(consumePendingCommandPayload()).toBeNull();
    expect(window.__aqeGetPlaybackRequest?.()).toEqual({
      action: "start",
      cursorMs: 0,
      endMs: 1000,
      engine: "html",
      loop: false,
      ord: 0,
      regionMode: "selection",
      source: "post_edit",
    });
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackEngine: "html",
      playbackState: "playing",
      sourceFilename: "current-edit.mp3",
    });
  });

  it("suppresses duplicate ready when session and legacy readiness both confirm", async () => {
    initializeEditorRuntime({
      audioFieldIndices: [0],
      pendingPostEditPlayback: {
        fieldOrd: 0,
        generation: 13,
        sourceKind: "generated_edit",
        requireGraphRedraw: true,
        sourceFilename: "updated.mp3",
      },
    });
    scan(window.__AQE_EDITOR_CONFIG__!);
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, { ...track, sourceFilename: "updated.mp3" }, 0);

    expect(window.__aqePlayAfterEdit?.(0)).toBe(true);
    await Promise.resolve();
    expect(consumePendingCommandPayload()).toEqual({
      command: "aqe:post-edit-playback-ready",
      fieldOrd: 0,
      generation: 13,
      sourceFilename: "updated.mp3",
    });

    notifyPostEditPlaybackReady(0, "updated.mp3");
    await Promise.resolve();

    expect(consumePendingCommandPayload()).toBeNull();
    expect(bridgeCommands().filter((command) => command === "aqe:command-payload")).toHaveLength(1);
  });

  it("clears session duplicate tracking for a new note", async () => {
    initializeEditorRuntime({
      audioFieldIndices: [0],
      pendingPostEditPlayback: {
        fieldOrd: 0,
        generation: 14,
        sourceKind: "generated_edit",
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
      generation: 14,
      sourceFilename: "clip one.mp3",
    });

    initializeEditorRuntime({
      audioFieldIndices: [0],
      pendingPostEditPlayback: {
        fieldOrd: 0,
        generation: 14,
        sourceKind: "generated_edit",
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
      generation: 14,
      sourceFilename: "clip one.mp3",
    });
  });
});
