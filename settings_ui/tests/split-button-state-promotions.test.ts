import { beforeEach, describe, expect, it } from "vitest";

import {
  getSplitButtonState,
  promoteSplitDefaultsForField,
  setPauseDetectionAlgorithmForField,
  setPauseThresholdForField,
  setShareTargetForField,
  setSpeedStepForField,
  splitButtonDefaults,
} from "../src/editor-inline/split-button-state.js";
import {
  setGraphConnectShortDropoutsForField,
  setGraphRecordingConditionForField,
  setGraphSmoothnessForField,
  setGraphVoiceLockForField,
  setGraphVoiceRangeForField,
} from "../src/editor-inline/graph-split-state.js";

describe("split button promotions", () => {
  beforeEach(() => {
    delete window.__AQE_EDITOR_CONFIG__;
    delete window.__aqeSplitButtonStates;
  });

  it("promotes local split values into runtime defaults", () => {
    setSpeedStepForField(0, 2);
    setSpeedStepForField(1, 3);

    promoteSplitDefaultsForField(0, { speedStep: 2 });

    expect(window.__AQE_EDITOR_CONFIG__?.splitButtonDefaults?.speedStep).toBe(2);
    expect(getSplitButtonState(0).speedEdited).toBe(false);
    expect(getSplitButtonState(0).speedStep).toBe(2);
    expect(getSplitButtonState(1).speedEdited).toBe(true);
    expect(getSplitButtonState(1).speedStep).toBe(3);
    expect(getSplitButtonState(2).speedStep).toBe(2);
  });

  it("promotes share target into runtime defaults", () => {
    setShareTargetForField(0, "catbox");
    setShareTargetForField(1, "litterbox");

    promoteSplitDefaultsForField(0, { shareTarget: "catbox" });

    expect(window.__AQE_EDITOR_CONFIG__?.splitButtonDefaults?.shareTarget).toBe("catbox");
    expect(getSplitButtonState(0).shareEdited).toBe(false);
    expect(getSplitButtonState(0).shareTarget).toBe("catbox");
    expect(getSplitButtonState(1).shareEdited).toBe(true);
    expect(getSplitButtonState(1).shareTarget).toBe("litterbox");
    expect(getSplitButtonState(2).shareTarget).toBe("catbox");
  });

  it("promotes pause advanced defaults into runtime defaults", () => {
    setPauseDetectionAlgorithmForField(1, "silero_vad");
    setPauseThresholdForField(1, 0.7);

    promoteSplitDefaultsForField(0, {
      pauseDetectionAlgorithm: "silero_vad",
      pauseSileroThreshold: 0.85,
      pauseSileroMinSilenceSeconds: 0.15,
      pauseSileroMinSpeechSeconds: 0.04,
      pauseSileroPreprocessDenoise: true,
    });

    expect(getSplitButtonState(0).pauseDetectionAlgorithm).toBe("silero_vad");
    expect(getSplitButtonState(0).pauseSileroThreshold).toBe(0.85);
    expect(getSplitButtonState(0).pauseSileroMinSilenceSeconds).toBe(0.15);
    expect(getSplitButtonState(0).pauseSileroMinSpeechSeconds).toBe(0.04);
    expect(getSplitButtonState(0).pauseSileroPreprocessDenoise).toBe(true);
    expect(getSplitButtonState(1).pauseEdited).toBe(true);
    expect(getSplitButtonState(1).pauseSileroThreshold).toBe(0.7);
    expect(getSplitButtonState(2).pauseDetectionAlgorithm).toBe("silero_vad");
    expect(getSplitButtonState(2).pauseSileroThreshold).toBe(0.85);
  });

  it("refreshes invalid pause advanced state from new runtime defaults", () => {
    const state = getSplitButtonState(0);
    state.pauseSilencedetectThresholdDb = Number.NaN;
    state.pauseSilencedetectPreprocessDenoise = "invalid" as unknown as boolean;
    window.__AQE_EDITOR_CONFIG__ = {
      ...(window.__AQE_EDITOR_CONFIG__ ?? { audioFieldIndices: [] }),
      splitButtonDefaults: {
        ...splitButtonDefaults(),
        pauseSilencedetectThresholdDb: -42,
        pauseSilencedetectPreprocessDenoise: false,
      },
    };

    expect(getSplitButtonState(0).pauseSilencedetectThresholdDb).toBe(-42);
    expect(getSplitButtonState(0).pauseSilencedetectPreprocessDenoise).toBe(false);
  });

  it("promotes graph defaults into runtime defaults", () => {
    setGraphVoiceRangeForField(0, "child");
    setGraphRecordingConditionForField(0, "studio");
    setGraphSmoothnessForField(0, "smooth");
    setGraphConnectShortDropoutsForField(0, 390);
    setGraphVoiceLockForField(0, "stable");
    setGraphVoiceRangeForField(1, "low");

    promoteSplitDefaultsForField(0, {
      graphConnectShortDropoutsMs: 390,
      graphRecordingCondition: "studio",
      graphSmoothness: "smooth",
      graphVoiceLock: "stable",
      graphVoiceRange: "child",
    });

    expect(getSplitButtonState(0).graphEdited).toBe(false);
    expect(getSplitButtonState(0).graphVoiceRange).toBe("child");
    expect(getSplitButtonState(1).graphEdited).toBe(true);
    expect(getSplitButtonState(1).graphVoiceRange).toBe("low");
    expect(getSplitButtonState(2).graphVoiceRange).toBe("child");
    expect(getSplitButtonState(2).graphConnectShortDropoutsMs).toBe(390);
  });
});
