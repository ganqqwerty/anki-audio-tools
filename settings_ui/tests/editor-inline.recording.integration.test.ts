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

  it("enables learner recording after graph render and dispatches the record payload", async () => {
    vi.useFakeTimers();
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    const recordButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-record-voice"]')!;
    const playYoursButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play-recording"]')!;
    expect(recordButton.disabled).toBe(true);
    expect(playYoursButton.disabled).toBe(true);

    window.__aqeSetVisualizer?.(0, { ...track, sourceFilename: "clip one.mp3" }, 0);
    await Promise.resolve();
    expect(recordButton.disabled).toBe(false);
    expect(playYoursButton.disabled).toBe(true);

    recordButton.click();
    expect(window.__aqeGraphStateForTest?.(0)?.recordingStatus).toBe("countdown");
    expect(window.__aqeGraphStateForTest?.(0)?.allButtonsDisabled).toBe(true);

    vi.runOnlyPendingTimers();
    expect(bridgeCommands()).toContain("focus:0");
    expect(bridgeCommands()).toContain("aqe:command-payload");
    expect(window.__aqePendingCommandPayload).toMatchObject({
      command: "aqe:record-voice",
      fieldOrd: 0,
      graphSettings: { smoothness: expect.any(String) },
    });
  });

  it("updates learner recording controls from Python state callbacks", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, { ...track, sourceFilename: "clip one.mp3" }, 0);
    await Promise.resolve();

    window.__aqeSetBusy?.(0, true, "Recording...");
    window.__aqeSetLearnerRecordingState?.({
      fieldOrd: 0,
      generation: 1,
      status: "recording",
      targetDurationMs: track.durationMs,
    });
    expect(window.__aqeGraphStateForTest?.(0)?.recordingStatus).toBe("recording");
    expect(window.__aqeGraphStateForTest?.(0)?.recordingStatusText).toBe("Recording...");
    expect(window.__aqeGraphStateForTest?.(0)?.allButtonsDisabled).toBe(true);

    window.__aqeSetBusy?.(0, false);
    window.__aqeSetLearnerRecordingState?.({
      fieldOrd: 0,
      generation: 1,
      mediaFilename: "target__aqe_voice.wav",
      status: "ready",
      targetDurationMs: track.durationMs,
    });
    expect(window.__aqeGraphStateForTest?.(0)?.recordingStatus).toBe("ready");
    expect(window.__aqeGraphStateForTest?.(0)?.playRecordingButtonDisabled).toBe(false);

    window.__aqeSetLearnerRecordingState?.({
      failureMessage: "microphone unavailable",
      fieldOrd: 0,
      generation: 2,
      status: "failed",
    });
    expect(window.__aqeGraphStateForTest?.(0)?.recordingStatusText).toBe("microphone unavailable");
    expect(window.__aqeGraphStateForTest?.(0)?.playRecordingButtonDisabled).toBe(true);
  });

  it("renders learner pitch overlay without learner intensity", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, { ...track, sourceFilename: "clip one.mp3" }, 0);
    await Promise.resolve();
    const targetIntensity = window.__aqeGraphStateForTest?.(0)?.intensity;

    window.__aqeSetLearnerVisualizer?.(0, {
      ...track,
      pitchMaxHz: 500,
      pitchMinHz: 80,
      points: [
        [0, 130, 1, true],
        [250, 210, 0.2, true],
        [650, 180, 0.8, true],
        [1000, 260, 0.1, true],
      ],
      sourceFilename: "target__aqe_voice.wav",
    });

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      intensity: targetIntensity,
      learnerIntensityPaths: 0,
      learnerPitchPaths: 1,
      pitchPaths: 2,
    });

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-graph"]')!.click();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      learnerIntensityPaths: 0,
      learnerPitchPaths: 0,
    });
    window.__aqePopPendingGraphAnalysisRequest?.();
  });
});
