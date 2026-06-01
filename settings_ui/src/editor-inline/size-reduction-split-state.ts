import {
  SIZE_REDUCTION_MODE_VALUES,
  sizeReductionModeOrDefault,
} from "../lib/audio-operation-parameters.js";
import type {
  FieldSplitButtonState,
  SplitButtonDefaults,
} from "./types.js";
import type { SplitDefaultSaveRequest } from "./split-default-save-types.js";

type CompleteSplitButtonDefaults = Required<SplitButtonDefaults>;

export type SizeReductionMode = FieldSplitButtonState["sizeReductionMode"];

export function defaultSizeReductionModeFromDefaults(
  defaults: CompleteSplitButtonDefaults,
): SizeReductionMode {
  return sizeReductionModeOrDefault(defaults.sizeReductionMode);
}

export function syncSizeReductionState(
  state: FieldSplitButtonState,
  defaultMode: SizeReductionMode,
): void {
  if (!SIZE_REDUCTION_MODE_VALUES.includes(state.sizeReductionMode)) {
    state.sizeReductionMode = defaultMode;
    state.sizeReductionEdited = false;
  }
  if (!state.sizeReductionEdited && state.defaultSizeReductionMode !== defaultMode) {
    state.defaultSizeReductionMode = defaultMode;
    state.sizeReductionMode = defaultMode;
  }
}

export function applyPromotedSizeReductionDefaultsToState(
  state: FieldSplitButtonState,
  defaults: CompleteSplitButtonDefaults,
  values: SplitDefaultSaveRequest["defaults"],
  forceCurrentField: boolean,
): void {
  if (values.sizeReductionMode === undefined) return;
  state.defaultSizeReductionMode = defaultSizeReductionModeFromDefaults(defaults);
  if (forceCurrentField || !state.sizeReductionEdited) {
    state.sizeReductionMode = state.defaultSizeReductionMode;
  }
  if (forceCurrentField) state.sizeReductionEdited = false;
}

export function setSizeReductionModeOnState(
  state: FieldSplitButtonState,
  value: SizeReductionMode,
): void {
  state.sizeReductionEdited = true;
  state.sizeReductionMode = sizeReductionModeOrDefault(value);
}
