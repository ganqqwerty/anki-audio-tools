<script lang="ts">
  import AqeTooltip from "$lib/AqeTooltip.svelte";
  import { t } from "$lib/i18n.js";
  import {
    DPDFNET_ATTENUATION_LIMIT_DB_VALUES,
    formatDpdfnetAggressiveness,
    formatPauseAggressiveness,
    formatOutputFormat,
    formatPauseDetectionAlgorithm,
    OUTPUT_FORMAT_VALUES,
  } from "$lib/audio-operation-parameters.js";
  import {
    choiceTooltip,
    denoiseAlgorithmTooltip,
    dpdfnetAggressivenessTooltip,
    pauseAggressivenessTooltip,
    pauseDetectionAlgorithmTooltip,
  } from "$lib/audio-option-tooltips.js";
  import {
    BatchParameterKind,
    BatchPauseAggressiveness,
    BatchPauseDetectionAlgorithm,
    DenoiseAlgorithm,
  } from "$lib/types.js";
  import type { BatchInitialState, BatchOperationOption } from "$lib/types.js";
  import type { BatchFormState } from "./batch-state.js";

  interface Props {
    state: BatchInitialState;
    form: BatchFormState;
    selected: BatchOperationOption | undefined;
    disabled: boolean;
  }

  let { state, form = $bindable(), selected, disabled }: Props = $props();
</script>

