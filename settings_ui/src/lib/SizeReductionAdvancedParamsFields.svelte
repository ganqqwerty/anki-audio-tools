<script lang="ts">
  import AqeTooltip from "$lib/AqeTooltip.svelte";
  import CommandIcon from "$lib/CommandIcon.svelte";
  import FieldTooltipTarget from "$lib/FieldTooltipTarget.svelte";
  import UnitNumberInput from "$lib/UnitNumberInput.svelte";
  import {
    SIZE_REDUCTION_SAMPLE_RATE_VALUES,
    clampSizeReductionBitrateKbps,
    clampSizeReductionChannels,
    clampSizeReductionSampleRateHz,
  } from "$lib/size-reduction-parameters.js";
  import { t } from "$lib/i18n.js";

  interface Props {
    bitrateKbps: number;
    channels: number;
    compact?: boolean;
    disabled?: boolean;
    disabledReason?: string | null | undefined;
    onBitrateKbps?: (value: number) => void;
    onChannels?: (value: number) => void;
    onSampleRateHz?: (value: number) => void;
    sampleRateHz: number;
    sourceMetadataText?: string | null;
    testPrefix?: string;
  }

  let {
    bitrateKbps = $bindable(),
    channels = $bindable(),
    compact = false,
    disabled = false,
    disabledReason = null,
    onBitrateKbps,
    onChannels,
    onSampleRateHz,
    sampleRateHz = $bindable(),
    sourceMetadataText = null,
    testPrefix = "size-reduction",
  }: Props = $props();

  function applyBitrate(value: number): void {
    onBitrateKbps?.(clampSizeReductionBitrateKbps(value));
  }

  function applySampleRate(value: number): void {
    onSampleRateHz?.(clampSizeReductionSampleRateHz(value));
  }

  function applyChannels(value: number): void {
    onChannels?.(clampSizeReductionChannels(value));
  }
</script>

<details
  class:advanced-params-compact={compact}
  class="advanced-params"
  data-testid={`${testPrefix}-advanced-params`}
>
  <summary>{t("settings.pause_advanced_params")}</summary>
  {#if sourceMetadataText}
    <p
      class="source-metadata"
      data-testid={`${testPrefix}-source-metadata`}
    >
      {sourceMetadataText}
    </p>
  {/if}
  <div class="advanced-params-grid">
    <label>
      <div class="field-label-row">
        <span>{t("settings.size_reduction_bitrate_kbps")}</span>
        <AqeTooltip>
          {#snippet trigger({ props })}
            <button
              {...props}
              type="button"
              class="help-icon-button aqe-tooltip-target"
              data-testid={`${testPrefix}-bitrate-kbps-help`}
              data-aqe-tooltip-content={t("settings.size_reduction_bitrate_kbps.help")}
              aria-label={`${t("settings.size_reduction_bitrate_kbps")} help`}
            >
              <CommandIcon icon="circle-help" size={14} />
            </button>
          {/snippet}
        </AqeTooltip>
      </div>
      <FieldTooltipTarget block content={t("settings.size_reduction_bitrate_kbps.help")} {disabledReason}>
        <UnitNumberInput
          bind:value={bitrateKbps}
          block
          density="comfortable"
          testId={`${testPrefix}-bitrate-kbps`}
          disabled={disabled}
          max="320"
          min="16"
          step="1"
          unit="kbps"
          onValueInput={applyBitrate}
        />
      </FieldTooltipTarget>
    </label>
    <label>
      <div class="field-label-row">
        <span>{t("settings.size_reduction_sample_rate_hz")}</span>
        <AqeTooltip>
          {#snippet trigger({ props })}
            <button
              {...props}
              type="button"
              class="help-icon-button aqe-tooltip-target"
              data-testid={`${testPrefix}-sample-rate-hz-help`}
              data-aqe-tooltip-content={t("settings.size_reduction_sample_rate_hz.help")}
              aria-label={`${t("settings.size_reduction_sample_rate_hz")} help`}
            >
              <CommandIcon icon="circle-help" size={14} />
            </button>
          {/snippet}
        </AqeTooltip>
      </div>
      <FieldTooltipTarget block content={t("settings.size_reduction_sample_rate_hz.help")} {disabledReason}>
        <select
          bind:value={sampleRateHz}
          data-testid={`${testPrefix}-sample-rate-hz`}
          disabled={disabled}
          onchange={(event) => applySampleRate(Number((event.currentTarget as HTMLSelectElement).value))}
        >
          {#each SIZE_REDUCTION_SAMPLE_RATE_VALUES as value}
            <option value={value}>{value} Hz</option>
          {/each}
        </select>
      </FieldTooltipTarget>
    </label>
    <label>
      <div class="field-label-row">
        <span>{t("settings.size_reduction_channels")}</span>
        <AqeTooltip>
          {#snippet trigger({ props })}
            <button
              {...props}
              type="button"
              class="help-icon-button aqe-tooltip-target"
              data-testid={`${testPrefix}-channels-help`}
              data-aqe-tooltip-content={t("settings.size_reduction_channels.help")}
              aria-label={`${t("settings.size_reduction_channels")} help`}
            >
              <CommandIcon icon="circle-help" size={14} />
            </button>
          {/snippet}
        </AqeTooltip>
      </div>
      <FieldTooltipTarget block content={t("settings.size_reduction_channels.help")} {disabledReason}>
        <select
          bind:value={channels}
          data-testid={`${testPrefix}-channels`}
          disabled={disabled}
          onchange={(event) => applyChannels(Number((event.currentTarget as HTMLSelectElement).value))}
        >
          <option value={1}>{t("settings.size_reduction_channels.mono")}</option>
          <option value={2}>{t("settings.size_reduction_channels.stereo")}</option>
        </select>
      </FieldTooltipTarget>
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

  .source-metadata {
    color: var(--fg-muted, var(--fg-subtle, currentColor));
    font-size: 0.75rem;
    line-height: 1.35;
    margin: 6px 0 0;
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

  select {
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

  .advanced-params-compact select {
    border-radius: 5px;
    font-size: 11px;
    min-height: 24px;
    padding: 2px 4px;
  }
</style>
