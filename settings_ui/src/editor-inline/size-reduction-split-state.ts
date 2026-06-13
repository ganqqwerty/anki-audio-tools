import {
  SIZE_REDUCTION_MODE_VALUES,
  clampSizeReductionBitrateKbps,
  clampSizeReductionChannels,
  clampSizeReductionSampleRateHz,
  sizeReductionPreset,
  sizeReductionModeOrDefault,
} from "../lib/size-reduction-parameters.js";
import type {
  FieldSplitButtonState,
  SplitButtonDefaults,
} from "./types.js";
import type { SplitDefaultSaveRequest } from "./split-default-save-types.js";

type CompleteSplitButtonDefaults = Required<SplitButtonDefaults>;

export type SizeReductionMode = FieldSplitButtonState["sizeReductionMode"];
export type SizeReductionAdvancedDefaults = Pick<
  FieldSplitButtonState,
  | "defaultSizeReductionBitrateKbps"
  | "defaultSizeReductionSampleRateHz"
  | "defaultSizeReductionChannels"
>;

export function defaultSizeReductionModeFromDefaults(
  defaults: CompleteSplitButtonDefaults,
): SizeReductionMode {
  return sizeReductionModeOrDefault(defaults.sizeReductionMode);
}

export function sizeReductionAdvancedDefaults(
  defaults: CompleteSplitButtonDefaults,
): SizeReductionAdvancedDefaults {
  const preset = sizeReductionPreset(defaultSizeReductionModeFromDefaults(defaults));
  return {
    defaultSizeReductionBitrateKbps: clampSizeReductionBitrateKbps(
      defaults.sizeReductionBitrateKbps ?? preset.bitrateKbps,
    ),
    defaultSizeReductionSampleRateHz: clampSizeReductionSampleRateHz(
      defaults.sizeReductionSampleRateHz ?? preset.sampleRateHz,
    ),
    defaultSizeReductionChannels: clampSizeReductionChannels(
      defaults.sizeReductionChannels ?? preset.channels,
    ),
  };
}

export function syncSizeReductionState(
  state: FieldSplitButtonState,
  defaultMode: SizeReductionMode,
  defaultParams: SizeReductionAdvancedDefaults,
): void {
  if (!SIZE_REDUCTION_MODE_VALUES.includes(state.sizeReductionMode)) {
    state.sizeReductionMode = defaultMode;
    state.sizeReductionEdited = false;
  }
  if (!state.sizeReductionEdited && state.defaultSizeReductionMode !== defaultMode) {
    state.defaultSizeReductionMode = defaultMode;
    state.sizeReductionMode = defaultMode;
  }
  syncSizeReductionAdvancedDefaults(state, defaultParams);
}

export function applyPromotedSizeReductionDefaultsToState(
  state: FieldSplitButtonState,
  defaults: CompleteSplitButtonDefaults,
  values: SplitDefaultSaveRequest["defaults"],
  forceCurrentField: boolean,
): void {
  if (values.sizeReductionMode !== undefined) {
    state.defaultSizeReductionMode = defaultSizeReductionModeFromDefaults(defaults);
    if (forceCurrentField || !state.sizeReductionEdited) {
      state.sizeReductionMode = state.defaultSizeReductionMode;
    }
    if (forceCurrentField) state.sizeReductionEdited = false;
  }
  if (sizeReductionAdvancedValuesChanged(values)) {
    syncSizeReductionAdvancedDefaults(state, sizeReductionAdvancedDefaults(defaults), forceCurrentField);
    if (forceCurrentField) state.sizeReductionEdited = false;
  }
}

export function setSizeReductionModeOnState(
  state: FieldSplitButtonState,
  value: SizeReductionMode,
): void {
  state.sizeReductionEdited = true;
  state.sizeReductionMode = sizeReductionModeOrDefault(value);
  const preset = sizeReductionPreset(state.sizeReductionMode);
  state.sizeReductionBitrateKbps = preset.bitrateKbps;
  state.sizeReductionSampleRateHz = preset.sampleRateHz;
  state.sizeReductionChannels = preset.channels;
}

export function setSizeReductionBitrateOnState(
  state: FieldSplitButtonState,
  value: number,
): void {
  state.sizeReductionEdited = true;
  state.sizeReductionBitrateKbps = clampSizeReductionBitrateKbps(value);
}

export function setSizeReductionSampleRateOnState(
  state: FieldSplitButtonState,
  value: number,
): void {
  state.sizeReductionEdited = true;
  state.sizeReductionSampleRateHz = clampSizeReductionSampleRateHz(value);
}

export function setSizeReductionChannelsOnState(
  state: FieldSplitButtonState,
  value: number,
): void {
  state.sizeReductionEdited = true;
  state.sizeReductionChannels = clampSizeReductionChannels(value);
}

function syncSizeReductionAdvancedDefaults(
  state: FieldSplitButtonState,
  defaults: SizeReductionAdvancedDefaults,
  forceCurrentField = false,
): void {
  syncNumberSizeReductionDefault(
    state,
    "defaultSizeReductionBitrateKbps",
    "sizeReductionBitrateKbps",
    defaults.defaultSizeReductionBitrateKbps,
    forceCurrentField,
  );
  syncNumberSizeReductionDefault(
    state,
    "defaultSizeReductionSampleRateHz",
    "sizeReductionSampleRateHz",
    defaults.defaultSizeReductionSampleRateHz,
    forceCurrentField,
  );
  syncNumberSizeReductionDefault(
    state,
    "defaultSizeReductionChannels",
    "sizeReductionChannels",
    defaults.defaultSizeReductionChannels,
    forceCurrentField,
  );
}

function syncNumberSizeReductionDefault(
  state: FieldSplitButtonState,
  defaultKey: keyof SizeReductionAdvancedDefaults,
  valueKey: keyof FieldSplitButtonState,
  value: number,
  forceCurrentField: boolean,
): void {
  if (state[defaultKey] !== value) {
    (state[defaultKey] as number) = value;
    if (forceCurrentField || !state.sizeReductionEdited) (state[valueKey] as number) = value;
  }
  if (!Number.isFinite(state[valueKey] as number)) (state[valueKey] as number) = value;
}

function sizeReductionAdvancedValuesChanged(values: SplitDefaultSaveRequest["defaults"]): boolean {
  return (
    values.sizeReductionBitrateKbps !== undefined ||
    values.sizeReductionSampleRateHz !== undefined ||
    values.sizeReductionChannels !== undefined
  );
}
