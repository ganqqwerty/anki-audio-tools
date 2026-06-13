import type { GraphRecordingCondition, GraphSmoothness, GraphVoiceLock, GraphVoiceRange } from "./graph-settings.js";
import type { FieldSplitButtonState } from "./types.js";
import {
  setChorusingAutoAdvanceForField,
  setChorusingPauseSecondsForField,
  setChorusingRepeatCountForField,
  setDenoiseAlgorithmForField,
  setDpdfnetAttnLimitDbForField,
  setOutputFormatForField,
  setPauseAggressivenessForField,
  setPauseDetectionAlgorithmForField,
  setPauseMinSilenceSecondsForField,
  setPauseMinSpeechSecondsForField,
  setPausePreprocessDenoiseForField,
  setPauseThresholdForField,
  setPitchHumModeForField,
  setShareTargetForField,
  setSpeedStepForField,
  setVoiceRecordingCountdownSecondsForField,
  setVolumeStepForField,
} from "./split-button-state.js";
import {
  setSizeReductionBitrateForField,
  setSizeReductionChannelsForField,
  setSizeReductionModeForField,
  setSizeReductionSampleRateForField,
} from "./size-reduction-field-state.js";
import {
  setGraphConnectShortDropoutsForField,
  setGraphRecordingConditionForField,
  setGraphSmoothnessForField,
  setGraphVoiceLockForField,
  setGraphVoiceRangeForField,
} from "./graph-split-state.js";

export type DenoiseAlgorithm = FieldSplitButtonState["denoiseAlgorithm"];
export type OutputFormatValue = FieldSplitButtonState["outputFormat"];
export type PauseAggressiveness = FieldSplitButtonState["pauseAggressiveness"];
export type PauseDetectionAlgorithm = FieldSplitButtonState["pauseDetectionAlgorithm"];
export type PitchHumMode = FieldSplitButtonState["pitchHumMode"];
export type SizeReductionMode = FieldSplitButtonState["sizeReductionMode"];
export type ShareTarget = FieldSplitButtonState["shareTarget"];
export type ChorusingSplitButtonState = Pick<
  FieldSplitButtonState,
  "chorusingPauseSeconds" | "chorusingAutoAdvance" | "chorusingRepeatCount"
>;

export interface SplitButtonStateMutators {
  setVolumeStepDb: (value: number) => void;
  setSpeedStep: (value: number) => void;
  setPauseAggressiveness: (value: PauseAggressiveness) => void;
  setPauseDetectionAlgorithm: (value: PauseDetectionAlgorithm) => void;
  setPauseThreshold: (value: number) => void;
  setPauseMinSilenceSeconds: (value: number) => void;
  setPauseMinSpeechSeconds: (value: number) => void;
  setPausePreprocessDenoise: (value: boolean) => void;
  setDenoiseAlgorithm: (value: DenoiseAlgorithm) => void;
  setDpdfnetAttnLimitDb: (value: number) => void;
  setOutputFormat: (value: OutputFormatValue) => void;
  setSizeReductionMode: (value: SizeReductionMode) => void;
  setSizeReductionBitrateKbps: (value: number) => void;
  setSizeReductionSampleRateHz: (value: number) => void;
  setSizeReductionChannels: (value: number) => void;
  setPitchHumMode: (value: PitchHumMode) => void;
  setShareTarget: (value: ShareTarget) => void;
  setGraphVoiceRange: (value: GraphVoiceRange) => void;
  setGraphRecordingCondition: (value: GraphRecordingCondition) => void;
  setGraphSmoothness: (value: GraphSmoothness) => void;
  setGraphConnectShortDropouts: (value: number) => void;
  setGraphVoiceLock: (value: GraphVoiceLock) => void;
  setVoiceRecordingCountdownSeconds: (value: number) => void;
}

