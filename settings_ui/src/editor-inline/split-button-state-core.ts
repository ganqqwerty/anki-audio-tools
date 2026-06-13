import type { FieldSplitButtonState, SplitButtonDefaults } from "./types.js";
import type { SplitDefaultSaveRequest } from "./split-default-save-types.js";
import {
  clampRepeatPauseSeconds,
  clampDpdfnetAttnLimitDb,
  clampSpeedStep,
  clampVolumeStepDb,
  outputFormatOrDefault,
} from "../lib/audio-operation-parameters.js";
import {
  clampGraphConnectShortDropoutsMs,
  graphRecordingConditionOrDefault,
  graphSmoothnessOrDefault,
  graphVoiceLockOrDefault,
  graphVoiceRangeOrDefault,
} from "./graph-split-values.js";
import { applyPromotedGraphDefaultsToState } from "./graph-promoted-defaults.js";
import {
  applyPromotedPauseDefaultsToState,
  pauseDefaultValues,
  pauseFieldValuesFromDefaults,
  syncPauseAdvancedDefaults,
} from "./pause-split-state.js";
import {
  applyPromotedSizeReductionDefaultsToState,
  defaultSizeReductionModeFromDefaults,
  sizeReductionAdvancedDefaults,
  syncSizeReductionState,
} from "./size-reduction-split-state.js";
import { splitButtonDefaults, fieldStates, pitchHumModeOrDefault, shareTargetOrDefault, clampVoiceRecordingCountdownSeconds } from "./split-button-state-defaults.js";
import { updateEditorRuntimeConfig } from "./editor-runtime-config.js";

type CompleteSplitButtonDefaults = Required<SplitButtonDefaults>;
type ShareTarget = FieldSplitButtonState["shareTarget"];
type FieldSplitButtonPauseType = {
  defaultPauseDetectionAlgorithm?: unknown;
  pauseDetectionAlgorithm?: unknown;
  shareTarget?: ShareTarget;
};

function replaceSplitButtonDefaults(values: Partial<CompleteSplitButtonDefaults>): CompleteSplitButtonDefaults {
  const nextDefaults = {
    ...splitButtonDefaults(),
    ...values,
  };
  updateEditorRuntimeConfig({ splitButtonDefaults: nextDefaults });
  return nextDefaults;
}

