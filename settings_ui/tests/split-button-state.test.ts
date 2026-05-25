import { beforeEach, describe, expect, it } from "vitest";

import {
  buildSplitCommandPayload,
  buildSplitDefaultSaveRequest,
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
  getSplitButtonState,
  promoteSplitDefaultsForField,
  setDenoiseAlgorithmForField,
  setDpdfnetAttnLimitDbForField,
  setOutputFormatForField,
  setPauseAggressivenessForField,
  setPitchHumModeForField,
  setRepeatPauseSecondsForField,
  setShareTargetForField,
  setSpeedStepForField,
  setVoiceRecordingCountdownSecondsForField,
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
    expect(formatDenoiseAlgorithm("voice_only")).toBe("Voice Only");
    expect(formatPitchHumMode("direct")).toBe("Pitch-to-hum");
    expect(formatPitchHumMode("pitch_tier")).toBe("PitchTier");
    expect(formatOutputFormat("ogg")).toBe("MP3");
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

  it("initializes field state from editor runtime defaults", () => {
    window.__AQE_EDITOR_CONFIG__ = {
      audioFieldIndices: [0],
      splitButtonDefaults: {
        denoiseAlgorithm: "standard",
        dpdfnetAttnLimitDb: 18,
        graphConnectShortDropoutsMs: 60,
        graphRecordingCondition: "noisy",
        graphSmoothness: "smooth",
        graphVoiceLock: "stable",
        graphVoiceRange: "bass",
        outputFormat: "flac",
        pauseAggressiveness: "normal",
        pitchHumMode: "pitch_tier",
        repeatPauseSeconds: 1.5,
        shareTarget: "catbox",
        speedStep: 1.5,
        voiceRecordingCountdownSeconds: 5,
        volumeStepDb: 15,
      },
    };

    expect(getSplitButtonState(0).volumeStepDb).toBe(15);
    expect(getSplitButtonState(0).speedStep).toBe(1.5);
    expect(getSplitButtonState(0).repeatPauseSeconds).toBe(1.5);
    expect(getSplitButtonState(0).pauseAggressiveness).toBe("normal");
    expect(getSplitButtonState(0).denoiseAlgorithm).toBe("standard");
    expect(getSplitButtonState(0).dpdfnetAttnLimitDb).toBe(18);
    expect(getSplitButtonState(0).graphVoiceRange).toBe("bass");
    expect(getSplitButtonState(0).graphRecordingCondition).toBe("noisy");
    expect(getSplitButtonState(0).graphSmoothness).toBe("smooth");
    expect(getSplitButtonState(0).graphConnectShortDropoutsMs).toBe(60);
    expect(getSplitButtonState(0).graphVoiceLock).toBe("stable");
    expect(getSplitButtonState(0).outputFormat).toBe("flac");
    expect(getSplitButtonState(0).pitchHumMode).toBe("pitch_tier");
    expect(getSplitButtonState(0).shareTarget).toBe("catbox");
    expect(getSplitButtonState(0).voiceRecordingCountdownSeconds).toBe(5);
  });

  it("keeps volume state isolated per field", () => {
    window.__AQE_EDITOR_CONFIG__ = {
      audioFieldIndices: [0, 1],
      splitButtonDefaults: {
        denoiseAlgorithm: "standard",
        pauseAggressiveness: "normal",
        repeatPauseSeconds: 0,
        speedStep: 1.5,
        volumeStepDb: 15,
      },
    };

    setVolumeStepForField(0, 6);

    expect(getSplitButtonState(0).volumeStepDb).toBe(6);
    expect(getSplitButtonState(1).volumeStepDb).toBe(15);
  });

  it("builds volume and speed payloads from local field state", () => {
    setVolumeStepForField(0, 6);
    setSpeedStepForField(0, 2);

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
        speedStep: 2,
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
    setDpdfnetAttnLimitDbForField(0, 18);
    expect(buildSplitCommandPayload("aqe:rnnoise", 0)).toEqual({
      command: "aqe:dpdfnet",
      fieldOrd: 0,
      overrides: {
        denoiseAlgorithm: "dpdfnet",
        dpdfnetAttnLimitDb: 18,
      },
    });
  });

  it("builds convert payloads from local field state", () => {
    setOutputFormatForField(0, "wav");

    expect(buildSplitCommandPayload("aqe:convert", 0)).toEqual({
      command: "aqe:convert",
      fieldOrd: 0,
      overrides: {
        targetFormat: "wav",
      },
    });
  });

  it("builds share payloads from field-local share target state", () => {
    setShareTargetForField(0, "catbox");

    expect(buildSplitCommandPayload("aqe:share", 0)).toEqual({
      command: "aqe:share",
      fieldOrd: 0,
      shareTarget: "catbox",
    });
  });

  it("keeps share target isolated per field", () => {
    setShareTargetForField(0, "catbox");

    expect(getSplitButtonState(0).shareTarget).toBe("catbox");
    expect(getSplitButtonState(1).shareTarget).toBe("litterbox");
  });

  it("builds share default save requests from local field state", () => {
    setShareTargetForField(0, "catbox");

    expect(buildSplitDefaultSaveRequest("aqe:share", 0)).toEqual({
      defaults: {
        shareTarget: "catbox",
      },
      fieldOrd: 0,
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

  it("builds record voice payload and default save requests from local field state", () => {
    setVoiceRecordingCountdownSecondsForField(0, 0);

    expect(buildSplitCommandPayload("aqe:record-voice", 0)).toEqual({
      command: "aqe:record-voice",
      fieldOrd: 0,
      graphSettings: {
        connectShortDropoutsMs: 240,
        recordingCondition: "auto",
        smoothness: "very_smooth",
        voiceLock: "balanced",
        voiceRange: "general",
      },
    });
    expect(buildSplitDefaultSaveRequest("aqe:record-voice", 0)).toEqual({
      defaults: {
        voiceRecordingCountdownSeconds: 0,
      },
      fieldOrd: 0,
    });
  });

  it("builds graph default save requests from local field state", () => {
    setGraphVoiceRangeForField(0, "low");
    setGraphRecordingConditionForField(0, "studio");
    setGraphSmoothnessForField(0, "smooth");
    setGraphConnectShortDropoutsForField(0, 390);
    setGraphVoiceLockForField(0, "stable");

    expect(buildSplitDefaultSaveRequest("aqe:analyze", 0)).toEqual({
      defaults: {
        graphConnectShortDropoutsMs: 390,
        graphRecordingCondition: "studio",
        graphSmoothness: "smooth",
        graphVoiceLock: "stable",
        graphVoiceRange: "low",
      },
      fieldOrd: 0,
    });
  });

  it("builds pitch hum payloads from local field state", () => {
    setPitchHumModeForField(0, "pitch_tier");

    expect(buildSplitCommandPayload("aqe:pitch-hum", 0)).toEqual({
      command: "aqe:pitch-hum",
      fieldOrd: 0,
      graphSettings: {
        connectShortDropoutsMs: 240,
        recordingCondition: "auto",
        smoothness: "very_smooth",
        voiceLock: "balanced",
        voiceRange: "general",
      },
      overrides: {
        pitchHumMode: "pitch_tier",
      },
    });
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

  it("keeps repeat pause state field-local without changing command payloads", () => {
    setRepeatPauseSecondsForField(0, 2);

    expect(getSplitButtonState(0).repeatPauseSeconds).toBe(2);
    expect(getSplitButtonState(1).repeatPauseSeconds).toBe(0);
    expect(buildSplitCommandPayload("aqe:faster", 0).overrides).not.toHaveProperty("repeatPauseSeconds");
  });

  it("persists local field state across editor bundle reinjection", () => {
    setVolumeStepForField(0, 6);
    expect(window.__aqeSplitButtonStates?.[0]?.volumeStepDb).toBe(6);
    expect(getSplitButtonState(0).volumeStepDb).toBe(6);
  });
});
