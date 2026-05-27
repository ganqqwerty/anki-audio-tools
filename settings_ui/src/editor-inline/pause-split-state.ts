import type { FieldSplitButtonState, SplitButtonDefaults } from "./types.js";
import type { SplitDefaultSaveRequest } from "./split-default-save-types.js";
import {
  clampPauseSeconds,
  clampPauseThreshold,
  pauseDetectionAlgorithmOrDefault,
  pausePreset,
} from "../lib/audio-operation-parameters.js";

type CompleteSplitButtonDefaults = Required<SplitButtonDefaults>;

type PauseAdvancedDefaults = Pick<
  FieldSplitButtonState,
  | "defaultPauseSilencedetectThresholdDb"
  | "defaultPauseSilencedetectMinSilenceSeconds"
  | "defaultPauseSilencedetectMinSpeechSeconds"
  | "defaultPauseSilencedetectPreprocessDenoise"
  | "defaultPauseSileroThreshold"
  | "defaultPauseSileroMinSilenceSeconds"
  | "defaultPauseSileroMinSpeechSeconds"
  | "defaultPauseSileroPreprocessDenoise"
>;

export type PauseDefaultValues = PauseAdvancedDefaults &
  Pick<FieldSplitButtonState, "defaultPauseAggressiveness" | "defaultPauseDetectionAlgorithm">;

export function pauseDefaultValues(defaults: CompleteSplitButtonDefaults): PauseDefaultValues {
  return {
    defaultPauseAggressiveness: defaults.pauseAggressiveness,
    defaultPauseDetectionAlgorithm: pauseDetectionAlgorithmOrDefault(defaults.pauseDetectionAlgorithm),
    defaultPauseSilencedetectThresholdDb: clampPauseThreshold(
      "silencedetect",
      defaults.pauseSilencedetectThresholdDb,
    ),
    defaultPauseSilencedetectMinSilenceSeconds: clampPauseSeconds(
      defaults.pauseSilencedetectMinSilenceSeconds,
    ),
    defaultPauseSilencedetectMinSpeechSeconds: clampPauseSeconds(defaults.pauseSilencedetectMinSpeechSeconds),
    defaultPauseSilencedetectPreprocessDenoise: Boolean(defaults.pauseSilencedetectPreprocessDenoise),
    defaultPauseSileroThreshold: clampPauseThreshold("silero_vad", defaults.pauseSileroThreshold),
    defaultPauseSileroMinSilenceSeconds: clampPauseSeconds(defaults.pauseSileroMinSilenceSeconds),
    defaultPauseSileroMinSpeechSeconds: clampPauseSeconds(defaults.pauseSileroMinSpeechSeconds),
    defaultPauseSileroPreprocessDenoise: Boolean(defaults.pauseSileroPreprocessDenoise),
  };
}

export function pauseFieldValuesFromDefaults(
  defaults: PauseDefaultValues,
): Pick<
  FieldSplitButtonState,
  | "pauseAggressiveness"
  | "pauseDetectionAlgorithm"
  | "pauseSilencedetectThresholdDb"
  | "pauseSilencedetectMinSilenceSeconds"
  | "pauseSilencedetectMinSpeechSeconds"
  | "pauseSilencedetectPreprocessDenoise"
  | "pauseSileroThreshold"
  | "pauseSileroMinSilenceSeconds"
  | "pauseSileroMinSpeechSeconds"
  | "pauseSileroPreprocessDenoise"
> {
  return {
    pauseAggressiveness: defaults.defaultPauseAggressiveness,
    pauseDetectionAlgorithm: defaults.defaultPauseDetectionAlgorithm,
    pauseSilencedetectThresholdDb: defaults.defaultPauseSilencedetectThresholdDb,
    pauseSilencedetectMinSilenceSeconds: defaults.defaultPauseSilencedetectMinSilenceSeconds,
    pauseSilencedetectMinSpeechSeconds: defaults.defaultPauseSilencedetectMinSpeechSeconds,
    pauseSilencedetectPreprocessDenoise: defaults.defaultPauseSilencedetectPreprocessDenoise,
    pauseSileroThreshold: defaults.defaultPauseSileroThreshold,
    pauseSileroMinSilenceSeconds: defaults.defaultPauseSileroMinSilenceSeconds,
    pauseSileroMinSpeechSeconds: defaults.defaultPauseSileroMinSpeechSeconds,
    pauseSileroPreprocessDenoise: defaults.defaultPauseSileroPreprocessDenoise,
  };
}