export interface SplitButtonStateHandlers {
  syncFromState: (state: FieldSplitButtonState) => void;
  syncPauseFromState: (state: FieldSplitButtonState) => void;
  applyVolumeStep: (value: number) => void;
  applySpeedStep: (value: number) => void;
  applyPauseAggressiveness: (value: PauseAggressiveness) => void;
  applyPauseDetectionAlgorithm: (value: PauseDetectionAlgorithm) => void;
  applyPauseThreshold: (value: number) => void;
  applyPauseMinSilenceSeconds: (value: number) => void;
  applyPauseMinSpeechSeconds: (value: number) => void;
  applyPausePreprocessDenoise: (value: boolean) => void;
  applyDenoiseAlgorithm: (value: DenoiseAlgorithm) => void;
  applyDpdfnetAttnLimitDb: (value: number) => void;
  applyOutputFormat: (value: OutputFormatValue) => void;
  applySizeReductionMode: (value: SizeReductionMode) => void;
  applySizeReductionBitrateKbps: (value: number) => void;
  applySizeReductionSampleRateHz: (value: number) => void;
  applySizeReductionChannels: (value: number) => void;
  applyPitchHumMode: (value: PitchHumMode) => void;
  applyShareTarget: (value: ShareTarget) => void;
  applyGraphVoiceRange: (value: GraphVoiceRange) => void;
  applyGraphRecordingCondition: (value: GraphRecordingCondition) => void;
  applyGraphSmoothness: (value: GraphSmoothness) => void;
  applyGraphConnectShortDropouts: (value: number) => void;
  applyGraphVoiceLock: (value: GraphVoiceLock) => void;
  applyVoiceRecordingCountdownSeconds: (value: number) => void;
}

export interface ChorusingSplitButtonMutators {
  setChorusingPauseSeconds: (value: number) => void;
  setChorusingAutoAdvance: (value: boolean) => void;
  setChorusingRepeatCount: (value: number) => void;
}

export interface ChorusingSplitButtonHandlers {
  syncFromState: (state: ChorusingSplitButtonState) => void;
  applyPauseSeconds: (value: number) => void;
  applyAutoAdvance: (value: boolean) => void;
  applyRepeatCount: (value: number) => void;
}

