import type {
  EditorCommand,
  EditorCommandPayload,
  FieldSplitButtonState,
  SplitButtonDefaults,
} from "./types.js";
import { t } from "../lib/i18n.js";
import {
  clampRepeatPauseSeconds,
  clampSpeedStep,
  clampTrimStepMs,
  clampVolumeStepDb,
} from "../lib/audio-operation-parameters.js";
import {
  clampGraphConnectShortDropoutsMs,
  defaultGraphSplitValues,
  graphRecordingConditionOrDefault,
  graphSmoothnessOrDefault,
  graphVoiceLockOrDefault,
  graphVoiceRangeOrDefault,
} from "./graph-split-values.js";
export {
  clampRepeatPauseSeconds,
  clampSpeedStep,
  clampTrimStepMs,
  clampVolumeStepDb,
  formatPauseAggressiveness,
  formatRepeatPauseSeconds,
  formatSpeedStep,
  formatTrimMs,
  formatVolumeDb,
} from "../lib/audio-operation-parameters.js";

type CompleteSplitButtonDefaults = Required<SplitButtonDefaults>;
const DEFAULTS: CompleteSplitButtonDefaults = {
  denoiseAlgorithm: "standard",
  ...defaultGraphSplitValues(),
  pauseAggressiveness: "normal",
  repeatPauseSeconds: 0,
  speedStep: 0.05,
  trimStepMs: 100,
  volumeStepDb: 3,
};

function fieldStates(): Record<number, FieldSplitButtonState> {
  window.__aqeSplitButtonStates ??= {};
  return window.__aqeSplitButtonStates;
}

export function splitButtonDefaults(): CompleteSplitButtonDefaults {
  return {
    ...DEFAULTS,
    ...window.__AQE_EDITOR_CONFIG__?.splitButtonDefaults,
  };
}

export function formatDenoiseAlgorithm(value: FieldSplitButtonState["denoiseAlgorithm"]): string {
  if (value === "rnnoise") return t("settings.denoise_algorithm.rnnoise");
  if (value === "dpdfnet") return t("settings.denoise_algorithm.dpdfnet");
  if (value === "voice_only") return t("settings.denoise_algorithm.voice_only");
  return t("settings.denoise_algorithm.standard");
}

export function getSplitButtonState(ord: number): FieldSplitButtonState {
  const defaults = splitButtonDefaults();
  const defaultGraphConnectShortDropoutsMs = clampGraphConnectShortDropoutsMs(defaults.graphConnectShortDropoutsMs);
  const defaultGraphRecordingCondition = graphRecordingConditionOrDefault(defaults.graphRecordingCondition);
  const defaultGraphSmoothness = graphSmoothnessOrDefault(defaults.graphSmoothness);
  const defaultGraphVoiceLock = graphVoiceLockOrDefault(defaults.graphVoiceLock);
  const defaultGraphVoiceRange = graphVoiceRangeOrDefault(defaults.graphVoiceRange);
  const defaultTrimStepMs = clampTrimStepMs(defaults.trimStepMs);
  const defaultVolumeStepDb = clampVolumeStepDb(defaults.volumeStepDb);
  const defaultSpeedStep = clampSpeedStep(defaults.speedStep);
  const defaultRepeatPauseSeconds = clampRepeatPauseSeconds(defaults.repeatPauseSeconds);
  const defaultPauseAggressiveness = defaults.pauseAggressiveness;
  const defaultDenoiseAlgorithm = defaults.denoiseAlgorithm;
  const states = fieldStates();
  const existing = states[ord];
  if (existing) {
    if (!Number.isFinite(existing.repeatPauseSeconds)) {
      existing.repeatPauseSeconds = defaultRepeatPauseSeconds;
      existing.defaultRepeatPauseSeconds = defaultRepeatPauseSeconds;
      existing.repeatPauseEdited = false;
    }
    if (!existing.trimEdited && existing.defaultTrimStepMs !== defaultTrimStepMs) {
      existing.defaultTrimStepMs = defaultTrimStepMs;
      existing.trimStepMs = defaultTrimStepMs;
    }
    if (!existing.volumeEdited && existing.defaultVolumeStepDb !== defaultVolumeStepDb) {
      existing.defaultVolumeStepDb = defaultVolumeStepDb;
      existing.volumeStepDb = defaultVolumeStepDb;
    }
    if (!existing.speedEdited && existing.defaultSpeedStep !== defaultSpeedStep) {
      existing.defaultSpeedStep = defaultSpeedStep;
      existing.speedStep = defaultSpeedStep;
    }
    if (!existing.repeatPauseEdited && existing.defaultRepeatPauseSeconds !== defaultRepeatPauseSeconds) {
      existing.defaultRepeatPauseSeconds = defaultRepeatPauseSeconds;
      existing.repeatPauseSeconds = defaultRepeatPauseSeconds;
    }
    if (!existing.pauseEdited && existing.defaultPauseAggressiveness !== defaultPauseAggressiveness) {
      existing.defaultPauseAggressiveness = defaultPauseAggressiveness;
      existing.pauseAggressiveness = defaultPauseAggressiveness;
    }
    if (!existing.denoiseEdited && existing.defaultDenoiseAlgorithm !== defaultDenoiseAlgorithm) {
      existing.defaultDenoiseAlgorithm = defaultDenoiseAlgorithm;
      existing.denoiseAlgorithm = defaultDenoiseAlgorithm;
    }
    if (!existing.graphEdited) {
      if (existing.defaultGraphVoiceRange !== defaultGraphVoiceRange) {
        existing.defaultGraphVoiceRange = defaultGraphVoiceRange;
        existing.graphVoiceRange = defaultGraphVoiceRange;
      }
      if (existing.defaultGraphRecordingCondition !== defaultGraphRecordingCondition) {
        existing.defaultGraphRecordingCondition = defaultGraphRecordingCondition;
        existing.graphRecordingCondition = defaultGraphRecordingCondition;
      }
      if (existing.defaultGraphSmoothness !== defaultGraphSmoothness) {
        existing.defaultGraphSmoothness = defaultGraphSmoothness;
        existing.graphSmoothness = defaultGraphSmoothness;
      }
      if (existing.defaultGraphConnectShortDropoutsMs !== defaultGraphConnectShortDropoutsMs) {
        existing.defaultGraphConnectShortDropoutsMs = defaultGraphConnectShortDropoutsMs;
        existing.graphConnectShortDropoutsMs = defaultGraphConnectShortDropoutsMs;
      }
      if (existing.defaultGraphVoiceLock !== defaultGraphVoiceLock) {
        existing.defaultGraphVoiceLock = defaultGraphVoiceLock;
        existing.graphVoiceLock = defaultGraphVoiceLock;
      }
    }
    return existing;
  }
  const state = {
    defaultDenoiseAlgorithm,
    defaultGraphConnectShortDropoutsMs,
    defaultGraphRecordingCondition,
    defaultGraphSmoothness,
    defaultGraphVoiceLock,
    defaultGraphVoiceRange,
    defaultPauseAggressiveness,
    defaultRepeatPauseSeconds,
    defaultTrimStepMs,
    defaultVolumeStepDb,
    defaultSpeedStep,
    denoiseAlgorithm: defaultDenoiseAlgorithm,
    denoiseEdited: false,
    graphConnectShortDropoutsMs: defaultGraphConnectShortDropoutsMs,
    graphEdited: false,
    graphRecordingCondition: defaultGraphRecordingCondition,
    graphSmoothness: defaultGraphSmoothness,
    graphVoiceLock: defaultGraphVoiceLock,
    graphVoiceRange: defaultGraphVoiceRange,
    pauseAggressiveness: defaultPauseAggressiveness,
    pauseEdited: false,
    repeatPauseEdited: false,
    repeatPauseSeconds: defaultRepeatPauseSeconds,
    speedEdited: false,
    speedStep: defaultSpeedStep,
    trimEdited: false,
    trimStepMs: defaultTrimStepMs,
    volumeEdited: false,
    volumeStepDb: defaultVolumeStepDb,
  };
  states[ord] = state;
  return state;
}

