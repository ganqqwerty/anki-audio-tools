import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import {
  bridgeCommands,
  clearQueuedAnimationFrames,
  dragGraphSelection,
  mockAnimationFrames,
  muteConsole,
  prepareHtmlAudio,
  renderFields,
  setRepeatMode,
  setGraphBounds,
  track,
} from "./editor-inline.integration.helpers.js";

function repeatPauseConfig(seconds: number) {
  return {
    audioFieldIndices: [0],
    splitButtonDefaults: {
      denoiseAlgorithm: "standard" as const,
      pauseAggressiveness: "normal" as const,
      repeatPauseSeconds: seconds,
      speedStep: 1.5,
      volumeStepDb: 15,
    },
  };
}

async function startSelectedRepeatWithPause(seconds: number) {
  vi.useFakeTimers();
  const frames = mockAnimationFrames();
  const config = repeatPauseConfig(seconds);
  initializeEditorRuntime(config);
  scan(config);
  await Promise.resolve();
  window.__aqeSetVisualizer?.(0, track, 100);
  const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
  setGraphBounds(svg);
  dragGraphSelection(svg, 0.25, 0.75);
  await setRepeatMode(true);
  clearQueuedAnimationFrames(frames);
  const audio = prepareHtmlAudio();

  document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
  await Promise.resolve();
  audio.currentTime = 0.76;
  frames.shift()?.(performance.now() + 800);
  return { audio };
}

function graphCountdownOverlay(): HTMLElement {
  return document.querySelector<HTMLElement>('[data-testid="aqe-recording-countdown-overlay-0"]')!;
}

describe("editor inline selected repeat pause integration", () => {
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

  it("waits for the configured repeat pause before the next HTML loop pass", async () => {
    const { audio } = await startSelectedRepeatWithPause(2);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "playing",
      progressClockMode: "stopped",
      repeatPauseSeconds: 2,
      repeatPauseWaiting: true,
      cursorMs: 250,
    });
    expect(audio.pause).toHaveBeenCalled();
    expect(audio.play).toHaveBeenCalledTimes(1);
    expect(graphCountdownOverlay().hidden).toBe(false);
    expect(graphCountdownOverlay()).toHaveTextContent("2");
    expect(graphCountdownOverlay()).toHaveAttribute("aria-label", "Repeating in 2s");

    await vi.advanceTimersByTimeAsync(1000);
    expect(graphCountdownOverlay()).toHaveTextContent("1");
    expect(graphCountdownOverlay()).toHaveAttribute("aria-label", "Repeating in 1s");
    await vi.advanceTimersByTimeAsync(999);
    expect(audio.play).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(1);

    expect(audio.play).toHaveBeenCalledTimes(2);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "playing",
      progressClockMode: "audio",
      repeatPauseWaiting: false,
      cursorMs: 250,
    });
    expect(graphCountdownOverlay().hidden).toBe(true);
    expect(bridgeCommands()).not.toContain("aqe:play-ended");
  });

  it("cancels a pending repeat pause when playback is paused", async () => {
    const { audio } = await startSelectedRepeatWithPause(1);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    expect(graphCountdownOverlay().hidden).toBe(true);
    await vi.advanceTimersByTimeAsync(1000);

    expect(audio.play).toHaveBeenCalledTimes(1);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "paused",
      repeatPauseWaiting: false,
      cursorMs: 250,
    });
  });

  it("completes playback when repeat is disabled during the repeat pause", async () => {
    const { audio } = await startSelectedRepeatWithPause(1);

    await setRepeatMode(false);
    expect(graphCountdownOverlay().hidden).toBe(true);
    await vi.advanceTimersByTimeAsync(1000);

    expect(audio.play).toHaveBeenCalledTimes(1);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "stopped",
      repeatEnabled: false,
      repeatPauseWaiting: false,
      cursorMs: 250,
    });
    expect(bridgeCommands()).toContain("aqe:play-ended");
  });
});
