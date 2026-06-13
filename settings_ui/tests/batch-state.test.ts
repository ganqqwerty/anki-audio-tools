import { describe, expect, it } from "vitest";

import {
  FALLBACK_BATCH_INITIAL_STATE,
  batchStartRequest,
  canStartBatch,
  selectedOperation,
  shouldShowTargetField,
} from "../src/batch/batch-state.js";
import {
  BatchOperationName,
  BatchParameterKind,
  BatchParameterName,
  BatchPauseAggressiveness,
  BatchPauseDetectionAlgorithm,
  DenoiseAlgorithm,
} from "../src/lib/types.js";
import type { BatchFormState } from "../src/batch/batch-state.js";

function form(overrides: Partial<BatchFormState> = {}): BatchFormState {
  return {
    operation: BatchOperationName.Graph,
    sourceField: "Audio",
    targetField: "Image",
    presetId: "clean_graph",
    audioTargetField: "Processed",
    graphTargetField: "Image",
    speedStep: 1.5,
    volumeStepDb: 6,
    pauseAggressiveness: BatchPauseAggressiveness.Aggressive,
    pauseDetectionAlgorithm: BatchPauseDetectionAlgorithm.Silencedetect,
    pauseSilencedetectThresholdDb: -52,
    pauseSilencedetectMinSilenceSeconds: 0.14,
    pauseSilencedetectMinSpeechSeconds: 0.04,
    pauseSilencedetectPreprocessDenoise: true,
    pauseSileroThreshold: 0.85,
    pauseSileroMinSilenceSeconds: 0.15,
    pauseSileroMinSpeechSeconds: 0.04,
    pauseSileroPreprocessDenoise: false,
    denoiseAlgorithm: DenoiseAlgorithm.Standard,
    dpdfnetAttnLimitDb: 12,
    targetFormat: "mp3",
    sizeReductionMode: "normal",
    sizeReductionBitrateKbps: 64,
    sizeReductionSampleRateHz: 32000,
    sizeReductionChannels: 1,
    ...overrides,
  };
}

