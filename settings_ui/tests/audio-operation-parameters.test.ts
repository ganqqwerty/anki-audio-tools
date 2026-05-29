import { describe, expect, it } from "vitest";

import {
  clampSpeedStep,
  clampVolumeStepDb,
  DEFAULT_OUTPUT_FORMAT,
  formatPauseAggressiveness,
  formatOutputFormat,
  formatSpeedStep,
  formatVolumeDb,
  OUTPUT_FORMAT_VALUES,
  outputFormatOrDefault,
} from "../src/lib/audio-operation-parameters.js";
import { configureI18n } from "../src/lib/i18n.js";

describe("audio-operation-parameters", () => {
  it("matches editor and batch clamp ranges", () => {
    expect(clampVolumeStepDb(99)).toBe(40);
    expect(clampVolumeStepDb(0.1)).toBe(1);
    expect(clampSpeedStep(0.001)).toBe(1.01);
    expect(clampSpeedStep(99)).toBe(5);
  });

  it("formats operation parameter labels consistently", () => {
    configureI18n("en", "ltr", {});

    expect(formatVolumeDb(1.5)).toBe("1.5 dB");
    expect(formatSpeedStep(1.5, "faster")).toBe("x1.5");
    expect(formatSpeedStep(2, "slower")).toBe("x2");
    expect(formatPauseAggressiveness("aggressive")).toBe("Aggressive");
    expect(formatOutputFormat("flac")).toBe("FLAC");
    expect(formatOutputFormat("source")).toBe("Same as source");
    expect(outputFormatOrDefault("aac")).toBe("source");
  });

  it("uses source as the persisted default output policy", () => {
    expect(DEFAULT_OUTPUT_FORMAT).toBe("source");
    expect(OUTPUT_FORMAT_VALUES).toEqual(["source", "mp3", "m4a", "wav", "flac"]);
    expect(outputFormatOrDefault("flac")).toBe("flac");
    expect(outputFormatOrDefault("source")).toBe("source");
    expect(outputFormatOrDefault("opus")).toBe("source");
  });
});
