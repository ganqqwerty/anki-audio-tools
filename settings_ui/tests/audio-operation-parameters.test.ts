import { describe, expect, it } from "vitest";

import {
  clampSpeedStep,
  clampTrimStepMs,
  clampVolumeStepDb,
  formatPauseAggressiveness,
  formatOutputFormat,
  formatSpeedStep,
  formatTrimMs,
  formatVolumeDb,
  outputFormatOrDefault,
} from "../src/lib/audio-operation-parameters.js";
import { configureI18n } from "../src/lib/i18n.js";

describe("audio-operation-parameters", () => {
  it("matches editor and batch clamp ranges", () => {
    expect(clampTrimStepMs(10)).toBe(50);
    expect(clampTrimStepMs(20_000)).toBe(10_000);
    expect(clampVolumeStepDb(99)).toBe(12);
    expect(clampVolumeStepDb(0.1)).toBe(0.5);
    expect(clampSpeedStep(0.001)).toBe(0.01);
    expect(clampSpeedStep(1)).toBe(0.25);
  });

  it("formats operation parameter labels consistently", () => {
    configureI18n("en", "ltr", {});

    expect(formatTrimMs(500)).toBe("500 ms");
    expect(formatTrimMs(1500)).toBe("1.5 s");
    expect(formatVolumeDb(1.5)).toBe("1.5 dB");
    expect(formatSpeedStep(0.1, "faster")).toBe("x1.10");
    expect(formatSpeedStep(0.1, "slower")).toBe("x0.90");
    expect(formatPauseAggressiveness("aggressive")).toBe("Aggressive");
    expect(formatOutputFormat("flac")).toBe("FLAC");
    expect(outputFormatOrDefault("aac")).toBe("mp3");
  });
});
