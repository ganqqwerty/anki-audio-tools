import { describe, expect, it } from "vitest";

import {
  FALLBACK_BATCH_INITIAL_STATE,
  batchStartRequest,
  canStartBatch,
  selectedOperation,
  shouldShowTargetField,
} from "../src/batch/batch-state.js";
import { BatchOperationName, BatchPauseAggressiveness, DenoiseAlgorithm } from "../src/lib/types.js";

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
        {
          operation: BatchOperationName.Graph,
          sourceField: "Audio",
          targetField: "Image",
          speedStep: 0.1,
          volumeStepDb: 6,
          pauseAggressiveness: BatchPauseAggressiveness.Aggressive,
          denoiseAlgorithm: DenoiseAlgorithm.Standard,
          dpdfnetAttnLimitDb: 12,
        },
        graph,
      ),
    ).toBe(true);
    expect(
      canStartBatch(
        {
          operation: BatchOperationName.Graph,
          sourceField: "Audio",
          targetField: "",
          speedStep: 0.1,
          volumeStepDb: 6,
          pauseAggressiveness: BatchPauseAggressiveness.Aggressive,
          denoiseAlgorithm: DenoiseAlgorithm.Standard,
          dpdfnetAttnLimitDb: 12,
        },
        graph,
      ),
    ).toBe(false);
    expect(
      canStartBatch(
        {
          operation: BatchOperationName.Faster,
          sourceField: "Audio",
          targetField: "",
          speedStep: 0.1,
          volumeStepDb: 6,
          pauseAggressiveness: BatchPauseAggressiveness.Aggressive,
          denoiseAlgorithm: DenoiseAlgorithm.Standard,
          dpdfnetAttnLimitDb: 12,
        },
        faster,
      ),
    ).toBe(true);
  });

  it("builds graph start requests with target field and no parameters", () => {
    const graph = selectedOperation(FALLBACK_BATCH_INITIAL_STATE, BatchOperationName.Graph);
    expect(
      batchStartRequest({
        operation: BatchOperationName.Graph,
        sourceField: "Audio",
        targetField: "Image",
        speedStep: 0.1,
        volumeStepDb: 6,
        pauseAggressiveness: BatchPauseAggressiveness.Aggressive,
        denoiseAlgorithm: DenoiseAlgorithm.Standard,
        dpdfnetAttnLimitDb: 12,
      }, graph),
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
    expect(
      batchStartRequest({
        operation: BatchOperationName.Faster,
        sourceField: "Audio",
        targetField: "Image",
        speedStep: 0.2,
        volumeStepDb: 6,
        pauseAggressiveness: BatchPauseAggressiveness.Aggressive,
        denoiseAlgorithm: DenoiseAlgorithm.Standard,
        dpdfnetAttnLimitDb: 12,
      }, faster),
    ).toEqual({
      operation: BatchOperationName.Faster,
      source_field: "Audio",
      target_field: null,
      parameters: { speed_step: 0.2 },
    });

    expect(
      batchStartRequest({
        operation: BatchOperationName.RemovePauses,
        sourceField: "Audio",
        targetField: "Image",
        speedStep: 0.2,
        volumeStepDb: 6,
        pauseAggressiveness: BatchPauseAggressiveness.Gentle,
        denoiseAlgorithm: DenoiseAlgorithm.Standard,
        dpdfnetAttnLimitDb: 12,
      }, pause),
    ).toEqual({
      operation: BatchOperationName.RemovePauses,
      source_field: "Audio",
      target_field: null,
      parameters: { pause_aggressiveness: "gentle" },
    });

    expect(
      batchStartRequest({
        operation: BatchOperationName.Denoise,
        sourceField: "Audio",
        targetField: "Image",
        speedStep: 0.2,
        volumeStepDb: 6,
        pauseAggressiveness: BatchPauseAggressiveness.Gentle,
        denoiseAlgorithm: DenoiseAlgorithm.Dpdfnet,
        dpdfnetAttnLimitDb: 18,
      }, denoise),
    ).toEqual({
      operation: BatchOperationName.Denoise,
      source_field: "Audio",
      target_field: null,
      parameters: { denoise_algorithm: "dpdfnet", dpdfnet_attn_limit_db: 18 },
    });
  });
});