export function getSplitButtonState(ord: number): FieldSplitButtonState {
  const defaults = splitButtonDefaults();
  const defaultGraphConnectShortDropoutsMs = clampGraphConnectShortDropoutsMs(defaults.graphConnectShortDropoutsMs);
  const defaultGraphRecordingCondition = graphRecordingConditionOrDefault(defaults.graphRecordingCondition);
  const defaultGraphSmoothness = graphSmoothnessOrDefault(defaults.graphSmoothness);
  const defaultGraphVoiceLock = graphVoiceLockOrDefault(defaults.graphVoiceLock);
  const defaultGraphVoiceRange = graphVoiceRangeOrDefault(defaults.graphVoiceRange);
  const defaultOutputFormat = outputFormatOrDefault(defaults.outputFormat);
  const defaultSizeReductionMode = defaultSizeReductionModeFromDefaults(defaults);
  const defaultSizeReductionParams = sizeReductionAdvancedDefaults(defaults);
  const defaultVolumeStepDb = clampVolumeStepDb(defaults.volumeStepDb);
  const defaultSpeedStep = clampSpeedStep(defaults.speedStep);
  const defaultRepeatPauseSeconds = clampRepeatPauseSeconds(defaults.repeatPauseSeconds);
  const defaultVoiceRecordingCountdownSeconds = clampVoiceRecordingCountdownSeconds(
    defaults.voiceRecordingCountdownSeconds,
  );
  const pauseDefaults = pauseDefaultValues(defaults);
  const defaultPitchHumMode = pitchHumModeOrDefault(defaults.pitchHumMode);
  const defaultDenoiseAlgorithm = defaults.denoiseAlgorithm;
  const defaultDpdfnetAttnLimitDb = clampDpdfnetAttnLimitDb(defaults.dpdfnetAttnLimitDb);
  const defaultShareTarget = shareTargetOrDefault(defaults.shareTarget);
  const states = fieldStates();
  const existing = states[ord];
  if (existing) {
    const runtimeState = existing as FieldSplitButtonState & FieldSplitButtonPauseType;
    if (!Number.isFinite(existing.repeatPauseSeconds)) {
      existing.repeatPauseSeconds = defaultRepeatPauseSeconds;
      existing.defaultRepeatPauseSeconds = defaultRepeatPauseSeconds;
      existing.repeatPauseEdited = false;
    }
    if (!Number.isFinite(existing.voiceRecordingCountdownSeconds)) {
      existing.voiceRecordingCountdownSeconds = defaultVoiceRecordingCountdownSeconds;
      existing.defaultVoiceRecordingCountdownSeconds = defaultVoiceRecordingCountdownSeconds;
      existing.voiceRecordingCountdownEdited = false;
    }
    if (runtimeState.shareTarget !== "catbox" && runtimeState.shareTarget !== "litterbox") {
      runtimeState.shareTarget = defaultShareTarget;
      existing.shareEdited = false;
    }
    syncSizeReductionState(existing, defaultSizeReductionMode, defaultSizeReductionParams);
    if (
      runtimeState.pauseDetectionAlgorithm !== "silencedetect" &&
      runtimeState.pauseDetectionAlgorithm !== "silero_vad"
    ) {
      existing.pauseDetectionAlgorithm = pauseDefaults.defaultPauseDetectionAlgorithm;
      existing.defaultPauseDetectionAlgorithm = pauseDefaults.defaultPauseDetectionAlgorithm;
      existing.pauseEdited = false;
    }
    if (
      runtimeState.defaultPauseDetectionAlgorithm !== "silencedetect" &&
      runtimeState.defaultPauseDetectionAlgorithm !== "silero_vad"
    ) {
      existing.defaultPauseDetectionAlgorithm = pauseDefaults.defaultPauseDetectionAlgorithm;
    }
    syncPauseAdvancedDefaults(existing, pauseDefaults);
    if (!existing.shareEdited && existing.shareTarget !== defaultShareTarget) {
      existing.shareTarget = defaultShareTarget;
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
    if (
      !existing.voiceRecordingCountdownEdited
      && existing.defaultVoiceRecordingCountdownSeconds !== defaultVoiceRecordingCountdownSeconds
    ) {
      existing.defaultVoiceRecordingCountdownSeconds = defaultVoiceRecordingCountdownSeconds;
      existing.voiceRecordingCountdownSeconds = defaultVoiceRecordingCountdownSeconds;
    }
    if (!existing.pauseEdited && existing.defaultPauseAggressiveness !== pauseDefaults.defaultPauseAggressiveness) {
      existing.defaultPauseAggressiveness = pauseDefaults.defaultPauseAggressiveness;
      existing.pauseAggressiveness = pauseDefaults.defaultPauseAggressiveness;
    }
    if (
      !existing.pauseEdited
      && existing.defaultPauseDetectionAlgorithm !== pauseDefaults.defaultPauseDetectionAlgorithm
    ) {
      existing.defaultPauseDetectionAlgorithm = pauseDefaults.defaultPauseDetectionAlgorithm;
      existing.pauseDetectionAlgorithm = pauseDefaults.defaultPauseDetectionAlgorithm;
    }
    if (!existing.outputFormatEdited && existing.defaultOutputFormat !== defaultOutputFormat) {
      existing.defaultOutputFormat = defaultOutputFormat;
      existing.outputFormat = defaultOutputFormat;
    }
    if (!existing.pitchHumEdited && existing.defaultPitchHumMode !== defaultPitchHumMode) {
      existing.defaultPitchHumMode = defaultPitchHumMode;
      existing.pitchHumMode = defaultPitchHumMode;
    }
    if (!existing.denoiseEdited && existing.defaultDenoiseAlgorithm !== defaultDenoiseAlgorithm) {
      existing.defaultDenoiseAlgorithm = defaultDenoiseAlgorithm;
      existing.denoiseAlgorithm = defaultDenoiseAlgorithm;
    }
    if (!existing.dpdfnetEdited && existing.defaultDpdfnetAttnLimitDb !== defaultDpdfnetAttnLimitDb) {
      existing.defaultDpdfnetAttnLimitDb = defaultDpdfnetAttnLimitDb;
      existing.dpdfnetAttnLimitDb = defaultDpdfnetAttnLimitDb;
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
  const state: FieldSplitButtonState = {
    defaultDenoiseAlgorithm,
    defaultDpdfnetAttnLimitDb,
    defaultGraphConnectShortDropoutsMs,
    defaultGraphRecordingCondition,
    defaultGraphSmoothness,
    defaultGraphVoiceLock,
    defaultGraphVoiceRange,
    defaultOutputFormat,
    defaultSizeReductionMode,
    ...defaultSizeReductionParams,
    ...pauseDefaults,
    defaultPitchHumMode,
    defaultRepeatPauseSeconds,
    defaultVoiceRecordingCountdownSeconds,
    defaultVolumeStepDb,
    defaultSpeedStep,
    denoiseAlgorithm: defaultDenoiseAlgorithm,
    denoiseEdited: false,
    dpdfnetAttnLimitDb: defaultDpdfnetAttnLimitDb,
    dpdfnetEdited: false,
    graphConnectShortDropoutsMs: defaultGraphConnectShortDropoutsMs,
    graphEdited: false,
    graphRecordingCondition: defaultGraphRecordingCondition,
    graphSmoothness: defaultGraphSmoothness,
    graphVoiceLock: defaultGraphVoiceLock,
    graphVoiceRange: defaultGraphVoiceRange,
    outputFormat: defaultOutputFormat,
    outputFormatEdited: false,
    sizeReductionEdited: false,
    sizeReductionMode: defaultSizeReductionMode,
    sizeReductionBitrateKbps: defaultSizeReductionParams.defaultSizeReductionBitrateKbps,
    sizeReductionSampleRateHz: defaultSizeReductionParams.defaultSizeReductionSampleRateHz,
    sizeReductionChannels: defaultSizeReductionParams.defaultSizeReductionChannels,
    ...pauseFieldValuesFromDefaults(pauseDefaults),
    pauseEdited: false,
    pitchHumEdited: false,
    pitchHumMode: defaultPitchHumMode,
    repeatPauseEdited: false,
    repeatPauseSeconds: defaultRepeatPauseSeconds,
    shareEdited: false,
    shareTarget: defaultShareTarget,
    speedEdited: false,
    speedStep: defaultSpeedStep,
    voiceRecordingCountdownEdited: false,
    voiceRecordingCountdownSeconds: defaultVoiceRecordingCountdownSeconds,
    volumeEdited: false,
    volumeStepDb: defaultVolumeStepDb,
  };
  states[ord] = state;
  return state;
}

function applyPromotedDefaultsToState(
  state: FieldSplitButtonState,
  defaults: CompleteSplitButtonDefaults,
  values: SplitDefaultSaveRequest["defaults"],
  forceCurrentField: boolean,
): void {
  if (values.volumeStepDb !== undefined) {
    state.defaultVolumeStepDb = clampVolumeStepDb(defaults.volumeStepDb);
    if (forceCurrentField || !state.volumeEdited) state.volumeStepDb = state.defaultVolumeStepDb;
    if (forceCurrentField) state.volumeEdited = false;
  }
  if (values.speedStep !== undefined) {
    state.defaultSpeedStep = clampSpeedStep(defaults.speedStep);
    if (forceCurrentField || !state.speedEdited) state.speedStep = state.defaultSpeedStep;
    if (forceCurrentField) state.speedEdited = false;
  }
  if (values.repeatPauseSeconds !== undefined) {
    state.defaultRepeatPauseSeconds = clampRepeatPauseSeconds(defaults.repeatPauseSeconds);
    if (forceCurrentField || !state.repeatPauseEdited) state.repeatPauseSeconds = state.defaultRepeatPauseSeconds;
    if (forceCurrentField) state.repeatPauseEdited = false;
  }
  if (values.voiceRecordingCountdownSeconds !== undefined) {
    state.defaultVoiceRecordingCountdownSeconds = clampVoiceRecordingCountdownSeconds(
      defaults.voiceRecordingCountdownSeconds,
    );
    if (forceCurrentField || !state.voiceRecordingCountdownEdited) {
      state.voiceRecordingCountdownSeconds = state.defaultVoiceRecordingCountdownSeconds;
    }
    if (forceCurrentField) state.voiceRecordingCountdownEdited = false;
  }
  applyPromotedPauseDefaultsToState(state, defaults, values, forceCurrentField);
  if (values.denoiseAlgorithm !== undefined) {
    state.defaultDenoiseAlgorithm = defaults.denoiseAlgorithm;
    if (forceCurrentField || !state.denoiseEdited) state.denoiseAlgorithm = state.defaultDenoiseAlgorithm;
    if (forceCurrentField) state.denoiseEdited = false;
  }
  if (values.dpdfnetAttnLimitDb !== undefined) {
    state.defaultDpdfnetAttnLimitDb = clampDpdfnetAttnLimitDb(defaults.dpdfnetAttnLimitDb);
    if (forceCurrentField || !state.dpdfnetEdited) state.dpdfnetAttnLimitDb = state.defaultDpdfnetAttnLimitDb;
    if (forceCurrentField) state.dpdfnetEdited = false;
  }
  applyPromotedSizeReductionDefaultsToState(state, defaults, values, forceCurrentField);
  if (values.pitchHumMode !== undefined) {
    state.defaultPitchHumMode = pitchHumModeOrDefault(defaults.pitchHumMode);
    if (forceCurrentField || !state.pitchHumEdited) state.pitchHumMode = state.defaultPitchHumMode;
    if (forceCurrentField) state.pitchHumEdited = false;
  }
  if (values.shareTarget !== undefined) {
    const nextShareTarget = shareTargetOrDefault(defaults.shareTarget);
    if (forceCurrentField || !state.shareEdited) state.shareTarget = nextShareTarget;
    if (forceCurrentField) state.shareEdited = false;
  }
  applyPromotedGraphDefaultsToState(state, defaults, values, forceCurrentField);
}

export function promoteSplitDefaultsForField(
  ord: number,
  values: SplitDefaultSaveRequest["defaults"],
): FieldSplitButtonState {
  const splitDefaults = { ...values };
  delete splitDefaults.repeatPlaybackByDefault;
  const nextDefaults = replaceSplitButtonDefaults(splitDefaults);
  for (const [rawOrd, state] of Object.entries(fieldStates())) {
    const forceCurrentField = Number(rawOrd) === ord;
    applyPromotedDefaultsToState(state, nextDefaults, values, forceCurrentField);
  }
  return getSplitButtonState(ord);
}
