import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  disposeEditorRuntime,
  initializeEditorRuntime,
  scan,
} from "../src/editor-inline/runtime.js";
import {
  bridgeCommands,
  muteConsole,
  peekPendingCommandPayload,
  renderFields,
  track,
} from "./editor-inline.integration.helpers.js";
import { invalidateFieldState } from "../src/editor-inline/field-state-store.js";
import { PRODUCT_LINKS } from "../src/lib/product-links.js";
import { EditorButtonMode } from "../src/lib/types.js";
import type { EditorRuntimeConfig } from "../src/editor-inline/types.js";

function recordingConfig(): EditorRuntimeConfig {
  return {
    audioFieldIndices: [0],
    splitButtonDefaults: {
      denoiseAlgorithm: "standard" as const,
      pauseAggressiveness: "normal" as const,
      repeatPauseSeconds: 0,
      speedStep: 1.5,
      voiceRecordingCountdownSeconds: 0,
      volumeStepDb: 15,
    },
    visibleEditorButtons: [
      "aqe:analyze",
      "aqe:record-voice",
      "aqe:play-recording",
    ],
  };
}

function recordingConfigWithCountdown(seconds: number): EditorRuntimeConfig {
  const config = recordingConfig();
  return {
    ...config,
    splitButtonDefaults: {
      ...config.splitButtonDefaults!,
      voiceRecordingCountdownSeconds: seconds,
    },
  };
}

function textRecordingConfig(): EditorRuntimeConfig {
  return {
    ...recordingConfig(),
    editorButtonModes: {
      "aqe:play-recording": EditorButtonMode.Text,
      "aqe:record-voice": EditorButtonMode.Text,
    },
  };
}

function setScrollbarDimensions(ord = 0, clientWidth = 500): HTMLDivElement {
  const scroller = document.querySelector<HTMLDivElement>(`[data-testid="aqe-time-scrollbar-scroll-${ord}"]`)!;
  Object.defineProperty(scroller, "clientWidth", { configurable: true, value: clientWidth });
  scroller.getBoundingClientRect = () => ({
    bottom: 16,
    height: 16,
    left: 0,
    right: clientWidth,
    top: 0,
    width: clientWidth,
    x: 0,
    y: 0,
    toJSON: () => ({}),
  });
  return scroller;
}

