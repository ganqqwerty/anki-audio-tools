import { beforeEach, describe, expect, it } from "vitest";

import {
  buildTrimCommandPayload,
  clampTrimStepMs,
  formatTrimMs,
  getSplitButtonState,
  setTrimStepForField,
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