describe("batch-state", () => {
  it("selects the current operation and target visibility", () => {
    const graph = selectedOperation(FALLBACK_BATCH_INITIAL_STATE, BatchOperationName.Graph);
    const faster = selectedOperation(FALLBACK_BATCH_INITIAL_STATE, BatchOperationName.Faster);

    expect(graph?.requires_target_field).toBe(true);
    expect(faster?.requires_target_field).toBe(false);
    expect(shouldShowTargetField(graph)).toBe(true);
    expect(shouldShowTargetField(faster)).toBe(false);
  });

  it("requires a source field and any target field requested by metadata", () => {
    const graph = selectedOperation(FALLBACK_BATCH_INITIAL_STATE, BatchOperationName.Graph);
    const faster = selectedOperation(FALLBACK_BATCH_INITIAL_STATE, BatchOperationName.Faster);

    expect(
      canStartBatch(
        form({
          operation: BatchOperationName.Graph,
        }),
        graph,
      ),
    ).toBe(true);
    expect(
      canStartBatch(
        form({
          operation: BatchOperationName.Graph,
          targetField: "",
        }),
        graph,
      ),
    ).toBe(false);
    expect(
      canStartBatch(
        form({
          operation: BatchOperationName.Faster,
          targetField: "",
        }),
        faster,
      ),
    ).toBe(true);
  });

  it("requires preset-specific target fields only when the selected preset produces them", () => {
    const operation = {
      operation: BatchOperationName.Preset,
      label: "Preset",
      requires_target_field: false,
      parameter_kind: BatchParameterKind.Preset,
      parameter_name: BatchParameterName.PresetID,
    };
    const audioAndGraph = {
      id: "clean_graph",
      name: "Clean + graph",
      has_transforms: true,
      graph_enabled: true,
    };
    const graphOnly = {
      id: "graph_only",
      name: "Graph only",
      has_transforms: false,
      graph_enabled: true,
    };

    expect(
      canStartBatch(
        form({ operation: BatchOperationName.Preset }),
        operation,
        audioAndGraph,
      ),
    ).toBe(true);
    expect(
      canStartBatch(
        form({ operation: BatchOperationName.Preset, audioTargetField: "" }),
        operation,
        audioAndGraph,
      ),
    ).toBe(false);
    expect(
      canStartBatch(
        form({ operation: BatchOperationName.Preset, audioTargetField: "" }),
        operation,
        graphOnly,
      ),
    ).toBe(true);
    expect(
      canStartBatch(
        form({ operation: BatchOperationName.Preset, graphTargetField: "" }),
        operation,
        graphOnly,
      ),
    ).toBe(false);
  });

  it("builds graph start requests with target field and no parameters", () => {
    const graph = selectedOperation(FALLBACK_BATCH_INITIAL_STATE, BatchOperationName.Graph);
    expect(
      batchStartRequest(form({
        operation: BatchOperationName.Graph,
      }), graph),
    ).toEqual({
      operation: BatchOperationName.Graph,
      source_field: "Audio",
      target_field: "Image",
      parameters: {},
    });
  });

  it("builds transform start requests with only the active parameter", () => {
    const faster = selectedOperation(FALLBACK_BATCH_INITIAL_STATE, BatchOperationName.Faster);
    const pause = selectedOperation(FALLBACK_BATCH_INITIAL_STATE, BatchOperationName.RemovePauses);
    const denoise = selectedOperation(FALLBACK_BATCH_INITIAL_STATE, BatchOperationName.Denoise);
    const convert = selectedOperation(FALLBACK_BATCH_INITIAL_STATE, BatchOperationName.Convert);
    const reduceSize = selectedOperation(FALLBACK_BATCH_INITIAL_STATE, BatchOperationName.ReduceSize);
    expect(
      batchStartRequest(form({
        operation: BatchOperationName.Faster,
        speedStep: 2,
      }), faster),
    ).toEqual({
      operation: BatchOperationName.Faster,
      source_field: "Audio",
      target_field: null,
      parameters: { speed_step: 2 },
    });

    expect(
      batchStartRequest(form({
        operation: BatchOperationName.RemovePauses,
        pauseAggressiveness: BatchPauseAggressiveness.Gentle,
        pauseSilencedetectThresholdDb: -42,
        pauseSilencedetectMinSilenceSeconds: 0.45,
        pauseSilencedetectMinSpeechSeconds: 0.12,
      }), pause),
    ).toEqual({
      operation: BatchOperationName.RemovePauses,
      source_field: "Audio",
      target_field: null,
      parameters: {
        pause_aggressiveness: "gentle",
        pause_detection_algorithm: "silencedetect",
        pause_min_silence_seconds: 0.45,
        pause_min_speech_seconds: 0.12,
        pause_preprocess_denoise: true,
        pause_threshold: -42,
      },
    });

    expect(
      batchStartRequest(form({
        operation: BatchOperationName.Denoise,
        pauseAggressiveness: BatchPauseAggressiveness.Gentle,
        denoiseAlgorithm: DenoiseAlgorithm.Dpdfnet,
        dpdfnetAttnLimitDb: 18,
      }), denoise),
    ).toEqual({
      operation: BatchOperationName.Denoise,
      source_field: "Audio",
      target_field: null,
      parameters: { denoise_algorithm: "dpdfnet", dpdfnet_attn_limit_db: 18 },
    });

    expect(
      batchStartRequest(form({
        operation: BatchOperationName.Convert,
        pauseAggressiveness: BatchPauseAggressiveness.Gentle,
        targetFormat: "flac",
      }), convert),
    ).toEqual({
      operation: BatchOperationName.Convert,
      source_field: "Audio",
      target_field: null,
      parameters: { target_format: "flac" },
    });

    expect(
      batchStartRequest(form({
        operation: BatchOperationName.ReduceSize,
        sizeReductionMode: "aggressive",
        sizeReductionBitrateKbps: 40,
        sizeReductionSampleRateHz: 22050,
        sizeReductionChannels: 1,
      }), reduceSize),
    ).toEqual({
      operation: BatchOperationName.ReduceSize,
      source_field: "Audio",
      target_field: null,
      parameters: {
        size_reduction_bitrate_kbps: 40,
        size_reduction_channels: 1,
        size_reduction_mode: "aggressive",
        size_reduction_sample_rate_hz: 22050,
      },
    });
  });

  it("builds preset start requests with conditional target fields", () => {
    const operation = {
      operation: BatchOperationName.Preset,
      label: "Preset",
      requires_target_field: false,
      parameter_kind: BatchParameterKind.Preset,
      parameter_name: BatchParameterName.PresetID,
    };
    const preset = {
      id: "clean_graph",
      name: "Clean + graph",
      has_transforms: true,
      graph_enabled: true,
    };

    expect(
      batchStartRequest(form({ operation: BatchOperationName.Preset }), operation, preset),
    ).toEqual({
      operation: BatchOperationName.Preset,
      source_field: "Audio",
      target_field: null,
      preset_id: "clean_graph",
      audio_target_field: "Processed",
      graph_target_field: "Image",
      parameters: {},
    });
  });
});
