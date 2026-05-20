import { beforeEach, describe, expect, it } from "vitest";

import {
  buildSplitCommandPayload,
  buildTrimCommandPayload,
  clampRepeatPauseSeconds,
  clampSpeedStep,
  clampTrimStepMs,
  clampVolumeStepDb,
  formatDenoiseAlgorithm,
  formatPauseAggressiveness,
  formatRepeatPauseSeconds,
  formatSpeedStep,
  formatTrimMs,
  formatVolumeDb,
  getSplitButtonState,
  setDenoiseAlgorithmForField,
  setPauseAggressivenessForField,
  setRepeatPauseSecondsForField,
  setSpeedStepForField,
  setTrimStepForField,
  setVolumeStepForField,
} from "../src/editor-inline/split-button-state.js";
import {
  setGraphConnectShortDropoutsForField,
  setGraphRecordingConditionForField,
  setGraphSmoothnessForField,
  setGraphVoiceLockForField,
  setGraphVoiceRangeForField,
} from "../src/editor-inline/graph-split-state.js";
import {
  clampGraphConnectShortDropoutsMs,
  formatGraphRecordingCondition,
  formatGraphSmoothness,
  formatGraphVoiceLock,
  formatGraphVoiceRange,
} from "../src/editor-inline/graph-split-values.js";

