import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import type { EditorRuntimeConfig } from "../src/editor-inline/types.js";
import {
  muteConsole,
  renderFields,
  setFullGraphViewport,
  setGraphBounds,
  track,
} from "./editor-inline.integration.helpers.js";
import {
  initAndScan,
  recordingConfig,
  setupAudioTrack,
} from "./editor-inline.recording.integration.helpers.js";

describe("editor inline graph-area controls", () => {
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

  it("mirrors configured toolbar visibility for graph-area controls", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    const actionRail = document.querySelector<HTMLElement>('[data-testid="aqe-graph-action-rail-0"]')!;
    expect(document.querySelector('[data-testid="aqe-graph-play-0"]')).not.toBeNull();
    expect(actionRail.querySelectorAll(".aqe-button")).toHaveLength(1);
    expect(document.querySelector('[data-testid="aqe-graph-repeat-0"]')).toBeNull();
    expect(document.querySelector('[data-testid="aqe-graph-settings-0"]')).not.toBeNull();
    expect(document.querySelector('[data-testid="aqe-graph-record-0"]')).toBeNull();
    expect(document.querySelector('[data-testid="aqe-graph-play-recording-0"]')).toBeNull();
  });

  it("keeps graph-area play synchronized with the toolbar control", async () => {
    const config = {
      audioFieldIndices: [0],
      splitButtonDefaults: {
        denoiseAlgorithm: "standard" as const,
        pauseAggressiveness: "normal" as const,
        repeatPauseSeconds: 0,
        speedStep: 1.5,
        volumeStepDb: 15,
      },
    };
    initializeEditorRuntime(config);
    scan(config);
    await Promise.resolve();

    window.__aqeSetVisualizer?.(0, track, 0);
    window.__aqeSetPlaybackState?.(0, "playing", 0);
    await Promise.resolve();

    expect(document.querySelector<HTMLButtonElement>('[data-testid="aqe-graph-play-0"]')).toHaveAttribute(
      "data-aqe-button-state",
      "pause",
    );
    expect(document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')).toHaveAttribute(
      "data-aqe-button-state",
      "pause",
    );
  });

  it("keeps recording controls out of the graph action rail", async () => {
    initAndScan(recordingConfig());

    expect(document.querySelector('[data-testid="aqe-button-0-record-voice"]')).not.toBeNull();
    expect(document.querySelector('[data-testid="aqe-button-0-play-recording"]')).not.toBeNull();
    expect(document.querySelector('[data-testid="aqe-graph-record-0"]')).toBeNull();
    expect(document.querySelector('[data-testid="aqe-graph-play-recording-0"]')).toBeNull();

    await setupAudioTrack();
    window.__aqeSetLearnerRecordingState?.({
      fieldOrd: 0,
      generation: 1,
      mediaFilename: "target__aqe_voice.wav",
      playbackStatus: "stopped",
      status: "ready",
      targetDurationMs: track.durationMs,
    });
    await new Promise((resolve) => window.setTimeout(resolve, 0));

    expect(document.querySelector('[data-testid="aqe-graph-record-0"]')).toBeNull();
    expect(document.querySelector('[data-testid="aqe-graph-play-recording-0"]')).toBeNull();
    expect(
      document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play-recording"]')?.disabled,
    ).toBe(false);
  });

  it("redraws the active graph when graph-area Speaker or Holes changes", async () => {
    const config: EditorRuntimeConfig = {
      audioFieldIndices: [0],
      splitButtonDefaults: {
        denoiseAlgorithm: "standard",
        graphConnectShortDropoutsMs: 0,
        graphRecordingCondition: "auto",
        graphSmoothness: "balanced",
        graphVoiceLock: "balanced",
        graphVoiceRange: "general",
        pauseAggressiveness: "normal",
        repeatPauseSeconds: 0,
        speedStep: 1.5,
        volumeStepDb: 15,
      },
    };
    initializeEditorRuntime(config);
    scan(config);
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 0);

    const voice = document.querySelector<HTMLSelectElement>('[data-testid="aqe-graph-voice-range-0"]')!;
    voice.value = "child";
    voice.dispatchEvent(new Event("change", { bubbles: true }));
    await Promise.resolve();

    expect(window.__aqePopPendingGraphAnalysisRequest?.()).toEqual({
      graphSettings: {
        connectShortDropoutsMs: 0,
        recordingCondition: "auto",
        smoothness: "balanced",
        voiceLock: "balanced",
        voiceRange: "child",
      },
      ord: 0,
      sourceFilename: "clip one.mp3",
    });

    window.__aqeSetVisualizer?.(0, { ...track, sourceFilename: "clip one.mp3" }, 0);
    const holes = document.querySelector<HTMLInputElement>('[data-testid="aqe-graph-connect-dropouts-0"]')!;
    holes.value = "90";
    holes.dispatchEvent(new Event("input", { bubbles: true }));
    await Promise.resolve();

    expect(window.__aqePopPendingGraphAnalysisRequest?.()).toEqual({
      graphSettings: {
        connectShortDropoutsMs: 90,
        recordingCondition: "auto",
        smoothness: "balanced",
        voiceLock: "balanced",
        voiceRange: "child",
      },
      ord: 0,
      sourceFilename: "clip one.mp3",
    });
  });

  it("keeps moved zoom controls wired to the current graph viewport", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 0);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    setFullGraphViewport();

    const zoomControls = document.querySelector<HTMLElement>('[data-testid="aqe-zoom-controls-0"]')!;
    expect(zoomControls.closest(".aqe-graph-layout")).not.toBeNull();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-zoom-in-0"]')!.click();

    const state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBeGreaterThanOrEqual(0);
    expect((state?.viewportEndMs ?? 1000) - (state?.viewportStartMs ?? 0)).toBeLessThan(1000);
  });
});
