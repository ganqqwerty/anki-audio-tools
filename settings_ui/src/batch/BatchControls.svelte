<script lang="ts">
  import AqeTooltip from "$lib/AqeTooltip.svelte";
  import { t } from "$lib/i18n.js";
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
  import { activeBatchPauseAlgorithm, type BatchFormState } from "./batch-state.js";
  import BatchFieldSelectors from "./BatchFieldSelectors.svelte";

  interface Props {
    state: BatchInitialState;
    form: BatchFormState;
    selected: BatchOperationOption | undefined;
    disabled: boolean;
  }

  let { state, form = $bindable(), selected, disabled }: Props = $props();

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
                onclick={() => applyPausePreset(value)}
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
        {#each [BatchPauseDetectionAlgorithm.Silencedetect, BatchPauseDetectionAlgorithm.SileroVad] as value}
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
    {#if activeBatchPauseAlgorithm(form) === "silero_vad"}
      <PauseAdvancedParamsFields
        algorithm="silero_vad"
        bind:threshold={form.pauseSileroThreshold}
        bind:minSilenceSeconds={form.pauseSileroMinSilenceSeconds}
        bind:minSpeechSeconds={form.pauseSileroMinSpeechSeconds}
        bind:preprocessDenoise={form.pauseSileroPreprocessDenoise}
        {disabled}
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
        testPrefix="batch-pause"
      />
    {/if}
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
    font-size: 11px;
    font-weight: 700;
  }

  select,
  input {
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

  select:disabled,
  input:disabled {
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
    background: var(--canvas-elevated, ButtonFace);
    border: 1px solid var(--border, ButtonBorder);
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

  .batch-choice-button:hover {
    text-decoration: none;
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
