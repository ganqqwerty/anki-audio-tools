import { beforeEach, describe, expect, it } from "vitest";

import {
  buildSplitCommandPayload,
  buildSplitDefaultSaveRequest,
  setChorusingAutoAdvanceForField,
  setChorusingPauseSecondsForField,
  setChorusingRepeatCountForField,
  setDenoiseAlgorithmForField,
  setDpdfnetAttnLimitDbForField,
  setOutputFormatForField,
  setPauseAggressivenessForField,
  setPauseDetectionAlgorithmForField,
  setPauseMinSilenceSecondsForField,
  setPauseMinSpeechSecondsForField,
  setPausePreprocessDenoiseForField,
  setPauseThresholdForField,
  setPitchHumModeForField,
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

describe("split button payloads", () => {
  beforeEach(() => {
    delete window.__AQE_EDITOR_CONFIG__;
    delete window.__aqeSplitButtonStates;
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
        pauseDetectionAlgorithm: "silencedetect",
        pauseMinSilenceSeconds: 0.14,
        pauseMinSpeechSeconds: 0.04,
        pausePreprocessDenoise: true,
        pauseThreshold: -52,
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

  it("builds pause payloads from manual advanced field state", () => {
    setPauseDetectionAlgorithmForField(0, "silero_vad");
    setPauseThresholdForField(0, 0.85);
    setPauseMinSilenceSecondsForField(0, 0.15);
    setPauseMinSpeechSecondsForField(0, 0.04);
    setPausePreprocessDenoiseForField(0, true);

    expect(buildSplitCommandPayload("aqe:remove-pauses", 0)).toEqual({
      command: "aqe:remove-pauses",
      fieldOrd: 0,
      overrides: {
        pauseAggressiveness: "normal",
        pauseDetectionAlgorithm: "silero_vad",
        pauseMinSilenceSeconds: 0.15,
        pauseMinSpeechSeconds: 0.04,
        pausePreprocessDenoise: true,
        pauseThreshold: 0.85,
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

  it("builds share default save requests from local field state", () => {
    setShareTargetForField(0, "catbox");

    expect(buildSplitDefaultSaveRequest("aqe:share", 0)).toEqual({
      defaults: {
        shareTarget: "catbox",
      },
      fieldOrd: 0,
    });
  });

  it("builds chorusing default save requests from local field state", () => {
    setChorusingPauseSecondsForField(0, 1.5);
    setChorusingAutoAdvanceForField(0, true);
    setChorusingRepeatCountForField(0, 6);

    expect(buildSplitDefaultSaveRequest("aqe:chorusing-practice", 0)).toEqual({
      defaults: {
        chorusingPauseSeconds: 1.5,
        chorusingAutoAdvanceByDefault: true,
        chorusingAutoAdvanceRepeats: 6,
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
});
