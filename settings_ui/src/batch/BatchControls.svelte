<script lang="ts">
  import FieldTooltipTarget from "$lib/FieldTooltipTarget.svelte";
  import { t } from "$lib/i18n.js";
  import UnitNumberInput from "$lib/UnitNumberInput.svelte";
  import { tooltipWithDisabledClarification } from "$lib/disabled-tooltip.js";
  import {
    DPDFNET_ATTENUATION_LIMIT_DB_VALUES,
    formatDpdfnetAggressiveness,
    formatPauseAggressiveness,
    formatOutputFormat,
    formatPauseDetectionAlgorithm,
    pausePreset,
    OUTPUT_FORMAT_VALUES,
  } from "$lib/audio-operation-parameters.js";
  import PauseAdvancedParamsFields from "$lib/PauseAdvancedParamsFields.svelte";
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
  import {
    activeBatchPauseAlgorithm,
    type BatchFormState,
  } from "./batch-state.js";
  import BatchFieldSelectors from "./BatchFieldSelectors.svelte";
  import BatchSizeReductionFields from "./BatchSizeReductionFields.svelte";

  interface Props {
    state: BatchInitialState;
    form: BatchFormState;
    selected: BatchOperationOption | undefined;
    disabled: boolean;
  }

  let { state, form = $bindable(), selected, disabled }: Props = $props();
  const disabledReason = $derived(disabled ? t("tooltip.disabled.batch_running") : undefined);

  function clarifiedTooltip(content: string): string {
    return tooltipWithDisabledClarification(content, disabledReason);
  }

  function applyPausePreset(value: BatchPauseAggressiveness): void {
    const algorithm = activeBatchPauseAlgorithm(form);
    const preset = pausePreset(algorithm, value);
    form.pauseAggressiveness = value;
    if (algorithm === "silero_vad") {
      form.pauseSileroThreshold = preset.threshold;
      form.pauseSileroMinSilenceSeconds = preset.minSilenceSeconds;
      form.pauseSileroMinSpeechSeconds = preset.minSpeechSeconds;
      form.pauseSileroPreprocessDenoise = preset.preprocessDenoise;
      return;
    }
    form.pauseSilencedetectThresholdDb = preset.threshold;
    form.pauseSilencedetectMinSilenceSeconds = preset.minSilenceSeconds;
    form.pauseSilencedetectMinSpeechSeconds = preset.minSpeechSeconds;
    form.pauseSilencedetectPreprocessDenoise = preset.preprocessDenoise;
  }
</script>

