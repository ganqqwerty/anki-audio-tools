import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  disposeEditorRuntime,
  initializeEditorRuntime,
  scan,
} from "../src/editor-inline/runtime.js";
import {
  bridgeCommands,
  muteConsole,
  renderFields,
  track,
} from "./editor-inline.integration.helpers.js";
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

function textRecordingConfig(): EditorRuntimeConfig {
  return {
    ...recordingConfig(),
    editorButtonModes: {
      "aqe:play-recording": EditorButtonMode.Text,
      "aqe:record-voice": EditorButtonMode.Text,
    },
  };
}

describe("editor inline learner recording integration", () => {
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

  it("hides learner recording controls unless they are configured visible", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    expect(document.querySelector('[data-testid="aqe-button-0-record-voice"]')).toBeNull();
    expect(document.querySelector('[data-testid="aqe-button-0-play-recording"]')).toBeNull();
  });

  it("renders the opt-in grouped buttons and dispatches record after the configured countdown", async () => {
    initializeEditorRuntime(recordingConfig());
    scan(recordingConfig());

    const group = document.querySelector(".aqe-recording-group");
    const recordButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-record-voice"]')!;
    const playYoursButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play-recording"]')!;
    expect(group).not.toBeNull();
    expect(recordButton.classList.contains("aqe-icon-only")).toBe(true);
    expect(playYoursButton.classList.contains("aqe-icon-only")).toBe(true);
    expect(document.querySelector('[data-testid="aqe-split-0-record-voice-menu"]')).not.toBeNull();
    expect(recordButton.disabled).toBe(true);
    expect(playYoursButton.disabled).toBe(true);

    window.__aqeSetVisualizer?.(0, { ...track, sourceFilename: "clip one.mp3" }, 0);
    await Promise.resolve();
    expect(recordButton.disabled).toBe(false);
    expect(playYoursButton.disabled).toBe(true);

    const menu = document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-record-voice-menu"]')!;
    menu.click();
    await Promise.resolve();
    const countdown = document.querySelector<HTMLInputElement>('[data-testid="aqe-split-0-record-voice-value"]')!;
    countdown.value = "0";
    countdown.dispatchEvent(new Event("input", { bubbles: true }));

    recordButton.click();

    expect(bridgeCommands()).toContain("focus:0");
    expect(bridgeCommands()).toContain("aqe:command-payload");
    expect(window.__aqePendingCommandPayload).toMatchObject({
      command: "aqe:record-voice",
      fieldOrd: 0,
      graphSettings: { smoothness: expect.any(String) },
    });
  });

  it("renders the recording group in text mode when configured", () => {
    initializeEditorRuntime(textRecordingConfig());
    scan(textRecordingConfig());

    const recordButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-record-voice"]')!;
    const playYoursButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play-recording"]')!;
    expect(recordButton.classList.contains("aqe-icon-only")).toBe(false);
    expect(playYoursButton.classList.contains("aqe-icon-only")).toBe(false);
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

    window.__aqeSetLearnerRecordingState?.({
      fieldOrd: 0,
      generation: 1,
      status: "recording",
      targetDurationMs: track.durationMs,
    });

    expect(recordButton.dataset.aqeButtonState).toBe("recording");
    expect(recordButton.getAttribute("aria-label")).toBe("Stop recording your voice");
    expect(recordButton.disabled).toBe(false);
    expect(playYoursButton.disabled).toBe(true);

    recordButton.click();
    expect(bridgeCommands()).toContain("aqe:stop-recording");

    window.__aqeSetLearnerRecordingState?.({
      fieldOrd: 0,
      generation: 1,
      mediaFilename: "target__aqe_voice.wav",
      status: "ready",
      targetDurationMs: track.durationMs,
    });
    expect(playYoursButton.disabled).toBe(false);

    playYoursButton.click();
    expect(bridgeCommands()).toContain("aqe:play-recording");
  });

  it("renders learner pitch only, expands graph duration, and keeps target playback constrained", async () => {
    initializeEditorRuntime(recordingConfig());
    scan(recordingConfig());
    window.__aqeSetVisualizer?.(0, { ...track, sourceFilename: "clip one.mp3" }, 0);
    await Promise.resolve();

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
      durationMs: 1500,
      targetDurationMs: 1000,
      learnerDurationMs: 1500,
      learnerIntensityPaths: 0,
      learnerPitchPaths: 1,
      playbackEndMs: 1000,
    });
    expect(window.__aqeGraphStateForTest?.(0)?.intensity).not.toBe("");

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-graph"]')!.click();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      learnerDurationMs: 0,
      learnerPitchPaths: 0,
      learnerRecordingStatus: "idle",
    });
    window.__aqePopPendingGraphAnalysisRequest?.();
  });
});