<div class="batch-grid">
  <label>
    <span>{t("batch.operation")}</span>
    <select bind:value={form.operation} data-testid="batch-operation" disabled={disabled}>
      {#each state.operations as operation}
        <option value={operation.operation}>{operation.label}</option>
      {/each}
    </select>
  </label>

  <label>
    <span>{t("batch.source_field")}</span>
    <select bind:value={form.sourceField} disabled={disabled}>
      {#each state.field_groups as group}
        {#each group.fields as field}
          <option value={field}>{group.notetype_name} / {field}</option>
        {/each}
      {/each}
    </select>
  </label>

  {#if selected?.requires_target_field}
    <label>
      <span>{t("batch.target_field")}</span>
      <select bind:value={form.targetField} disabled={disabled}>
        {#each state.field_groups as group}
          {#each group.fields as field}
            <option value={field}>{group.notetype_name} / {field}</option>
          {/each}
        {/each}
      </select>
    </label>
  {/if}

  {#if selected?.parameter_kind === BatchParameterKind.Speed}
    <label>
      <span>{t("settings.speed_step")}</span>
      <input bind:value={form.speedStep} disabled={disabled} max="5" min="1.01" step="0.01" type="number" />
    </label>
  {:else if selected?.parameter_kind === BatchParameterKind.Volume}
    <label>
      <span>{t("settings.volume_step_db")}</span>
      <input bind:value={form.volumeStepDb} disabled={disabled} max="40" min="1" step="0.5" type="number" />
    </label>
  {:else if selected?.parameter_kind === BatchParameterKind.Pause}
    <label>
      <span>{t("settings.pause_aggressiveness")}</span>
      <div class="batch-choice-group" role="radiogroup" aria-label={t("settings.pause_aggressiveness")}>
        {#each [BatchPauseAggressiveness.Gentle, BatchPauseAggressiveness.Normal, BatchPauseAggressiveness.Aggressive] as value}
          <AqeTooltip>
            {#snippet trigger({ props })}
              <button
                {...props}
                type="button"
                class="batch-choice-button aqe-tooltip-target"
                disabled={disabled}
                data-testid={`batch-pause-aggressiveness-${value}`}
                data-aqe-tooltip-content={choiceTooltip(formatPauseAggressiveness(value), pauseAggressivenessTooltip(value))}
                role="radio"
                aria-checked={form.pauseAggressiveness === value ? "true" : "false"}
                onclick={() => (form.pauseAggressiveness = value)}
              >
                {formatPauseAggressiveness(value)}
              </button>
            {/snippet}
          </AqeTooltip>
        {/each}
      </div>
    </label>
    <label>
      <span>{t("settings.pause_detection_algorithm")}</span>
      <div
        class="batch-choice-group"
        data-testid="batch-pause-detection-algorithm"
        role="radiogroup"
        aria-label={t("settings.pause_detection_algorithm")}
      >
        {#each [BatchPauseDetectionAlgorithm.DeepFilter, BatchPauseDetectionAlgorithm.SileroVad] as value}
          <AqeTooltip>
            {#snippet trigger({ props })}
              <button
                {...props}
                type="button"
                class="batch-choice-button aqe-tooltip-target"
                disabled={disabled}
                data-testid={`batch-pause-detection-algorithm-${value}`}
                data-aqe-tooltip-content={choiceTooltip(
                  formatPauseDetectionAlgorithm(value),
                  pauseDetectionAlgorithmTooltip(value),
                )}
                role="radio"
                aria-checked={form.pauseDetectionAlgorithm === value ? "true" : "false"}
                onclick={() => (form.pauseDetectionAlgorithm = value)}
              >
                {formatPauseDetectionAlgorithm(value)}
              </button>
            {/snippet}
          </AqeTooltip>
        {/each}
      </div>
    </label>
  {:else if selected?.parameter_kind === BatchParameterKind.Format}
    <label>
      <span>{t("settings.output_format")}</span>
      <select bind:value={form.targetFormat} data-testid="batch-output-format" disabled={disabled}>
        {#each OUTPUT_FORMAT_VALUES as format}
          <option value={format}>{formatOutputFormat(format)}</option>
        {/each}
      </select>
    </label>
  {:else if selected?.parameter_kind === BatchParameterKind.Denoise}
    <label>
      <span>{t("batch.suppressor")}</span>
      <div class="batch-choice-group batch-choice-group-wrap" role="radiogroup" aria-label={t("batch.suppressor")}>
        {#each [DenoiseAlgorithm.Standard, DenoiseAlgorithm.Rnnoise, DenoiseAlgorithm.Dpdfnet, DenoiseAlgorithm.VoiceOnly] as value}
          <AqeTooltip>
            {#snippet trigger({ props })}
              <button
                {...props}
                type="button"
                class="batch-choice-button aqe-tooltip-target"
                disabled={disabled}
                data-testid={`batch-denoise-algorithm-${value}`}
                data-aqe-tooltip-content={choiceTooltip(
                  t(`settings.denoise_algorithm.${value}`),
                  denoiseAlgorithmTooltip(value),
                )}
                role="radio"
                aria-checked={form.denoiseAlgorithm === value ? "true" : "false"}
                onclick={() => (form.denoiseAlgorithm = value)}
              >
                {t(`settings.denoise_algorithm.${value}`)}
              </button>
            {/snippet}
          </AqeTooltip>
        {/each}
      </div>
    </label>
    {#if form.denoiseAlgorithm === DenoiseAlgorithm.Dpdfnet}
      <label>
        <span>{t("settings.dpdfnet_attn_limit_db")}</span>
        <div
          class="batch-choice-group"
          data-testid="batch-dpdfnet-attn-limit-db"
          role="radiogroup"
          aria-label={t("settings.dpdfnet_attn_limit_db")}
        >
          {#each DPDFNET_ATTENUATION_LIMIT_DB_VALUES as value}
            <AqeTooltip>
              {#snippet trigger({ props })}
                <button
                  {...props}
                  type="button"
                  class="batch-choice-button aqe-tooltip-target"
                  disabled={disabled}
                  data-testid={`batch-dpdfnet-attn-limit-db-${value}`}
                  data-aqe-tooltip-content={choiceTooltip(
                    formatDpdfnetAggressiveness(value),
                    dpdfnetAggressivenessTooltip(value),
                  )}
                  role="radio"
                  aria-checked={form.dpdfnetAttnLimitDb === value ? "true" : "false"}
                  onclick={() => (form.dpdfnetAttnLimitDb = value)}
                >
                  {formatDpdfnetAggressiveness(value)}
                </button>
              {/snippet}
            </AqeTooltip>
          {/each}
        </div>
      </label>
    {/if}
  {/if}
</div>

<style>
  .batch-grid {
    display: grid;
    gap: 14px;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  }

  label {
    display: grid;
    gap: 6px;
  }

  span {
    color: var(--fg-subtle, currentColor);
    font-size: 0.85rem;
    font-weight: 600;
  }

  select,
  input {
    background: var(--canvas-elevated, Field);
    border: 1px solid var(--border, ButtonBorder);
    border-radius: 6px;
    box-sizing: border-box;
    color: var(--fg, FieldText);
    font: inherit;
    min-height: 34px;
    padding: 6px 8px;
    width: 100%;
  }

  select:disabled,
  input:disabled {
    opacity: 0.7;
  }

  .batch-choice-group {
    display: inline-flex;
    flex-wrap: nowrap;
    gap: 6px;
    min-width: 0;
  }

  .batch-choice-group-wrap {
    flex-wrap: wrap;
  }

  .batch-choice-button {
    background: var(--canvas-elevated, ButtonFace);
    border: 1px solid var(--border, ButtonBorder);
    border-radius: 6px;
    color: var(--fg, ButtonText);
    cursor: pointer;
    font: inherit;
    min-height: 34px;
    padding: 6px 10px;
  }

  .batch-choice-button[aria-checked="true"] {
    box-shadow: inset 0 0 0 1px ButtonBorder;
    font-weight: 700;
  }

  .batch-choice-button:disabled {
    cursor: not-allowed;
    opacity: 0.7;
  }
</style>
