import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import {
  bridgeCommands,
  muteConsole,
  prepareHtmlAudio,
  renderFields,
  setRepeatMode,
} from "./editor-inline.integration.helpers.js";

describe("editor inline post-edit playback integration", () => {
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
      engine: "native",
      loop: false,
      ord: 0,
      regionMode: "full",
    });
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackEngine: "native",
      playbackState: "stopped",
      repeatEnabled: false,
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

    window.__aqeSetBusy?.(0, false);

    expect(window.__aqePlayAfterEdit?.(0)).toBe(true);
    expect(window.__aqePostEditPlaybackIntents?.[0]).toBeUndefined();
    expect(bridgeCommands()).toContain("aqe:play");
  });

  it("cancels pending post-edit autoplay when a history command is sent", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-volume-up"]')!.click();
    expect(window.__aqePostEditPlaybackIntents?.[0]).toBeDefined();
    window.__aqeSetBusy?.(0, false);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-redo"]')!.click();

    expect(window.__aqePostEditPlaybackIntents?.[0]).toBeUndefined();
    expect(bridgeCommands()).toContain("aqe:redo");
    window.__aqePendingPlaybackRequest = null;
    window.__aqeLastPlaybackRequest = null;

    expect(window.__aqePlayAfterEdit?.(0)).toBe(true);
    expect(window.__aqeLastPlaybackRequest).toBeNull();
  });
});
