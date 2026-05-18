import { beforeEach, describe, expect, it } from "vitest";

import {
  buildTrimCommandPayload,
  buildSplitCommandPayload,
  clampSpeedStep,
  clampTrimStepMs,
  clampVolumeStepDb,
  formatDenoiseAlgorithm,
  formatPauseAggressiveness,
  formatSpeedStep,
  formatTrimMs,
  formatVolumeDb,
  getSplitButtonState,
  setDenoiseAlgorithmForField,
  setPauseAggressivenessForField,
  setSpeedStepForField,
  setTrimStepForField,
  setVolumeStepForField,
} from "../src/editor-inline/split-button-state.js";

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

  it("formats option split values for pause and denoise controls", () => {
    expect(formatPauseAggressiveness("gentle")).toBe("Gentle");
    expect(formatPauseAggressiveness("normal")).toBe("Normal");
    expect(formatPauseAggressiveness("aggressive")).toBe("Aggressive");
    expect(formatDenoiseAlgorithm("standard")).toBe("Standard");
    expect(formatDenoiseAlgorithm("rnnoise")).toBe("RNNoise");
  });

  it("initializes field state from editor runtime defaults", () => {
    window.__AQE_EDITOR_CONFIG__ = {
      audioFieldIndices: [0],
      splitButtonDefaults: {
        denoiseAlgorithm: "standard",
        pauseAggressiveness: "normal",
        speedStep: 0.05,
        trimStepMs: 250,
        volumeStepDb: 3,
      },
    };

    expect(getSplitButtonState(0).trimStepMs).toBe(250);
    expect(getSplitButtonState(0).volumeStepDb).toBe(3);
    expect(getSplitButtonState(0).speedStep).toBe(0.05);
    expect(getSplitButtonState(0).pauseAggressiveness).toBe("normal");
    expect(getSplitButtonState(0).denoiseAlgorithm).toBe("standard");
  });

  it("keeps trim state isolated per field", () => {
    window.__AQE_EDITOR_CONFIG__ = {
      audioFieldIndices: [0, 1],
      splitButtonDefaults: {
        denoiseAlgorithm: "standard",
        pauseAggressiveness: "normal",
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

  it("persists local field state across editor bundle reinjection", () => {
    setTrimStepForField(0, 200);
    expect(window.__aqeSplitButtonStates?.[0]?.trimStepMs).toBe(200);
    expect(getSplitButtonState(0).trimStepMs).toBe(200);
  });
});
