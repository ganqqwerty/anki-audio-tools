import { getSplitButtonState } from "./split-button-state.js";
import {
  setSizeReductionBitrateOnState,
  setSizeReductionChannelsOnState,
  setSizeReductionModeOnState,
  setSizeReductionSampleRateOnState,
  type SizeReductionMode,
} from "./size-reduction-split-state.js";
import type { FieldSplitButtonState } from "./types.js";

export function setSizeReductionModeForField(
  ord: number,
  value: SizeReductionMode,
): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  setSizeReductionModeOnState(state, value);
  return state;
}

export function setSizeReductionBitrateForField(
  ord: number,
  value: number,
): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  setSizeReductionBitrateOnState(state, value);
  return state;
}

export function setSizeReductionSampleRateForField(
  ord: number,
  value: number,
): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  setSizeReductionSampleRateOnState(state, value);
  return state;
}

export function setSizeReductionChannelsForField(
  ord: number,
  value: number,
): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  setSizeReductionChannelsOnState(state, value);
  return state;
}