describe("split button state", () => {
  beforeEach(() => {
    delete window.__AQE_EDITOR_CONFIG__;
    delete window.__aqeSplitButtonStates;
  });

  it("formats trim values for compact display", () => {
    expect(formatTrimMs(200)).toBe("200 ms");
    expect(formatTrimMs(999)).toBe("999 ms");
    expect(formatTrimMs(1000)).toBe("1 s");
    expect(formatTrimMs(1500)).toBe("1.5 s");
  });

  it("clamps trim values to the supported slider range", () => {
    expect(clampTrimStepMs(10)).toBe(50);
    expect(clampTrimStepMs(200)).toBe(200);
    expect(clampTrimStepMs(20000)).toBe(10000);
  });

  it("formats and clamps volume step values", () => {
    expect(formatVolumeDb(3)).toBe("3 dB");
    expect(formatVolumeDb(2.5)).toBe("2.5 dB");
    expect(clampVolumeStepDb(0.1)).toBe(0.5);
    expect(clampVolumeStepDb(20)).toBe(12);
  });

  it("formats and clamps speed step values", () => {
    expect(formatSpeedStep(0.05, "aqe:faster")).toBe("x1.05");
    expect(formatSpeedStep(0.1, "aqe:slower")).toBe("x0.90");
    expect(clampSpeedStep(0.001)).toBe(0.01);
    expect(clampSpeedStep(1)).toBe(0.25);
  });

  it("formats and clamps repeat pause values", () => {
    expect(formatRepeatPauseSeconds(0)).toBe("0 s");
    expect(formatRepeatPauseSeconds(0.5)).toBe("0.5 s");
    expect(formatRepeatPauseSeconds(2)).toBe("2 s");
    expect(clampRepeatPauseSeconds(-1)).toBe(0);
    expect(clampRepeatPauseSeconds(20)).toBe(10);
    expect(clampRepeatPauseSeconds(0.56)).toBe(0.6);
  });

  it("formats option split values for pause and denoise controls", () => {
    expect(formatPauseAggressiveness("gentle")).toBe("Gentle");
    expect(formatPauseAggressiveness("normal")).toBe("Normal");
    expect(formatPauseAggressiveness("aggressive")).toBe("Aggressive");
    expect(formatDenoiseAlgorithm("standard")).toBe("Standard");
    expect(formatDenoiseAlgorithm("rnnoise")).toBe("RNNoise");
    expect(formatDenoiseAlgorithm("dpdfnet")).toBe("DPDFNet");
    expect(formatDenoiseAlgorithm("voice_only")).toBe("Voice Only");
  });

  it("formats and clamps graph split values", () => {
    expect(formatGraphVoiceRange("child")).toBe("Child / falsetto");
    expect(formatGraphRecordingCondition("very_noisy")).toBe("Very noisy");
    expect(formatGraphSmoothness("very_smooth")).toBe("Very smooth");
    expect(formatGraphVoiceLock("stable")).toBe("Stable");
    expect(clampGraphConnectShortDropoutsMs(-10)).toBe(0);
    expect(clampGraphConnectShortDropoutsMs(44)).toBe(30);
    expect(clampGraphConnectShortDropoutsMs(999)).toBe(500);
  });

  it("initializes field state from editor runtime defaults", () => {
    window.__AQE_EDITOR_CONFIG__ = {
      audioFieldIndices: [0],
      splitButtonDefaults: {
        denoiseAlgorithm: "standard",
        graphConnectShortDropoutsMs: 60,
        graphRecordingCondition: "noisy",
        graphSmoothness: "smooth",
        graphVoiceLock: "stable",
        graphVoiceRange: "bass",
        pauseAggressiveness: "normal",
        repeatPauseSeconds: 1.5,
        speedStep: 0.05,
        trimStepMs: 250,
        volumeStepDb: 3,
      },
    };

    expect(getSplitButtonState(0).trimStepMs).toBe(250);
    expect(getSplitButtonState(0).volumeStepDb).toBe(3);
    expect(getSplitButtonState(0).speedStep).toBe(0.05);
    expect(getSplitButtonState(0).repeatPauseSeconds).toBe(1.5);
    expect(getSplitButtonState(0).pauseAggressiveness).toBe("normal");
    expect(getSplitButtonState(0).denoiseAlgorithm).toBe("standard");
    expect(getSplitButtonState(0).graphVoiceRange).toBe("bass");
    expect(getSplitButtonState(0).graphRecordingCondition).toBe("noisy");
    expect(getSplitButtonState(0).graphSmoothness).toBe("smooth");
    expect(getSplitButtonState(0).graphConnectShortDropoutsMs).toBe(60);
    expect(getSplitButtonState(0).graphVoiceLock).toBe("stable");
  });

  it("keeps trim state isolated per field", () => {
    window.__AQE_EDITOR_CONFIG__ = {
      audioFieldIndices: [0, 1],
      splitButtonDefaults: {
        denoiseAlgorithm: "standard",
        pauseAggressiveness: "normal",
        repeatPauseSeconds: 0,
        speedStep: 0.05,
        trimStepMs: 100,
        volumeStepDb: 3,
      },
    };

    setTrimStepForField(0, 200);

    expect(getSplitButtonState(0).trimStepMs).toBe(200);
    expect(getSplitButtonState(1).trimStepMs).toBe(100);
  });

  it("builds volume and speed payloads from local field state", () => {
    setVolumeStepForField(0, 6);
    setSpeedStepForField(0, 0.1);

    expect(buildSplitCommandPayload("aqe:volume-up", 0)).toEqual({
      command: "aqe:volume-up",
      fieldOrd: 0,
      overrides: {
        volumeStepDb: 6,
      },
    });
    expect(buildSplitCommandPayload("aqe:faster", 0)).toEqual({
      command: "aqe:faster",
      fieldOrd: 0,
      overrides: {
        speedStep: 0.1,
      },
    });
  });

  it("builds pause and denoise payloads from local field state", () => {
    setPauseAggressivenessForField(0, "aggressive");
    setDenoiseAlgorithmForField(0, "rnnoise");

    expect(buildSplitCommandPayload("aqe:remove-pauses", 0)).toEqual({
      command: "aqe:remove-pauses",
      fieldOrd: 0,
      overrides: {
        pauseAggressiveness: "aggressive",
      },
    });
    expect(buildSplitCommandPayload("aqe:denoise-standard", 0)).toEqual({
      command: "aqe:rnnoise",
      fieldOrd: 0,
      overrides: {
        denoiseAlgorithm: "rnnoise",
      },
    });

    setDenoiseAlgorithmForField(0, "voice_only");
    expect(buildSplitCommandPayload("aqe:denoise-standard", 0)).toEqual({
      command: "aqe:voice-only",
      fieldOrd: 0,
      overrides: {
        denoiseAlgorithm: "voice_only",
      },
    });

    setDenoiseAlgorithmForField(0, "dpdfnet");
    expect(buildSplitCommandPayload("aqe:rnnoise", 0)).toEqual({
      command: "aqe:dpdfnet",
      fieldOrd: 0,
      overrides: {
        denoiseAlgorithm: "dpdfnet",
      },
    });
  });

  it("builds graph payloads from local field state", () => {
    setGraphVoiceRangeForField(0, "child");
    setGraphRecordingConditionForField(0, "studio");
    setGraphSmoothnessForField(0, "very_smooth");
    setGraphConnectShortDropoutsForField(0, 90);
    setGraphVoiceLockForField(0, "stable");

    expect(buildSplitCommandPayload("aqe:analyze", 0)).toEqual({
      command: "aqe:analyze",
      fieldOrd: 0,
      graphSettings: {
        connectShortDropoutsMs: 90,
        recordingCondition: "studio",
        smoothness: "very_smooth",
        voiceLock: "stable",
        voiceRange: "child",
      },
    });
  });

  it("builds trim payloads from local field state", () => {
    setTrimStepForField(0, 200);

    expect(buildTrimCommandPayload("aqe:trim-left", 0)).toEqual({
      command: "aqe:trim-left",
      fieldOrd: 0,
      overrides: {
        trimStepMs: 200,
      },
    });
  });

  it("keeps repeat pause state field-local without changing command payloads", () => {
    setRepeatPauseSecondsForField(0, 2);

    expect(getSplitButtonState(0).repeatPauseSeconds).toBe(2);
    expect(getSplitButtonState(1).repeatPauseSeconds).toBe(0);
    expect(buildSplitCommandPayload("aqe:faster", 0).overrides).not.toHaveProperty("repeatPauseSeconds");
  });

  it("persists local field state across editor bundle reinjection", () => {
    setTrimStepForField(0, 200);
    expect(window.__aqeSplitButtonStates?.[0]?.trimStepMs).toBe(200);
    expect(getSplitButtonState(0).trimStepMs).toBe(200);
  });
});
