import {
  BatchOperationName,
  BatchParameterKind,
  BatchParameterName,
  BatchPauseAggressiveness,
  BatchPauseDetectionAlgorithm,
  DenoiseAlgorithm,
  Direction,
  OutputFormat,
} from "$lib/types.js";
import {
  clampDpdfnetAttnLimitDb,
  clampSpeedStep,
  clampVolumeStepDb,
  outputFormatOrDefault,
  type OutputFormatValue,
} from "$lib/audio-operation-parameters.js";
import type {
  BatchInitialState,
  BatchOperationOption,
  BatchStartRequest,
} from "$lib/types.js";

export interface BatchFormState {
  operation: BatchOperationName;
  sourceField: string;
  targetField: string;
  speedStep: number;
  volumeStepDb: number;
  pauseAggressiveness: BatchPauseAggressiveness;
  pauseDetectionAlgorithm: BatchPauseDetectionAlgorithm;
  denoiseAlgorithm: DenoiseAlgorithm;
  dpdfnetAttnLimitDb: number;
  targetFormat: OutputFormatValue;
}

export const FALLBACK_BATCH_INITIAL_STATE: BatchInitialState = {
  note_count: 0,
  operations: [
    {
      operation: BatchOperationName.Graph,
      label: "Graph",
      requires_target_field: true,
      parameter_kind: BatchParameterKind.None,
      parameter_name: BatchParameterName.None,
    },
    {
      operation: BatchOperationName.Convert,
      label: "Convert",
      requires_target_field: false,
      parameter_kind: BatchParameterKind.Format,
      parameter_name: BatchParameterName.TargetFormat,
    },
    {
      operation: BatchOperationName.Denoise,
      label: "Denoise",
      requires_target_field: false,
      parameter_kind: BatchParameterKind.Denoise,
      parameter_name: BatchParameterName.DenoiseAlgorithm,
    },
    {
      operation: BatchOperationName.RemovePauses,
      label: "Shorten Pauses",
      requires_target_field: false,
      parameter_kind: BatchParameterKind.Pause,
      parameter_name: BatchParameterName.PauseAggressiveness,
    },
    {
      operation: BatchOperationName.Slower,
      label: "Slower",
      requires_target_field: false,
      parameter_kind: BatchParameterKind.Speed,
      parameter_name: BatchParameterName.SpeedStep,
    },
    {
      operation: BatchOperationName.Faster,
      label: "Faster",
      requires_target_field: false,
      parameter_kind: BatchParameterKind.Speed,
      parameter_name: BatchParameterName.SpeedStep,
    },
    {
      operation: BatchOperationName.VolumeDown,
      label: "Volume -",
      requires_target_field: false,
      parameter_kind: BatchParameterKind.Volume,
      parameter_name: BatchParameterName.VolumeStepDB,
    },
    {
      operation: BatchOperationName.VolumeUp,
      label: "Volume +",
      requires_target_field: false,
      parameter_kind: BatchParameterKind.Volume,
      parameter_name: BatchParameterName.VolumeStepDB,
    },
  ],
  field_groups: [],
  defaults: {
    speed_step: 1.5,
    volume_step_db: 15,
    pause_aggressiveness: BatchPauseAggressiveness.Normal,
    pause_detection_algorithm: BatchPauseDetectionAlgorithm.DeepFilter,
    denoise_algorithm: DenoiseAlgorithm.Standard,
    dpdfnet_attn_limit_db: 12,
    output_format: OutputFormat.Mp3,
  },
  locale: "en",
  direction: Direction.LTR,
  messages: {},
};

export function initialBatchState(): BatchInitialState {
  return window.__AQE_BATCH_INITIAL_STATE__ ?? FALLBACK_BATCH_INITIAL_STATE;
}

export function initialFormState(state: BatchInitialState): BatchFormState {
  const firstOperation = state.operations[0]?.operation ?? BatchOperationName.Graph;
  const firstField = state.field_groups[0]?.fields[0] ?? "";
  return {
    operation: firstOperation,
    sourceField: firstField,
    targetField: firstField,
    speedStep: state.defaults.speed_step,
    volumeStepDb: state.defaults.volume_step_db,
    pauseAggressiveness: state.defaults.pause_aggressiveness,
    pauseDetectionAlgorithm: state.defaults.pause_detection_algorithm,
    denoiseAlgorithm: state.defaults.denoise_algorithm,
    dpdfnetAttnLimitDb: clampDpdfnetAttnLimitDb(state.defaults.dpdfnet_attn_limit_db),
    targetFormat: outputFormatOrDefault(state.defaults.output_format),
  };
}

export function selectedOperation(
  state: BatchInitialState,
  operation: BatchOperationName,
): BatchOperationOption | undefined {
  return state.operations.find((item) => item.operation === operation);
}

export function shouldShowTargetField(operation: BatchOperationOption | undefined): boolean {
  return operation?.requires_target_field === true;
}

export function canStartBatch(form: BatchFormState, operation: BatchOperationOption | undefined): boolean {
  if (operation === undefined || form.sourceField.length === 0) return false;
  if (operation.requires_target_field && form.targetField.length === 0) return false;
  return true;
}

export function batchStartRequest(
  form: BatchFormState,
  operation: BatchOperationOption | undefined,
): BatchStartRequest {
  const request: BatchStartRequest = {
    operation: form.operation,
    source_field: form.sourceField,
    target_field: operation?.requires_target_field === true ? form.targetField : null,
    parameters: {},
  };
  if (operation?.parameter_name === BatchParameterName.SpeedStep) {
    request.parameters.speed_step = clampSpeedStep(form.speedStep);
  }
  if (operation?.parameter_name === BatchParameterName.VolumeStepDB) {
    request.parameters.volume_step_db = clampVolumeStepDb(form.volumeStepDb);
  }
  if (operation?.parameter_name === BatchParameterName.PauseAggressiveness) {
    request.parameters.pause_aggressiveness = form.pauseAggressiveness;
    request.parameters.pause_detection_algorithm = form.pauseDetectionAlgorithm;
  }
  if (operation?.parameter_name === BatchParameterName.DenoiseAlgorithm) {
    request.parameters.denoise_algorithm = form.denoiseAlgorithm;
    if (form.denoiseAlgorithm === DenoiseAlgorithm.Dpdfnet) {
      request.parameters.dpdfnet_attn_limit_db = clampDpdfnetAttnLimitDb(form.dpdfnetAttnLimitDb);
    }
  }
  if (operation?.parameter_name === BatchParameterName.TargetFormat) {
    request.parameters.target_format = outputFormatOrDefault(form.targetFormat) as OutputFormat;
  }
  return request;
}

declare global {
  interface Window {
    __AQE_BATCH_INITIAL_STATE__?: BatchInitialState;
  }
}
