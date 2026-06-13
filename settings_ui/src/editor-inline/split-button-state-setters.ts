import type { EditorCommand, EditorCommandPayload, FieldSplitButtonState } from "./types.js";
import type { SplitDefaultSaveRequest } from "./split-default-save-types.js";
import {
  clampDpdfnetAttnLimitDb,
  clampRepeatPauseSeconds,
  clampSpeedStep,
  clampVolumeStepDb,
  outputFormatOrDefault,
  pauseDetectionAlgorithmOrDefault,
} from "../lib/audio-operation-parameters.js";
import {
  buildSplitCommandPayloadFromState,
  buildSplitDefaultSaveRequestFromState,
} from "./split-button-state-commands.js";
import {
  applyPausePresetToState,
  setPauseMinSpeechSecondsOnState,
  setPauseMinSilenceSecondsOnState,
  setPausePreprocessDenoiseOnState,
  setPauseThresholdOnState,
} from "./pause-split-state.js";
import {
  clampChorusingPauseSeconds,
  clampChorusingRepeatCount,
  clampVoiceRecordingCountdownSeconds,
  pitchHumModeOrDefault,
} from "./split-button-state-defaults.js";
import { getSplitButtonState } from "./split-button-state-core.js";
import type { PitchHumMode, ShareTarget } from "./split-button-state-defaults.js";

export const REPEAT_PAUSE_STATE_CHANGED_EVENT = "aqe-ui:repeat-pause-state-changed";

export interface RepeatPauseStateChangedDetail {
  ord: number;
  state: FieldSplitButtonState;
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
  notifyRepeatPauseStateChanged(ord, state);
  return state;
}

export function setChorusingPauseSecondsForField(ord: number, value: number): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.chorusingEdited = true;
  state.chorusingPauseSeconds = clampChorusingPauseSeconds(value);
  return state;
}

export function setChorusingAutoAdvanceForField(ord: number, value: boolean): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.chorusingEdited = true;
  state.chorusingAutoAdvance = value;
  return state;
}

export function setChorusingRepeatCountForField(ord: number, value: number): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.chorusingEdited = true;
  state.chorusingRepeatCount = clampChorusingRepeatCount(value);
  return state;
}

function notifyRepeatPauseStateChanged(ord: number, state: FieldSplitButtonState): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent<RepeatPauseStateChangedDetail>(
    REPEAT_PAUSE_STATE_CHANGED_EVENT,
    { detail: { ord, state } },
  ));
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

export const buildSplitDefaultSaveRequest = (command: EditorCommand, ord: number): SplitDefaultSaveRequest =>
  buildSplitDefaultSaveRequestFromState(command, ord, getSplitButtonState(ord));
