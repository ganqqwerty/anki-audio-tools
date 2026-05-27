<script lang="ts">
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
</script>

<details class="advanced-params" data-testid={`${testPrefix}-advanced-params`}>
  <summary>{t("settings.pause_advanced_params")}</summary>
  <div class="advanced-params-grid">
    <label>
      <span>{pauseThresholdLabel(algorithm)}</span>
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
      <span>{t("settings.pause_min_silence_seconds")}</span>
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
      <span>{t("settings.pause_min_speech_seconds")}</span>
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
      <span>{t("settings.pause_preprocess_denoise")}</span>
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
</style>
