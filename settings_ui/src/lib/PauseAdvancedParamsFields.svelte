<script lang="ts">
  import AqeTooltip from "$lib/AqeTooltip.svelte";
  import CommandIcon from "$lib/CommandIcon.svelte";
  import {
    pauseThresholdLabel,
    pauseThresholdMax,
    pauseThresholdMin,
    pauseThresholdStep,
    type PauseDetectionAlgorithmValue,
  } from "$lib/audio-operation-parameters.js";
  import { t } from "$lib/i18n.js";

  interface Props {
    algorithm: PauseDetectionAlgorithmValue;
    compact?: boolean;
    threshold: number;
    minSilenceSeconds: number;
    minSpeechSeconds: number;
    preprocessDenoise: boolean;
    disabled?: boolean;
    onMinSilenceSeconds?: (value: number) => void;
    onMinSpeechSeconds?: (value: number) => void;
    onPreprocessDenoise?: (value: boolean) => void;
    onThreshold?: (value: number) => void;
    testPrefix?: string;
  }

  let {
    algorithm,
    compact = false,
    threshold = $bindable(),
    minSilenceSeconds = $bindable(),
    minSpeechSeconds = $bindable(),
    preprocessDenoise = $bindable(),
    disabled = false,
    onMinSilenceSeconds,
    onMinSpeechSeconds,
    onPreprocessDenoise,
    onThreshold,
    testPrefix = "pause",
  }: Props = $props();

  const thresholdDescriptionKey = $derived(
    algorithm === "silero_vad"
      ? "settings.pause_threshold_probability.help"
      : "settings.pause_threshold_db.help",
  );

</script>

<details
  class:advanced-params-compact={compact}
  class="advanced-params"
  data-testid={`${testPrefix}-advanced-params`}
