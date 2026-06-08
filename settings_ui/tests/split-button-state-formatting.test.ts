import { beforeEach, describe, expect, it } from "vitest";

import {
  clampDpdfnetAttnLimitDb,
  clampRepeatPauseSeconds,
  clampSpeedStep,
  clampVoiceRecordingCountdownSeconds,
  clampVolumeStepDb,
  formatDenoiseAlgorithm,
  formatDpdfnetAggressiveness,
  formatOutputFormat,
  formatPauseAggressiveness,
  formatPitchHumMode,
  formatRepeatPauseSeconds,
  formatSpeedStep,
  formatVoiceRecordingCountdownSeconds,
  formatVolumeDb,
} from "../src/editor-inline/split-button-state.js";
import {
  clampGraphConnectShortDropoutsMs,
  formatGraphRecordingCondition,
  formatGraphSmoothness,
  formatGraphVoiceLock,
  formatGraphVoiceRange,
} from "../src/editor-inline/graph-split-values.js";

describe("split button formatting and clamps", () => {
  beforeEach(() => {
    delete window.__AQE_EDITOR_CONFIG__;
    delete window.__aqeSplitButtonStates;
  });

  it("formats and clamps volume step values", () => {
    expect(formatVolumeDb(15)).toBe("15 dB");
    expect(formatVolumeDb(2.5)).toBe("2.5 dB");
    expect(clampVolumeStepDb(0.1)).toBe(1);
    expect(clampVolumeStepDb(99)).toBe(40);
  });

  it("formats and clamps speed step values", () => {
    expect(formatSpeedStep(1.25, "aqe:faster")).toBe("x1.25");
    expect(formatSpeedStep(1.5, "aqe:slower")).toBe("x1.5");
    expect(clampSpeedStep(0.001)).toBe(1.01);
    expect(clampSpeedStep(99)).toBe(5);
  });

  it("formats and clamps repeat pause values", () => {
    expect(formatRepeatPauseSeconds(0)).toBe("0 s");
    expect(formatRepeatPauseSeconds(0.5)).toBe("0.5 s");
    expect(formatRepeatPauseSeconds(2)).toBe("2 s");
    expect(clampRepeatPauseSeconds(-1)).toBe(0);
    expect(clampRepeatPauseSeconds(20)).toBe(10);
    expect(clampRepeatPauseSeconds(0.56)).toBe(0.6);
  });

  it("formats and clamps voice recording countdown values", () => {
    expect(formatVoiceRecordingCountdownSeconds(3)).toBe("3s");
    expect(clampVoiceRecordingCountdownSeconds(-1)).toBe(0);
    expect(clampVoiceRecordingCountdownSeconds(20)).toBe(10);
    expect(clampVoiceRecordingCountdownSeconds(2.4)).toBe(2);
  });

  it("formats option split values for pause and denoise controls", () => {
    expect(formatPauseAggressiveness("gentle")).toBe("Gentle");
    expect(formatPauseAggressiveness("normal")).toBe("Normal");
    expect(formatPauseAggressiveness("aggressive")).toBe("Aggressive");
    expect(formatDenoiseAlgorithm("standard")).toBe("Standard");
    expect(formatDenoiseAlgorithm("rnnoise")).toBe("RNNoise");
    expect(formatDenoiseAlgorithm("dpdfnet")).toBe("DPDFNet");
    expect(formatDenoiseAlgorithm("voice_only")).toBe("Spleeter");
    expect(formatPitchHumMode("direct")).toBe("Pitch-to-hum");
    expect(formatPitchHumMode("pitch_tier")).toBe("PitchTier");
    expect(formatOutputFormat("ogg")).toBe("Same as source");
    expect(formatDpdfnetAggressiveness(6)).toBe("Gentle");
    expect(formatDpdfnetAggressiveness(12)).toBe("Normal");
    expect(formatDpdfnetAggressiveness(18)).toBe("Aggressive");
    expect(clampDpdfnetAttnLimitDb(17.4)).toBe(18);
  });

  it("formats and clamps graph split values", () => {
    expect(formatGraphVoiceRange("child")).toBe("Child/falcetto");
    expect(formatGraphRecordingCondition("very_noisy")).toBe("Very noisy");
    expect(formatGraphSmoothness("very_smooth")).toBe("Very smooth");
    expect(formatGraphVoiceLock("stable")).toBe("Stable");
    expect(clampGraphConnectShortDropoutsMs(-10)).toBe(0);
    expect(clampGraphConnectShortDropoutsMs(44)).toBe(30);
    expect(clampGraphConnectShortDropoutsMs(999)).toBe(500);
  });
});
