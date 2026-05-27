import type {
  EditorCommand,
  EditorCommandPayload,
  FieldSplitButtonState,
  SplitButtonDefaults,
} from "./types.js";
import type { SplitDefaultSaveRequest } from "./split-default-save-types.js";
import { t } from "../lib/i18n.js";
import {
  clampRepeatPauseSeconds,
  clampDpdfnetAttnLimitDb,
  DEFAULT_OUTPUT_FORMAT,
  clampSpeedStep,
  clampVolumeStepDb,
  outputFormatOrDefault,
  pauseDetectionAlgorithmOrDefault,
} from "../lib/audio-operation-parameters.js";
import {
  clampGraphConnectShortDropoutsMs,
  defaultGraphSplitValues,
  graphRecordingConditionOrDefault,
  graphSmoothnessOrDefault,
  graphVoiceLockOrDefault,
  graphVoiceRangeOrDefault,
} from "./graph-split-values.js";
import {
  buildSplitCommandPayloadFromState,
  buildSplitDefaultSaveRequestFromState,
} from "./split-button-state-commands.js";
import { applyPromotedGraphDefaultsToState } from "./graph-promoted-defaults.js";
import {
  applyPausePresetToState,
  applyPromotedPauseDefaultsToState,
  pauseDefaultValues,
  pauseFieldValuesFromDefaults,
  setPauseMinSilenceSecondsOnState,
  setPauseMinSpeechSecondsOnState,
  setPausePreprocessDenoiseOnState,
  setPauseThresholdOnState,
  syncPauseAdvancedDefaults,
} from "./pause-split-state.js";
export {
  clampRepeatPauseSeconds,
  clampDpdfnetAttnLimitDb,
  clampSpeedStep,
  clampVolumeStepDb,
  formatOutputFormat,
  formatPauseAggressiveness,
  formatPauseDetectionAlgorithm,
  formatDpdfnetAggressiveness,
  formatRepeatPauseSeconds,
  formatSpeedStep,
  formatVolumeDb,
} from "../lib/audio-operation-parameters.js";
export {
  formatDenoiseAlgorithm,
  formatPitchHumMode,
  formatShareTarget,
} from "./split-button-formatters.js";

