import { beforeEach, describe, expect, it } from "vitest";

import {
  buildSplitCommandPayload,
  getSplitButtonState,
  setShareTargetForField,
  setRepeatPauseSecondsForField,
  setSpeedStepForField,
  setVolumeStepForField,
} from "../src/editor-inline/split-button-state.js";

describe("split button state transitions", () => {
  beforeEach(() => {
    delete window.__AQE_EDITOR_CONFIG__;
    delete window.__aqeSplitButtonStates;
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

  it("keeps share target isolated per field", () => {
    setShareTargetForField(0, "catbox");

    expect(getSplitButtonState(0).shareTarget).toBe("catbox");
    expect(getSplitButtonState(1).shareTarget).toBe("litterbox");
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