export function syncPauseAdvancedDefaults(
  state: FieldSplitButtonState,
  defaults: PauseAdvancedDefaults,
  forceCurrentField = false,
): void {
  syncNumberPauseDefault(
    state,
    "defaultPauseSilencedetectThresholdDb",
    "pauseSilencedetectThresholdDb",
    defaults.defaultPauseSilencedetectThresholdDb,
    forceCurrentField,
  );
  syncNumberPauseDefault(
    state,
    "defaultPauseSilencedetectMinSilenceSeconds",
    "pauseSilencedetectMinSilenceSeconds",
    defaults.defaultPauseSilencedetectMinSilenceSeconds,
    forceCurrentField,
  );
  syncNumberPauseDefault(
    state,
    "defaultPauseSilencedetectMinSpeechSeconds",
    "pauseSilencedetectMinSpeechSeconds",
    defaults.defaultPauseSilencedetectMinSpeechSeconds,
    forceCurrentField,
  );
  syncBooleanPauseDefault(
    state,
    "defaultPauseSilencedetectPreprocessDenoise",
    "pauseSilencedetectPreprocessDenoise",
    defaults.defaultPauseSilencedetectPreprocessDenoise,
    forceCurrentField,
  );
  syncNumberPauseDefault(
    state,
    "defaultPauseSileroThreshold",
    "pauseSileroThreshold",
    defaults.defaultPauseSileroThreshold,
    forceCurrentField,
  );
  syncNumberPauseDefault(
    state,
    "defaultPauseSileroMinSilenceSeconds",
    "pauseSileroMinSilenceSeconds",
    defaults.defaultPauseSileroMinSilenceSeconds,
    forceCurrentField,
  );
  syncNumberPauseDefault(
    state,
    "defaultPauseSileroMinSpeechSeconds",
    "pauseSileroMinSpeechSeconds",
    defaults.defaultPauseSileroMinSpeechSeconds,
    forceCurrentField,
  );
  syncBooleanPauseDefault(
    state,
    "defaultPauseSileroPreprocessDenoise",
    "pauseSileroPreprocessDenoise",
    defaults.defaultPauseSileroPreprocessDenoise,
    forceCurrentField,
  );
}

export function applyPausePresetToState(state: FieldSplitButtonState): void {
  const preset = pausePreset(state.pauseDetectionAlgorithm, state.pauseAggressiveness);
  if (state.pauseDetectionAlgorithm === "silero_vad") {
    state.pauseSileroThreshold = preset.threshold;
    state.pauseSileroMinSilenceSeconds = preset.minSilenceSeconds;
    state.pauseSileroMinSpeechSeconds = preset.minSpeechSeconds;
    state.pauseSileroPreprocessDenoise = preset.preprocessDenoise;
    return;
  }
  state.pauseSilencedetectThresholdDb = preset.threshold;
  state.pauseSilencedetectMinSilenceSeconds = preset.minSilenceSeconds;
  state.pauseSilencedetectMinSpeechSeconds = preset.minSpeechSeconds;
  state.pauseSilencedetectPreprocessDenoise = preset.preprocessDenoise;
}