describe("editor inline learner recording integration", () => {
  let restoreConsole: () => void;

  beforeEach(() => {
    restoreConsole = muteConsole();
    renderFields();
  });

  afterEach(() => {
    disposeEditorRuntime();
    delete window.__aqeSplitButtonStates;
    restoreConsole();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("hides learner recording controls unless they are configured visible", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    expect(document.querySelector('[data-testid="aqe-button-0-record-voice"]')).toBeNull();
    expect(document.querySelector('[data-testid="aqe-button-0-play-recording"]')).toBeNull();
    expect(document.querySelector('[data-testid="aqe-button-0-share-recording"]')).toBeNull();
    expect(document.querySelector('[data-testid="aqe-button-0-show-recording-file"]')).toBeNull();
  });

  it("expands partial learner recording visibility to the full group", () => {
    const config: EditorRuntimeConfig = {
      ...recordingConfig(),
      visibleEditorButtons: ["aqe:record-voice"],
    };

    initializeEditorRuntime(config);
    scan(config);

    const group = document.querySelector<HTMLElement>(".aqe-recording-group")!;
    expect(group).not.toBeNull();
    expect(group).toHaveClass("aqe-toolbar-panel");
    expect(group).toHaveAttribute("role", "group");
    expect(group).toHaveAttribute("aria-label", "Record / Play yours");
    expect(group).toHaveAttribute("data-aqe-toolbar-button-container", "true");
    const panelLabel = group.querySelector<HTMLElement>(".aqe-toolbar-panel-label");
    expect(panelLabel).toHaveTextContent("Record / Play yours");
    expect(panelLabel).toHaveAttribute(
      "data-aqe-tooltip-content",
      "Record your voice for the current graph, then play, share, or show your latest recording.",
    );
    expect(document.querySelector('[data-testid="aqe-button-0-record-voice"]')).not.toBeNull();
    expect(document.querySelector('[data-testid="aqe-button-0-play-recording"]')).not.toBeNull();
    expect(document.querySelector('[data-testid="aqe-button-0-share-recording"]')).not.toBeNull();
    expect(document.querySelector('[data-testid="aqe-button-0-show-recording-file"]')).not.toBeNull();
  });

  it("renders the opt-in grouped buttons and dispatches record after the configured countdown", async () => {
    initializeEditorRuntime(recordingConfig());
    scan(recordingConfig());

    const group = document.querySelector(".aqe-recording-group");
    const recordButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-record-voice"]')!;
    const playYoursButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play-recording"]')!;
    const shareYoursButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-share-recording"]')!;
    const showYoursButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-show-recording-file"]')!;
    expect(group).not.toBeNull();
    expect(group).toHaveClass("aqe-toolbar-panel");
    expect(group).toHaveAttribute("aria-label", "Record / Play yours");
    expect(group).toHaveAttribute("data-aqe-toolbar-button-container", "true");
    expect(group?.querySelector(".aqe-split-group")).not.toBeNull();
    expect(recordButton.classList.contains("aqe-icon-only")).toBe(true);
    expect(playYoursButton.classList.contains("aqe-icon-only")).toBe(true);
    expect(shareYoursButton.classList.contains("aqe-icon-only")).toBe(true);
    expect(showYoursButton.classList.contains("aqe-icon-only")).toBe(true);
    expect(document.querySelector('[data-testid="aqe-split-0-record-voice-menu"]')).not.toBeNull();
    expect(recordButton.disabled).toBe(true);
    expect(playYoursButton.disabled).toBe(true);
    expect(shareYoursButton.disabled).toBe(true);
    expect(showYoursButton.disabled).toBe(true);
    expect(recordButton.closest(".aqe-button-tooltip-target")).toHaveAttribute(
      "data-aqe-tooltip-content",
      "Record\nRecord your voice for this graph\n\nDraw the graph before recording your voice",
    );
    expect(playYoursButton.closest(".aqe-button-tooltip-target")).toHaveAttribute(
      "data-aqe-tooltip-content",
      "Play yours\nPlay your latest recording\n\nRecord your voice before playing it",
    );

    window.__aqeSetVisualizer?.(0, { ...track, sourceFilename: "clip one.mp3" }, 0);
    await Promise.resolve();
    document.querySelector<HTMLElement>('[data-testid="aqe-graph-0"]')!.dataset.cursorMs = "400";
    invalidateFieldState(0);
    expect(recordButton.disabled).toBe(false);
    expect(playYoursButton.disabled).toBe(true);
    expect(shareYoursButton.disabled).toBe(true);
    expect(showYoursButton.disabled).toBe(true);
    expect(recordButton.closest(".aqe-button-tooltip-target")).toHaveAttribute(
      "data-aqe-tooltip-content",
      "Record\nRecord your voice for this graph",
    );
    expect(playYoursButton.closest(".aqe-button-tooltip-target")).toHaveAttribute(
      "data-aqe-tooltip-content",
      "Play yours\nPlay your latest recording\n\nRecord your voice before playing it",
    );

    const menu = document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-record-voice-menu"]')!;
    menu.click();
    await Promise.resolve();
    const popover = document.querySelector<HTMLElement>('[data-testid="aqe-split-0-record-voice-popover"]')!;
    expect(popover.querySelector<HTMLAnchorElement>(".aqe-split-video-link")).toHaveAttribute(
      "href",
      PRODUCT_LINKS.editorVideos.recordVoice,
    );
    const countdown = document.querySelector<HTMLInputElement>('[data-testid="aqe-split-0-record-voice-value"]')!;
    countdown.value = "0";
    countdown.dispatchEvent(new Event("input", { bubbles: true }));

    recordButton.click();

    const overlay = document.querySelector<HTMLElement>('[data-testid="aqe-recording-countdown-overlay-0"]')!;
    expect(overlay).not.toBeNull();
    expect(overlay.hidden).toBe(true);
    expect(window.__aqeGraphStateForTest?.(0)?.learnerRecordingStatus).toBe("idle");
    expect(bridgeCommands()).toContain("focus:0");
    expect(bridgeCommands()).toContain("aqe:command-payload");
    expect(peekPendingCommandPayload()).toMatchObject({
      command: "aqe:record-voice",
      fieldOrd: 0,
      graphSettings: { smoothness: expect.any(String) },
      startCursorMs: 400,
    });
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      cursorMs: 400,
      learnerStartCursorMs: 400,
    });
  });

  it("shows a graph overlay while a positive recording countdown runs", async () => {
    vi.useFakeTimers();
    const config = recordingConfigWithCountdown(3);
    initializeEditorRuntime(config);
    scan(config);
    window.__aqeSetVisualizer?.(0, { ...track, sourceFilename: "clip one.mp3" }, 0);
    await Promise.resolve();

    const recordButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-record-voice"]')!;
    recordButton.click();

    let overlay = document.querySelector<HTMLElement>('[data-testid="aqe-recording-countdown-overlay-0"]')!;
    expect(overlay).not.toBeNull();
    expect(overlay.hidden).toBe(false);
    expect(overlay).toHaveTextContent("3");
    expect(overlay).toHaveAttribute("aria-label", "Recording starts in 3s");
    expect(bridgeCommands()).not.toContain("aqe:command-payload");

    await vi.advanceTimersByTimeAsync(1000);
    await Promise.resolve();
    overlay = document.querySelector<HTMLElement>('[data-testid="aqe-recording-countdown-overlay-0"]')!;
    expect(overlay).toHaveTextContent("2");
    expect(overlay).toHaveAttribute("aria-label", "Recording starts in 2s");

    await vi.advanceTimersByTimeAsync(1000);
    await Promise.resolve();
    overlay = document.querySelector<HTMLElement>('[data-testid="aqe-recording-countdown-overlay-0"]')!;
    expect(overlay).toHaveTextContent("1");
    expect(overlay).toHaveAttribute("aria-label", "Recording starts in 1s");

    await vi.advanceTimersByTimeAsync(1000);
    await Promise.resolve();
    overlay = document.querySelector<HTMLElement>('[data-testid="aqe-recording-countdown-overlay-0"]')!;
    expect(overlay.hidden).toBe(true);
    expect(bridgeCommands()).toContain("focus:0");
    expect(bridgeCommands()).toContain("aqe:command-payload");
    expect(peekPendingCommandPayload()).toMatchObject({
      command: "aqe:record-voice",
      fieldOrd: 0,
    });
  });

  it("renders the recording group in text mode when configured", () => {
    initializeEditorRuntime(textRecordingConfig());
    scan(textRecordingConfig());

    const recordButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-record-voice"]')!;
    const playYoursButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play-recording"]')!;
    const shareYoursButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-share-recording"]')!;
    const showYoursButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-show-recording-file"]')!;
    expect(recordButton.classList.contains("aqe-icon-only")).toBe(false);
    expect(playYoursButton.classList.contains("aqe-icon-only")).toBe(false);
    expect(shareYoursButton.classList.contains("aqe-icon-only")).toBe(true);
    expect(showYoursButton.classList.contains("aqe-icon-only")).toBe(true);
    expect(recordButton.textContent).toContain("Record");
    expect(playYoursButton.textContent).toContain("Play yours");
  });

  it("toggles Record to Stop while recording and enables Play yours only when ready", async () => {
    initializeEditorRuntime(recordingConfig());
    scan(recordingConfig());
    window.__aqeSetVisualizer?.(0, { ...track, sourceFilename: "clip one.mp3" }, 0);
    await Promise.resolve();

    const recordButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-record-voice"]')!;
    const playYoursButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play-recording"]')!;
    const shareYoursButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-share-recording"]')!;
    const showYoursButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-show-recording-file"]')!;

    window.__aqeSetLearnerRecordingState?.({
      fieldOrd: 0,
      generation: 1,
      status: "recording",
      targetDurationMs: track.durationMs,
    });

    expect(recordButton.dataset.aqeButtonState).toBe("recording");
    expect(recordButton.getAttribute("aria-label")).toBe("Stop\nStop recording your voice");
    expect(recordButton.disabled).toBe(false);
    expect(playYoursButton.disabled).toBe(true);
    expect(shareYoursButton.disabled).toBe(true);
    expect(showYoursButton.disabled).toBe(true);

    recordButton.click();
    expect(bridgeCommands()).toContain("aqe:stop-recording");

    window.__aqeSetLearnerRecordingState?.({
      fieldOrd: 0,
      generation: 1,
      mediaFilename: "target__aqe_voice.wav",
      playbackStatus: "stopped",
      status: "ready",
      targetDurationMs: track.durationMs,
    });
    expect(playYoursButton.disabled).toBe(false);
    expect(shareYoursButton.disabled).toBe(false);
    expect(showYoursButton.disabled).toBe(false);

    playYoursButton.click();
    expect(bridgeCommands()).toContain("aqe:play-recording");

    window.__aqeSetLearnerRecordingState?.({
      fieldOrd: 0,
      generation: 1,
      mediaFilename: "target__aqe_voice.wav",
      playbackStatus: "playing",
      status: "ready",
      targetDurationMs: track.durationMs,
    });
    expect(playYoursButton.dataset.aqeButtonState).toBe("pause");
    expect(playYoursButton.textContent).toContain("Pause yours");

    window.__aqeSetLearnerRecordingState?.({
      fieldOrd: 0,
      generation: 1,
      mediaFilename: "target__aqe_voice.wav",
      playbackStatus: "stopped",
      status: "ready",
      targetDurationMs: track.durationMs,
    });
    expect(playYoursButton.dataset.aqeButtonState).toBe("default");
    expect(playYoursButton.textContent).toContain("Play yours");

    showYoursButton.click();
    expect(peekPendingCommandPayload()).toMatchObject({
      command: "aqe:show-recording-file",
      fieldOrd: 0,
    });

    shareYoursButton.click();
    expect(peekPendingCommandPayload()).toMatchObject({
      command: "aqe:share-recording",
      fieldOrd: 0,
      shareTarget: "litterbox",
    });
  });

  it("grows the active recording graph and reveals the time scrollbar once recording exceeds the target graph", async () => {
    initializeEditorRuntime(recordingConfig());
    scan(recordingConfig());
    window.__aqeSetVisualizer?.(0, { ...track, sourceFilename: "clip one.mp3" }, 0);
    await Promise.resolve();
    const initialScrollbar = document.querySelector<HTMLElement>('[data-testid="aqe-time-scrollbar-0"]')!;
    expect(initialScrollbar.hidden).toBe(true);
    setScrollbarDimensions();

    window.__aqeSetLearnerRecordingState?.({
      fieldOrd: 0,
      generation: 1,
      recordingDurationMs: 400,
      startCursorMs: 900,
      status: "recording",
      targetDurationMs: track.durationMs,
    });
    await Promise.resolve();

    const scrollbar = document.querySelector<HTMLElement>('[data-testid="aqe-time-scrollbar-0"]')!;
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      durationMs: 1300,
      learnerDurationMs: 1300,
      learnerRecordingStatus: "recording",
      targetDurationMs: 1000,
    });
    await vi.waitFor(() => {
      expect(scrollbar.hidden).toBe(false);
    });
  });

  it("follows the recording cursor after recording growth makes the graph horizontally scrollable", async () => {
    const frames: Array<(time: number) => void> = [];
    vi.spyOn(window, "requestAnimationFrame").mockImplementation((callback) => {
      frames.push(callback);
      return frames.length;
    });
    vi.spyOn(window, "cancelAnimationFrame").mockImplementation(() => undefined);
    let now = 1000;
    vi.spyOn(performance, "now").mockImplementation(() => now);

    initializeEditorRuntime(recordingConfig());
    scan(recordingConfig());
    window.__aqeSetVisualizer?.(0, { ...track, sourceFilename: "clip one.mp3" }, 0);
    await Promise.resolve();
    const scroller = setScrollbarDimensions();

    window.__aqeSetLearnerRecordingState?.({
      fieldOrd: 0,
      generation: 1,
      startCursorMs: 900,
      status: "recording",
      targetDurationMs: track.durationMs,
    });
    await Promise.resolve();

    now = 1250;
    frames.shift()?.(now);
    await Promise.resolve();
    await Promise.resolve();

    const scrollbar = document.querySelector<HTMLElement>('[data-testid="aqe-time-scrollbar-0"]')!;
    const state = window.__aqeGraphStateForTest?.(0);
    expect(state?.durationMs).toBeGreaterThan(1000);
    expect(state?.cursorMs).toBeGreaterThan(1000);
    expect(state?.viewportStartMs).toBeGreaterThan(0);
    await vi.waitFor(() => {
      expect(scrollbar.hidden).toBe(false);
      expect(scroller.scrollLeft).toBeGreaterThan(0);
    });
  });

  it("renders learner pitch only, expands graph duration, and keeps target playback constrained", async () => {
    initializeEditorRuntime(recordingConfig());
    scan(recordingConfig());
    window.__aqeSetVisualizer?.(0, { ...track, sourceFilename: "clip one.mp3" }, 0);
    await Promise.resolve();

    window.__aqeSetLearnerRecordingState?.({
      fieldOrd: 0,
      generation: 1,
      startCursorMs: 400,
      status: "ready",
      targetDurationMs: track.durationMs,
    });
    window.__aqeSetLearnerVisualizer?.(0, {
      ...track,
      durationMs: 1500,
      pitchMaxHz: 500,
      pitchMinHz: 80,
      points: [
        [0, 130, 1, true],
        [600, 210, 0.2, true],
        [1500, 260, 0.1, true],
      ],
      sourceFilename: "target__aqe_voice.wav",
    });

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      durationMs: 1900,
      targetDurationMs: 1000,
      learnerDurationMs: 1900,
      learnerIntensityPaths: 0,
      learnerPitchPaths: 1,
      learnerStartCursorMs: 400,
      playbackEndMs: 1000,
    });
    expect(window.__aqeGraphStateForTest?.(0)?.intensity).not.toBe("");

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-graph"]')!.click();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      learnerDurationMs: 0,
      learnerPitchPaths: 0,
      learnerPlaybackStatus: "stopped",
      learnerRecordingStatus: "idle",
      learnerStartCursorMs: 0,
    });
    window.__aqePopPendingGraphAnalysisRequest?.();
  });
});
