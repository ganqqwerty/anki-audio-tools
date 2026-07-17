import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  clearAllHtmlAudioSessions,
  readHtmlAudioSessionState,
} from "../src/editor-inline/html-audio-session-controller.js";
import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import {
  bridgeCommands,
  clearQueuedAnimationFrames,
  mockAnimationFrames,
  prepareHtmlAudio,
  renderFields,
  setRepeatMode,
  track,
} from "./editor-inline.integration.helpers.js";

describe("editor inline HTML audio repeat boundary", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.spyOn(HTMLMediaElement.prototype, "load").mockImplementation(() => undefined);
    vi.spyOn(HTMLMediaElement.prototype, "pause").mockImplementation(() => undefined);
    renderFields();
  });

  afterEach(() => {
    disposeEditorRuntime();
    clearAllHtmlAudioSessions();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("routes source audio ended through the session boundary before the RAF boundary", async () => {
    const frames = mockAnimationFrames();
    const config = {
      audioFieldIndices: [0],
      splitButtonDefaults: {
        denoiseAlgorithm: "standard" as const,
        pauseAggressiveness: "normal" as const,
        repeatPauseSeconds: 2,
        speedStep: 1.5,
        volumeStepDb: 15,
      },
    };
    initializeEditorRuntime(config);
    scan(config);
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 100);
    await setRepeatMode(true);
    clearQueuedAnimationFrames(frames);
    const audio = prepareHtmlAudio(0);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();
    await Promise.resolve();

    expect(readHtmlAudioSessionState(0)).toMatchObject({
      kind: "playing",
      source: { kind: "source", sourceFilename: "clip one.mp3" },
    });
    expect(frames.length).toBeGreaterThan(0);

    audio.dispatchEvent(new Event("ended"));

    expect(readHtmlAudioSessionState(0)).toMatchObject({
      cursorMs: 0,
      kind: "ready",
      source: { kind: "source", sourceFilename: "clip one.mp3" },
    });
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "playing",
      repeatPauseSeconds: 2,
      cursorMs: 0,
    });
    expect(audio.pause).toHaveBeenCalled();
    expect(audio.play).toHaveBeenCalledTimes(1);
    expect(bridgeCommands()).not.toContain("aqe:play-ended");

    await vi.advanceTimersByTimeAsync(2000);

    expect(audio.play).toHaveBeenCalledTimes(2);
  });
});