export function applyPromotedPauseDefaultsToState(
  state: FieldSplitButtonState,
  defaults: CompleteSplitButtonDefaults,
  values: SplitDefaultSaveRequest["defaults"],
  forceCurrentField: boolean,
): void {
  if (values.pauseAggressiveness !== undefined) {
    state.defaultPauseAggressiveness = defaults.pauseAggressiveness;
    if (forceCurrentField || !state.pauseEdited) state.pauseAggressiveness = state.defaultPauseAggressiveness;
    if (forceCurrentField) state.pauseEdited = false;
  }
  if (values.pauseDetectionAlgorithm !== undefined) {
    state.defaultPauseDetectionAlgorithm = pauseDetectionAlgorithmOrDefault(defaults.pauseDetectionAlgorithm);
    if (forceCurrentField || !state.pauseEdited) {
      state.pauseDetectionAlgorithm = state.defaultPauseDetectionAlgorithm;
    }
    if (forceCurrentField) state.pauseEdited = false;
  }
  if (pauseAdvancedValuesChanged(values)) {
    syncPauseAdvancedDefaults(state, pauseDefaultValues(defaults), forceCurrentField);
    if (forceCurrentField) state.pauseEdited = false;
  }
}

export function setPauseThresholdOnState(state: FieldSplitButtonState, value: number): void {
  if (state.pauseDetectionAlgorithm === "silero_vad") {
    state.pauseSileroThreshold = clampPauseThreshold("silero_vad", value);
  } else {
    state.pauseSilencedetectThresholdDb = clampPauseThreshold("silencedetect", value);
  }
}

export function setPauseMinSilenceSecondsOnState(state: FieldSplitButtonState, value: number): void {
  if (state.pauseDetectionAlgorithm === "silero_vad") {
    state.pauseSileroMinSilenceSeconds = clampPauseSeconds(value);
  } else {
    state.pauseSilencedetectMinSilenceSeconds = clampPauseSeconds(value);
  }
}

export function setPauseMinSpeechSecondsOnState(state: FieldSplitButtonState, value: number): void {
  if (state.pauseDetectionAlgorithm === "silero_vad") {
    state.pauseSileroMinSpeechSeconds = clampPauseSeconds(value);
  } else {
    state.pauseSilencedetectMinSpeechSeconds = clampPauseSeconds(value);
  }
}

export function setPausePreprocessDenoiseOnState(state: FieldSplitButtonState, value: boolean): void {
  if (state.pauseDetectionAlgorithm === "silero_vad") {
    state.pauseSileroPreprocessDenoise = value;
  } else {
    state.pauseSilencedetectPreprocessDenoise = value;
  }
}

function syncNumberPauseDefault(
  state: FieldSplitButtonState,
  defaultKey: keyof PauseAdvancedDefaults,
  valueKey: keyof FieldSplitButtonState,
  value: number,
  forceCurrentField: boolean,
): void {
  const target = state as unknown as Record<string, unknown>;
  if (target[defaultKey] !== value) {
    target[defaultKey] = value;
    if (forceCurrentField || !state.pauseEdited) target[valueKey] = value;
  }
  if (!Number.isFinite(target[valueKey])) target[valueKey] = value;
}

function syncBooleanPauseDefault(
  state: FieldSplitButtonState,
  defaultKey: keyof PauseAdvancedDefaults,
  valueKey: keyof FieldSplitButtonState,
  value: boolean,
  forceCurrentField: boolean,
): void {
  const target = state as unknown as Record<string, unknown>;
  if (target[defaultKey] !== value) {
    target[defaultKey] = value;
    if (forceCurrentField || !state.pauseEdited) target[valueKey] = value;
  }
  if (typeof target[valueKey] !== "boolean") target[valueKey] = value;
}

function pauseAdvancedValuesChanged(values: SplitDefaultSaveRequest["defaults"]): boolean {
  return (
    values.pauseSilencedetectThresholdDb !== undefined ||
    values.pauseSilencedetectMinSilenceSeconds !== undefined ||
    values.pauseSilencedetectMinSpeechSeconds !== undefined ||
    values.pauseSilencedetectPreprocessDenoise !== undefined ||
    values.pauseSileroThreshold !== undefined ||
    values.pauseSileroMinSilenceSeconds !== undefined ||
    values.pauseSileroMinSpeechSeconds !== undefined ||
    values.pauseSileroPreprocessDenoise !== undefined
  );
}