type CompleteSplitButtonDefaults = Required<SplitButtonDefaults>;
type PitchHumMode = FieldSplitButtonState["pitchHumMode"];
type ShareTarget = FieldSplitButtonState["shareTarget"];
const DEFAULTS: CompleteSplitButtonDefaults = {
  denoiseAlgorithm: "standard",
  dpdfnetAttnLimitDb: 12,
  ...defaultGraphSplitValues(),
  outputFormat: DEFAULT_OUTPUT_FORMAT,
  pauseAggressiveness: "normal",
  pauseDetectionAlgorithm: "silencedetect",
  pauseSilencedetectThresholdDb: -45,
  pauseSilencedetectMinSilenceSeconds: 0.3,
  pauseSilencedetectMinSpeechSeconds: 0.1,
  pauseSilencedetectPreprocessDenoise: true,
  pauseSileroThreshold: 0.5,
  pauseSileroMinSilenceSeconds: 0.45,
  pauseSileroMinSpeechSeconds: 0.1,
  pauseSileroPreprocessDenoise: false,
  pitchHumMode: "direct",
  repeatPauseSeconds: 0,
  shareTarget: "litterbox",
  speedStep: 1.5,
  voiceRecordingCountdownSeconds: 3,
  volumeStepDb: 15,
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

export function clampVoiceRecordingCountdownSeconds(value: unknown): number {
  if (typeof value === "boolean" || typeof value !== "number" || !Number.isFinite(value)) {
    return 3;
  }
  return Math.max(0, Math.min(10, Math.round(value)));
}

export function formatVoiceRecordingCountdownSeconds(seconds: number): string {
  return t("editor.recording.countdown_seconds", { seconds: clampVoiceRecordingCountdownSeconds(seconds) });
}

function pitchHumModeOrDefault(value: unknown): PitchHumMode {
  return value === "pitch_tier" ? "pitch_tier" : "direct";
}

function shareTargetOrDefault(value: unknown): ShareTarget {
  return value === "catbox" ? "catbox" : "litterbox";
}

export function getSplitButtonState(ord: number): FieldSplitButtonState {
  const defaults = splitButtonDefaults();
  const defaultGraphConnectShortDropoutsMs = clampGraphConnectShortDropoutsMs(defaults.graphConnectShortDropoutsMs);
  const defaultGraphRecordingCondition = graphRecordingConditionOrDefault(defaults.graphRecordingCondition);
  const defaultGraphSmoothness = graphSmoothnessOrDefault(defaults.graphSmoothness);
  const defaultGraphVoiceLock = graphVoiceLockOrDefault(defaults.graphVoiceLock);
  const defaultGraphVoiceRange = graphVoiceRangeOrDefault(defaults.graphVoiceRange);
  const defaultOutputFormat = outputFormatOrDefault(defaults.outputFormat);
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
    const runtimeState = existing as FieldSplitButtonState & {
      defaultPauseDetectionAlgorithm?: unknown;
      pauseDetectionAlgorithm?: unknown;
      shareTarget?: ShareTarget;
    };
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

function replaceSplitButtonDefaults(values: Partial<CompleteSplitButtonDefaults>): CompleteSplitButtonDefaults {
  const nextDefaults = {
    ...splitButtonDefaults(),
    ...values,
  };
  window.__AQE_EDITOR_CONFIG__ = {
    ...(window.__AQE_EDITOR_CONFIG__ ?? { audioFieldIndices: [] }),
    splitButtonDefaults: nextDefaults,
  };
  return nextDefaults;
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

export function setVoiceRecordingCountdownSecondsForField(ord: number, value: number): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.voiceRecordingCountdownEdited = true;
  state.voiceRecordingCountdownSeconds = clampVoiceRecordingCountdownSeconds(value);
  return state;
}

export function setPauseAggressivenessForField(
  ord: number,
  value: FieldSplitButtonState["pauseAggressiveness"],
): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.pauseEdited = true;
  state.pauseAggressiveness = value;
  applyPausePresetToState(state);
  return state;
}

export function setPauseDetectionAlgorithmForField(
  ord: number,
  value: FieldSplitButtonState["pauseDetectionAlgorithm"],
): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.pauseEdited = true;
  state.pauseDetectionAlgorithm = pauseDetectionAlgorithmOrDefault(value);
  return state;
}

export function setPauseThresholdForField(ord: number, value: number): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.pauseEdited = true;
  setPauseThresholdOnState(state, value);
  return state;
}

export function setPauseMinSilenceSecondsForField(ord: number, value: number): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.pauseEdited = true;
  setPauseMinSilenceSecondsOnState(state, value);
  return state;
}

export function setPauseMinSpeechSecondsForField(ord: number, value: number): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.pauseEdited = true;
  setPauseMinSpeechSecondsOnState(state, value);
  return state;
}

export function setPausePreprocessDenoiseForField(ord: number, value: boolean): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.pauseEdited = true;
  setPausePreprocessDenoiseOnState(state, value);
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

export function setDpdfnetAttnLimitDbForField(ord: number, value: number): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.dpdfnetEdited = true;
  state.dpdfnetAttnLimitDb = clampDpdfnetAttnLimitDb(value);
  return state;
}

export function setPitchHumModeForField(ord: number, value: PitchHumMode): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.pitchHumEdited = true;
  state.pitchHumMode = pitchHumModeOrDefault(value);
  return state;
}

export function setShareTargetForField(ord: number, value: ShareTarget): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.shareEdited = true;
  state.shareTarget = value;
  return state;
}

export function setOutputFormatForField(ord: number, value: unknown): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.outputFormatEdited = true;
  state.outputFormat = outputFormatOrDefault(value);
  return state;
}

export function buildSplitCommandPayload(command: EditorCommand, ord: number): EditorCommandPayload {
  return buildSplitCommandPayloadFromState(command, ord, getSplitButtonState(ord));
}

export function buildSplitDefaultSaveRequest(command: EditorCommand, ord: number): SplitDefaultSaveRequest {
  return buildSplitDefaultSaveRequestFromState(command, ord, getSplitButtonState(ord));
}