export function createSplitButtonStateHandlers(
  getTargetOrd: () => number,
  mutators: SplitButtonStateMutators,
): SplitButtonStateHandlers {
  const {
    setVolumeStepDb,
    setSpeedStep,
    setPauseAggressiveness,
    setPauseDetectionAlgorithm,
    setPauseThreshold,
    setPauseMinSilenceSeconds,
    setPauseMinSpeechSeconds,
    setPausePreprocessDenoise,
    setDenoiseAlgorithm,
    setDpdfnetAttnLimitDb,
    setOutputFormat,
    setSizeReductionMode,
    setSizeReductionBitrateKbps,
    setSizeReductionSampleRateHz,
    setSizeReductionChannels,
    setPitchHumMode,
    setShareTarget,
    setGraphVoiceRange,
    setGraphRecordingCondition,
    setGraphSmoothness,
    setGraphConnectShortDropouts,
    setGraphVoiceLock,
    setVoiceRecordingCountdownSeconds,
  } = mutators;

  const syncPauseFromState = (state: FieldSplitButtonState): void => {
    setPauseDetectionAlgorithm(state.pauseDetectionAlgorithm);
    if (state.pauseDetectionAlgorithm === "silero_vad") {
      setPauseThreshold(state.pauseSileroThreshold);
      setPauseMinSilenceSeconds(state.pauseSileroMinSilenceSeconds);
      setPauseMinSpeechSeconds(state.pauseSileroMinSpeechSeconds);
      setPausePreprocessDenoise(state.pauseSileroPreprocessDenoise);
      return;
    }
    setPauseThreshold(state.pauseSilencedetectThresholdDb);
    setPauseMinSilenceSeconds(state.pauseSilencedetectMinSilenceSeconds);
    setPauseMinSpeechSeconds(state.pauseSilencedetectMinSpeechSeconds);
    setPausePreprocessDenoise(state.pauseSilencedetectPreprocessDenoise);
  };

  const syncFromState = (state: FieldSplitButtonState): void => {
    setVolumeStepDb(state.volumeStepDb);
    setSpeedStep(state.speedStep);
    setPauseAggressiveness(state.pauseAggressiveness);
    syncPauseFromState(state);
    setDenoiseAlgorithm(state.denoiseAlgorithm);
    setDpdfnetAttnLimitDb(state.dpdfnetAttnLimitDb);
    setOutputFormat(state.outputFormat);
    setSizeReductionMode(state.sizeReductionMode);
    setSizeReductionBitrateKbps(state.sizeReductionBitrateKbps);
    setSizeReductionSampleRateHz(state.sizeReductionSampleRateHz);
    setSizeReductionChannels(state.sizeReductionChannels);
    setPitchHumMode(state.pitchHumMode);
    setShareTarget(state.shareTarget);
    setGraphVoiceRange(state.graphVoiceRange);
    setGraphRecordingCondition(state.graphRecordingCondition);
    setGraphSmoothness(state.graphSmoothness);
    setGraphConnectShortDropouts(state.graphConnectShortDropoutsMs);
    setGraphVoiceLock(state.graphVoiceLock);
    setVoiceRecordingCountdownSeconds(state.voiceRecordingCountdownSeconds);
  };

  const applyVolumeStep = (value: number): void => {
    setVolumeStepDb(setVolumeStepForField(getTargetOrd(), value).volumeStepDb);
  };

  const applySpeedStep = (value: number): void => {
    setSpeedStep(setSpeedStepForField(getTargetOrd(), value).speedStep);
  };

  const applyPauseAggressiveness = (value: PauseAggressiveness): void => {
    const nextState = setPauseAggressivenessForField(getTargetOrd(), value);
    setPauseAggressiveness(nextState.pauseAggressiveness);
    syncPauseFromState(nextState);
  };

  const applyPauseDetectionAlgorithm = (value: PauseDetectionAlgorithm): void => {
    syncPauseFromState(setPauseDetectionAlgorithmForField(getTargetOrd(), value));
  };

  const applyPauseThreshold = (value: number): void => {
    syncPauseFromState(setPauseThresholdForField(getTargetOrd(), value));
  };

  const applyPauseMinSilenceSeconds = (value: number): void => {
    syncPauseFromState(setPauseMinSilenceSecondsForField(getTargetOrd(), value));
  };

  const applyPauseMinSpeechSeconds = (value: number): void => {
    syncPauseFromState(setPauseMinSpeechSecondsForField(getTargetOrd(), value));
  };

  const applyPausePreprocessDenoise = (value: boolean): void => {
    syncPauseFromState(setPausePreprocessDenoiseForField(getTargetOrd(), value));
  };

  const applyDenoiseAlgorithm = (value: DenoiseAlgorithm): void => {
    setDenoiseAlgorithm(setDenoiseAlgorithmForField(getTargetOrd(), value).denoiseAlgorithm);
  };

  const applyDpdfnetAttnLimitDb = (value: number): void => {
    setDpdfnetAttnLimitDb(setDpdfnetAttnLimitDbForField(getTargetOrd(), value).dpdfnetAttnLimitDb);
  };

  const applyOutputFormat = (value: OutputFormatValue): void => {
    setOutputFormat(setOutputFormatForField(getTargetOrd(), value).outputFormat);
  };

  const applySizeReductionMode = (value: SizeReductionMode): void => {
    const nextState = setSizeReductionModeForField(getTargetOrd(), value);
    setSizeReductionMode(nextState.sizeReductionMode);
    setSizeReductionBitrateKbps(nextState.sizeReductionBitrateKbps);
    setSizeReductionSampleRateHz(nextState.sizeReductionSampleRateHz);
    setSizeReductionChannels(nextState.sizeReductionChannels);
  };

  const applySizeReductionBitrateKbps = (value: number): void => {
    const nextState = setSizeReductionBitrateForField(getTargetOrd(), value);
    setSizeReductionMode(nextState.sizeReductionMode);
    setSizeReductionBitrateKbps(nextState.sizeReductionBitrateKbps);
    setSizeReductionSampleRateHz(nextState.sizeReductionSampleRateHz);
    setSizeReductionChannels(nextState.sizeReductionChannels);
  };

  const applySizeReductionSampleRateHz = (value: number): void => {
    const nextState = setSizeReductionSampleRateForField(getTargetOrd(), value);
    setSizeReductionMode(nextState.sizeReductionMode);
    setSizeReductionBitrateKbps(nextState.sizeReductionBitrateKbps);
    setSizeReductionSampleRateHz(nextState.sizeReductionSampleRateHz);
    setSizeReductionChannels(nextState.sizeReductionChannels);
  };

  const applySizeReductionChannels = (value: number): void => {
    const nextState = setSizeReductionChannelsForField(getTargetOrd(), value);
    setSizeReductionMode(nextState.sizeReductionMode);
    setSizeReductionBitrateKbps(nextState.sizeReductionBitrateKbps);
    setSizeReductionSampleRateHz(nextState.sizeReductionSampleRateHz);
    setSizeReductionChannels(nextState.sizeReductionChannels);
  };

  const applyPitchHumMode = (value: PitchHumMode): void => {
    setPitchHumMode(setPitchHumModeForField(getTargetOrd(), value).pitchHumMode);
  };

  const applyShareTarget = (value: ShareTarget): void => {
    setShareTarget(setShareTargetForField(getTargetOrd(), value).shareTarget);
  };

  const applyGraphVoiceRange = (value: GraphVoiceRange): void => {
    setGraphVoiceRange(setGraphVoiceRangeForField(getTargetOrd(), value).graphVoiceRange);
  };

  const applyGraphRecordingCondition = (value: GraphRecordingCondition): void => {
    setGraphRecordingCondition(setGraphRecordingConditionForField(getTargetOrd(), value).graphRecordingCondition);
  };

  const applyGraphSmoothness = (value: GraphSmoothness): void => {
    setGraphSmoothness(setGraphSmoothnessForField(getTargetOrd(), value).graphSmoothness);
  };

  const applyGraphConnectShortDropouts = (value: number): void => {
    setGraphConnectShortDropouts(setGraphConnectShortDropoutsForField(getTargetOrd(), value).graphConnectShortDropoutsMs);
  };

  const applyGraphVoiceLock = (value: GraphVoiceLock): void => {
    setGraphVoiceLock(setGraphVoiceLockForField(getTargetOrd(), value).graphVoiceLock);
  };

  const applyVoiceRecordingCountdownSeconds = (value: number): void => {
    setVoiceRecordingCountdownSeconds(setVoiceRecordingCountdownSecondsForField(getTargetOrd(), value).voiceRecordingCountdownSeconds);
  };

  return {
    syncFromState,
    syncPauseFromState,
    applyVolumeStep,
    applySpeedStep,
    applyPauseAggressiveness,
    applyPauseDetectionAlgorithm,
    applyPauseThreshold,
    applyPauseMinSilenceSeconds,
    applyPauseMinSpeechSeconds,
    applyPausePreprocessDenoise,
    applyDenoiseAlgorithm,
    applyDpdfnetAttnLimitDb,
    applyOutputFormat,
    applySizeReductionMode,
    applySizeReductionBitrateKbps,
    applySizeReductionSampleRateHz,
    applySizeReductionChannels,
    applyPitchHumMode,
    applyShareTarget,
    applyGraphVoiceRange,
    applyGraphRecordingCondition,
    applyGraphSmoothness,
    applyGraphConnectShortDropouts,
    applyGraphVoiceLock,
    applyVoiceRecordingCountdownSeconds,
  };
}

export function createChorusingSplitButtonStateHandlers(
  getTargetOrd: () => number,
  mutators: ChorusingSplitButtonMutators,
): ChorusingSplitButtonHandlers {
  const {
    setChorusingPauseSeconds,
    setChorusingAutoAdvance,
    setChorusingRepeatCount,
  } = mutators;

  const syncFromState = (state: ChorusingSplitButtonState): void => {
    setChorusingPauseSeconds(state.chorusingPauseSeconds);
    setChorusingAutoAdvance(state.chorusingAutoAdvance);
    setChorusingRepeatCount(state.chorusingRepeatCount);
  };

  return {
    syncFromState,
    applyPauseSeconds: (value: number): void => {
      syncFromState(setChorusingPauseSecondsForField(getTargetOrd(), value));
    },
    applyAutoAdvance: (value: boolean): void => {
      syncFromState(setChorusingAutoAdvanceForField(getTargetOrd(), value));
    },
    applyRepeatCount: (value: number): void => {
      syncFromState(setChorusingRepeatCountForField(getTargetOrd(), value));
    },
  };
}