export function setTrimStepForField(ord: number, value: number): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.trimEdited = true;
  state.trimStepMs = clampTrimStepMs(value);
  return state;
}

export function setVolumeStepForField(ord: number, value: number): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.volumeEdited = true;
  state.volumeStepDb = clampVolumeStepDb(value);
  return state;
}

export function setSpeedStepForField(ord: number, value: number): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.speedEdited = true;
  state.speedStep = clampSpeedStep(value);
  return state;
}

export function setRepeatPauseSecondsForField(ord: number, value: number): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.repeatPauseEdited = true;
  state.repeatPauseSeconds = clampRepeatPauseSeconds(value);
  return state;
}

export function setPauseAggressivenessForField(
  ord: number,
  value: FieldSplitButtonState["pauseAggressiveness"],
): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.pauseEdited = true;
  state.pauseAggressiveness = value;
  return state;
}

export function setDenoiseAlgorithmForField(
  ord: number,
  value: FieldSplitButtonState["denoiseAlgorithm"],
): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.denoiseEdited = true;
  state.denoiseAlgorithm = value;
  return state;
}

export function buildTrimCommandPayload(command: EditorCommand, ord: number): EditorCommandPayload {
  return {
    command,
    fieldOrd: ord,
    overrides: {
      trimStepMs: getSplitButtonState(ord).trimStepMs,
    },
  };
}

export function buildSplitCommandPayload(command: EditorCommand, ord: number): EditorCommandPayload {
  const state = getSplitButtonState(ord);
  if (command === "aqe:volume-up" || command === "aqe:volume-down") {
    return { command, fieldOrd: ord, overrides: { volumeStepDb: state.volumeStepDb } };
  }
  if (command === "aqe:faster" || command === "aqe:slower") {
    return { command, fieldOrd: ord, overrides: { speedStep: state.speedStep } };
  }
  if (command === "aqe:remove-pauses") {
    return { command, fieldOrd: ord, overrides: { pauseAggressiveness: state.pauseAggressiveness } };
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
    return { command: selectedCommand, fieldOrd: ord, overrides: { denoiseAlgorithm: state.denoiseAlgorithm } };
  }
  if (command === "aqe:analyze") {
    return {
      command,
      fieldOrd: ord,
      graphSettings: {
        connectShortDropoutsMs: state.graphConnectShortDropoutsMs,
        recordingCondition: state.graphRecordingCondition,
        smoothness: state.graphSmoothness,
        voiceLock: state.graphVoiceLock,
        voiceRange: state.graphVoiceRange,
      },
    };
  }
  return buildTrimCommandPayload(command, ord);
}
