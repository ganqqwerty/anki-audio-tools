import type {
  EditorCommand,
  EditorCommandPayload,
  FieldSplitButtonState,
} from "./types.js";
import type { SplitDefaultSaveRequest } from "./split-default-save-types.js";

function graphSettingsPayload(state: FieldSplitButtonState): NonNullable<EditorCommandPayload["graphSettings"]> {
  return {
    connectShortDropoutsMs: state.graphConnectShortDropoutsMs,
    recordingCondition: state.graphRecordingCondition,
    smoothness: state.graphSmoothness,
    voiceLock: state.graphVoiceLock,
    voiceRange: state.graphVoiceRange,
  };
}

export function buildSplitCommandPayloadFromState(
  command: EditorCommand,
  ord: number,
  state: FieldSplitButtonState,
): EditorCommandPayload {
  if (command === "aqe:volume-up" || command === "aqe:volume-down") {
    return { command, fieldOrd: ord, overrides: { volumeStepDb: state.volumeStepDb } };
  }
  if (command === "aqe:faster" || command === "aqe:slower") {
    return { command, fieldOrd: ord, overrides: { speedStep: state.speedStep } };
  }
  if (command === "aqe:remove-pauses") {
    return { command, fieldOrd: ord, overrides: { pauseAggressiveness: state.pauseAggressiveness } };
  }
  if (command === "aqe:convert") {
    return { command, fieldOrd: ord, overrides: { targetFormat: state.outputFormat } };
  }
  if (command === "aqe:share") {
    return { command, fieldOrd: ord, shareTarget: state.shareTarget };
  }
  if (
    command === "aqe:denoise-standard" ||
    command === "aqe:rnnoise" ||
    command === "aqe:dpdfnet" ||
    command === "aqe:voice-only"
  ) {
    const selectedCommand =
      state.denoiseAlgorithm === "rnnoise"
        ? "aqe:rnnoise"
        : state.denoiseAlgorithm === "dpdfnet"
          ? "aqe:dpdfnet"
          : state.denoiseAlgorithm === "voice_only"
            ? "aqe:voice-only"
            : "aqe:denoise-standard";
    const overrides: EditorCommandPayload["overrides"] = { denoiseAlgorithm: state.denoiseAlgorithm };
    if (state.denoiseAlgorithm === "dpdfnet") {
      overrides.dpdfnetAttnLimitDb = state.dpdfnetAttnLimitDb;
    }
    return { command: selectedCommand, fieldOrd: ord, overrides };
  }
  if (command === "aqe:analyze" || command === "aqe:pitch-hum") {
    const payload: EditorCommandPayload = {
      command,
      fieldOrd: ord,
      graphSettings: graphSettingsPayload(state),
    };
    if (command === "aqe:pitch-hum") {
      payload.overrides = { pitchHumMode: state.pitchHumMode };
    }
    return payload;
  }
  return { command, fieldOrd: ord };
}

export function buildSplitDefaultSaveRequestFromState(
  command: EditorCommand,
  ord: number,
  state: FieldSplitButtonState,
): SplitDefaultSaveRequest {
  const request: SplitDefaultSaveRequest = {
    defaults: {},
    fieldOrd: ord,
  };
  if (command === "aqe:volume-up" || command === "aqe:volume-down") {
    request.defaults.volumeStepDb = state.volumeStepDb;
  } else if (command === "aqe:faster" || command === "aqe:slower") {
    request.defaults.speedStep = state.speedStep;
  } else if (command === "aqe:remove-pauses") {
    request.defaults.pauseAggressiveness = state.pauseAggressiveness;
  } else if (
    command === "aqe:denoise-standard" ||
    command === "aqe:rnnoise" ||
    command === "aqe:dpdfnet" ||
    command === "aqe:voice-only"
  ) {
    request.defaults.denoiseAlgorithm = state.denoiseAlgorithm;
    request.defaults.dpdfnetAttnLimitDb = state.dpdfnetAttnLimitDb;
  } else if (command === "aqe:analyze") {
    request.defaults.graphVoiceRange = state.graphVoiceRange;
    request.defaults.graphRecordingCondition = state.graphRecordingCondition;
    request.defaults.graphSmoothness = state.graphSmoothness;
    request.defaults.graphConnectShortDropoutsMs = state.graphConnectShortDropoutsMs;
    request.defaults.graphVoiceLock = state.graphVoiceLock;
  } else if (command === "aqe:pitch-hum") {
    request.defaults.pitchHumMode = state.pitchHumMode;
  }
  return request;
}