>
  <summary>{t("settings.pause_advanced_params")}</summary>
  <div class="advanced-params-grid">
    <label>
      <div class="field-label-row">
        <span>{pauseThresholdLabel(algorithm)}</span>
        <AqeTooltip>
          {#snippet trigger({ props })}
            <button
              {...props}
              type="button"
              class="help-icon-button aqe-tooltip-target"
              data-testid={`${testPrefix}-threshold-help`}
              data-aqe-tooltip-content={t(thresholdDescriptionKey)}
              aria-label={`${pauseThresholdLabel(algorithm)} help`}
            >
              <CommandIcon icon="circle-help" size={14} />
            </button>
          {/snippet}
        </AqeTooltip>
      </div>
      <input
        bind:value={threshold}
        data-testid={`${testPrefix}-threshold`}
        disabled={disabled}
        max={pauseThresholdMax(algorithm)}
        min={pauseThresholdMin(algorithm)}
        step={pauseThresholdStep(algorithm)}
        type="number"
        oninput={(event) => onThreshold?.((event.currentTarget as HTMLInputElement).valueAsNumber)}
      />
    </label>
    <label>
      <div class="field-label-row">
        <span>{t("settings.pause_min_silence_seconds")}</span>
        <AqeTooltip>
          {#snippet trigger({ props })}
            <button
              {...props}
              type="button"
              class="help-icon-button aqe-tooltip-target"
              data-testid={`${testPrefix}-min-silence-seconds-help`}
              data-aqe-tooltip-content={t("settings.pause_min_silence_seconds.help")}
              aria-label={`${t("settings.pause_min_silence_seconds")} help`}
            >
              <CommandIcon icon="circle-help" size={14} />
            </button>
          {/snippet}
        </AqeTooltip>
      </div>
      <input
        bind:value={minSilenceSeconds}
        data-testid={`${testPrefix}-min-silence-seconds`}
        disabled={disabled}
        max="10"
        min="0.01"
        step="0.01"
        type="number"
        oninput={(event) => onMinSilenceSeconds?.((event.currentTarget as HTMLInputElement).valueAsNumber)}
      />
    </label>
    <label>
      <div class="field-label-row">
        <span>{t("settings.pause_min_speech_seconds")}</span>
        <AqeTooltip>
          {#snippet trigger({ props })}
            <button
              {...props}
              type="button"
              class="help-icon-button aqe-tooltip-target"
              data-testid={`${testPrefix}-min-speech-seconds-help`}
              data-aqe-tooltip-content={t("settings.pause_min_speech_seconds.help")}
              aria-label={`${t("settings.pause_min_speech_seconds")} help`}
            >
              <CommandIcon icon="circle-help" size={14} />
            </button>
          {/snippet}
        </AqeTooltip>
      </div>
      <input
        bind:value={minSpeechSeconds}
        data-testid={`${testPrefix}-min-speech-seconds`}
        disabled={disabled}
        max="10"
        min="0.01"
        step="0.01"
        type="number"
        oninput={(event) => onMinSpeechSeconds?.((event.currentTarget as HTMLInputElement).valueAsNumber)}
      />
    </label>
    <label class="advanced-params-toggle">
      <input
        bind:checked={preprocessDenoise}
        data-testid={`${testPrefix}-preprocess-denoise`}
        disabled={disabled}
        type="checkbox"
        onchange={(event) => onPreprocessDenoise?.((event.currentTarget as HTMLInputElement).checked)}
      />
      <div class="field-label-row">
        <span>{t("settings.pause_preprocess_denoise")}</span>
        <AqeTooltip>
          {#snippet trigger({ props })}
            <button
              {...props}
              type="button"
              class="help-icon-button aqe-tooltip-target"
              data-testid={`${testPrefix}-preprocess-denoise-help`}
              data-aqe-tooltip-content={t("settings.pause_preprocess_denoise.help")}
              aria-label={`${t("settings.pause_preprocess_denoise")} help`}
            >
              <CommandIcon icon="circle-help" size={14} />
            </button>
          {/snippet}
        </AqeTooltip>
      </div>
    </label>
  </div>
</details>

<style>
  .advanced-params {
    grid-column: 1 / -1;
  }

  summary {
    color: var(--fg-subtle, currentColor);
    cursor: pointer;
    font-size: 0.85rem;
    font-weight: 700;
  }

  .advanced-params-grid {
    display: grid;
    gap: 10px;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    margin-top: 10px;
  }

  label {
    display: grid;
    gap: 6px;
  }

  .field-label-row {
    align-items: center;
    display: flex;
    gap: 6px;
  }

  span {
    color: var(--fg-subtle, currentColor);
    font-size: 0.85rem;
    font-weight: 600;
  }

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

  .advanced-params-toggle {
    align-items: center;
    display: flex;
    gap: 8px;
    min-height: 34px;
  }

  .advanced-params-toggle input {
    min-height: auto;
    width: auto;
  }

  .help-icon-button {
    appearance: none;
    align-items: center;
    background: none;
    border: 0;
    border-radius: 4px;
    box-shadow: none;
    color: var(--fg-subtle, currentColor);
    cursor: help;
    display: inline-flex;
    outline: none;
    padding: 0;
  }

  .help-icon-button:hover {
    background: none;
    border-color: transparent;
    box-shadow: none;
  }

  .help-icon-button:focus-visible {
    outline: 1px solid Highlight;
    outline-offset: 2px;
  }

  .advanced-params-compact summary,
  .advanced-params-compact span {
    font-size: 11px;
  }

  .advanced-params-compact .advanced-params-grid {
    gap: 8px;
    grid-template-columns: repeat(auto-fit, minmax(112px, 1fr));
  }

  .advanced-params-compact label {
    gap: 4px;
  }

  .advanced-params-compact input {
    border-radius: 5px;
    font-size: 11px;
    min-height: 24px;
    padding: 2px 4px;
  }

  .advanced-params-compact .advanced-params-toggle {
    gap: 6px;
    min-height: 24px;
  }
</style>