<div class="batch-grid">
  <BatchFieldSelectors {state} bind:form {selected} {disabled} />

  {#if selected?.parameter_kind === BatchParameterKind.Speed}
    <label>
      <span>{t("settings.speed_step")}</span>
      <FieldTooltipTarget block content={t("settings.speed_step")} {disabledReason}>
        <UnitNumberInput
          block
          bind:value={form.speedStep}
          disabled={disabled}
          max="5"
          min="1.01"
          step="0.01"
          unit="x"
          unitPosition="prefix"
        />
      </FieldTooltipTarget>
    </label>
  {:else if selected?.parameter_kind === BatchParameterKind.Volume}
    <label>
      <span>{t("settings.volume_step_db")}</span>
      <FieldTooltipTarget block content={t("settings.volume_step_db")} {disabledReason}>
        <UnitNumberInput
          block
          bind:value={form.volumeStepDb}
          disabled={disabled}
          max="40"
          min="1"
          step="0.5"
          unit="dB"
        />
      </FieldTooltipTarget>
    </label>
  {:else if selected?.parameter_kind === BatchParameterKind.Pause}
    <label>
      <span>{t("settings.pause_aggressiveness")}</span>
      <div class="batch-choice-group" role="radiogroup" aria-label={t("settings.pause_aggressiveness")}>
        {#each [BatchPauseAggressiveness.Gentle, BatchPauseAggressiveness.Normal, BatchPauseAggressiveness.Aggressive] as value}
          {@const tooltip = choiceTooltip(formatPauseAggressiveness(value), pauseAggressivenessTooltip(value))}
          <FieldTooltipTarget content={tooltip} {disabledReason}>
            <button
              type="button"
              class="batch-choice-button aqe-tooltip-target"
              disabled={disabled}
              data-testid={`batch-pause-aggressiveness-${value}`}
              data-aqe-tooltip-content={clarifiedTooltip(tooltip)}
              role="radio"
              aria-checked={form.pauseAggressiveness === value ? "true" : "false"}
              onclick={() => applyPausePreset(value)}
            >
              {formatPauseAggressiveness(value)}
            </button>
          </FieldTooltipTarget>
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
        {#each [BatchPauseDetectionAlgorithm.Silencedetect, BatchPauseDetectionAlgorithm.SileroVad] as value}
          {@const tooltip = choiceTooltip(
            formatPauseDetectionAlgorithm(value),
            pauseDetectionAlgorithmTooltip(value),
          )}
          <FieldTooltipTarget content={tooltip} {disabledReason}>
            <button
              type="button"
              class="batch-choice-button aqe-tooltip-target"
              disabled={disabled}
              data-testid={`batch-pause-detection-algorithm-${value}`}
              data-aqe-tooltip-content={clarifiedTooltip(tooltip)}
              role="radio"
              aria-checked={form.pauseDetectionAlgorithm === value ? "true" : "false"}
              onclick={() => (form.pauseDetectionAlgorithm = value)}
            >
              {formatPauseDetectionAlgorithm(value)}
            </button>
          </FieldTooltipTarget>
        {/each}
      </div>
    </label>
    {#if activeBatchPauseAlgorithm(form) === "silero_vad"}
      <PauseAdvancedParamsFields
        algorithm="silero_vad"
        bind:threshold={form.pauseSileroThreshold}
        bind:minSilenceSeconds={form.pauseSileroMinSilenceSeconds}
        bind:minSpeechSeconds={form.pauseSileroMinSpeechSeconds}
        bind:preprocessDenoise={form.pauseSileroPreprocessDenoise}
        {disabled}
        {disabledReason}
        testPrefix="batch-pause"
      />
    {:else}
      <PauseAdvancedParamsFields
        algorithm="silencedetect"
        bind:threshold={form.pauseSilencedetectThresholdDb}
        bind:minSilenceSeconds={form.pauseSilencedetectMinSilenceSeconds}
        bind:minSpeechSeconds={form.pauseSilencedetectMinSpeechSeconds}
        bind:preprocessDenoise={form.pauseSilencedetectPreprocessDenoise}
        {disabled}
        {disabledReason}
        testPrefix="batch-pause"
      />
    {/if}
  {:else if selected?.parameter_kind === BatchParameterKind.Format}
    <label>
      <span>{t("settings.output_format")}</span>
      <FieldTooltipTarget block content={t("settings.output_format")} {disabledReason}>
        <select bind:value={form.targetFormat} data-testid="batch-output-format" disabled={disabled}>
          {#each OUTPUT_FORMAT_VALUES as format}
            <option value={format}>{formatOutputFormat(format)}</option>
          {/each}
        </select>
      </FieldTooltipTarget>
    </label>
  {:else if selected?.parameter_kind === BatchParameterKind.SizeReduction}
    <BatchSizeReductionFields bind:form {disabled} {disabledReason} />
  {:else if selected?.parameter_kind === BatchParameterKind.Denoise}
    <label>
      <span>{t("batch.suppressor")}</span>
      <div class="batch-choice-group batch-choice-group-wrap" role="radiogroup" aria-label={t("batch.suppressor")}>
        {#each [DenoiseAlgorithm.Standard, DenoiseAlgorithm.Rnnoise, DenoiseAlgorithm.Dpdfnet, DenoiseAlgorithm.VoiceOnly] as value}
          {@const tooltip = choiceTooltip(
            t(`settings.denoise_algorithm.${value}`),
            denoiseAlgorithmTooltip(value),
          )}
          <FieldTooltipTarget content={tooltip} {disabledReason}>
            <button
              type="button"
              class="batch-choice-button aqe-tooltip-target"
              disabled={disabled}
              data-testid={`batch-denoise-algorithm-${value}`}
              data-aqe-tooltip-content={clarifiedTooltip(tooltip)}
              role="radio"
              aria-checked={form.denoiseAlgorithm === value ? "true" : "false"}
              onclick={() => (form.denoiseAlgorithm = value)}
            >
              {t(`settings.denoise_algorithm.${value}`)}
            </button>
          </FieldTooltipTarget>
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
            {@const tooltip = choiceTooltip(
              formatDpdfnetAggressiveness(value),
              dpdfnetAggressivenessTooltip(value),
            )}
            <FieldTooltipTarget content={tooltip} {disabledReason}>
              <button
                type="button"
                class="batch-choice-button aqe-tooltip-target"
                disabled={disabled}
                data-testid={`batch-dpdfnet-attn-limit-db-${value}`}
                data-aqe-tooltip-content={clarifiedTooltip(tooltip)}
                role="radio"
                aria-checked={form.dpdfnetAttnLimitDb === value ? "true" : "false"}
                onclick={() => (form.dpdfnetAttnLimitDb = value)}
              >
                {formatDpdfnetAggressiveness(value)}
              </button>
            </FieldTooltipTarget>
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
    font-size: 11px;
    font-weight: 700;
  }

  select {
    background: var(--canvas-elevated, Field);
    border: 1px solid var(--border, ButtonBorder);
    border-radius: 5px;
    box-sizing: border-box;
    color: var(--fg, FieldText);
    font: inherit;
    font-size: 11px;
    min-height: 24px;
    padding: 2px 4px;
    width: 100%;
  }

  select {
    border-radius: 6px;
    min-height: 30px;
    padding: 4px 8px;
  }

  select:disabled {
    opacity: 0.7;
  }

  .batch-choice-group {
    display: inline-flex;
    flex-wrap: nowrap;
    gap: 5px;
    min-width: 0;
  }

  .batch-choice-group-wrap {
    flex-wrap: wrap;
  }

  .batch-choice-button {
    align-items: center;
    appearance: none;
    background: color-mix(in srgb, var(--canvas-elevated, ButtonFace) 88%, transparent);
    border: 1px solid color-mix(in srgb, var(--border, ButtonBorder) 86%, transparent);
    border-radius: 7px;
    color: var(--fg, ButtonText);
    cursor: pointer;
    display: inline-flex;
    font: inherit;
    font-size: 11px;
    font-weight: 400;
    min-height: 24px;
    padding: 3px 6px;
  }

  .batch-choice-button:disabled {
    cursor: not-allowed;
    opacity: 0.7;
  }
</style>
