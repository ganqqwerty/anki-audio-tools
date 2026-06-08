<script lang="ts">
  import AqeTooltip from "../lib/AqeTooltip.svelte";
  import {
    choiceTooltip,
    dpdfnetAggressivenessTooltip,
    pauseDetectionAlgorithmTooltip,
  } from "../lib/audio-option-tooltips.js";
  import { t } from "../lib/i18n.js";
  import {
    DPDFNET_ATTENUATION_LIMIT_DB_VALUES,
    PAUSE_DETECTION_ALGORITHM_VALUES,
    pauseDetectionAlgorithmOrDefault,
  } from "../lib/audio-operation-parameters.js";
  import type { AudioSourceMetadataSummary } from "../lib/size-reduction-parameters.js";
  import PauseAdvancedParamsFields from "../lib/PauseAdvancedParamsFields.svelte";
  import SizeReductionAdvancedParamsFields from "../lib/SizeReductionAdvancedParamsFields.svelte";
  import {
    formatDpdfnetAggressiveness,
    formatPauseDetectionAlgorithm,
  } from "./split-button-state.js";
  import { formatSourceMetadata } from "./source-metadata-formatting.js";
  import { requestSourceMetadata } from "./source-metadata-requests.js";
  import type { ButtonSpec, FieldSplitButtonState } from "./types.js";

  type DenoiseAlgorithm = FieldSplitButtonState["denoiseAlgorithm"];
  type PauseDetectionAlgorithm = FieldSplitButtonState["pauseDetectionAlgorithm"];

  const {
    command,
    denoiseAlgorithm,
    dpdfnetAttnLimitDb,
    onChange,
    onDpdfnetAttnLimitDb,
    onPauseDetectionAlgorithm,
    onPauseMinSilenceSeconds,
    onPauseMinSpeechSeconds,
    onPausePreprocessDenoise,
    onPauseThreshold,
    onSizeReductionBitrateKbps,
    onSizeReductionChannels,
    onSizeReductionSampleRateHz,
    pauseMinSilenceSeconds,
    pauseMinSpeechSeconds,
    pausePreprocessDenoise,
    pauseThreshold,
    pauseDetectionAlgorithm,
    sizeReductionBitrateKbps,
    sizeReductionChannels,
    sizeReductionSampleRateHz,
    slug,
    targetOrd,
  }: {
    command: ButtonSpec["command"];
    denoiseAlgorithm: DenoiseAlgorithm;
    dpdfnetAttnLimitDb: number;
    onChange: () => void;
    onDpdfnetAttnLimitDb: (value: number) => void;
    onPauseDetectionAlgorithm: (value: PauseDetectionAlgorithm) => void;
    onPauseMinSilenceSeconds: (value: number) => void;
    onPauseMinSpeechSeconds: (value: number) => void;
    onPausePreprocessDenoise: (value: boolean) => void;
    onPauseThreshold: (value: number) => void;
    onSizeReductionBitrateKbps: (value: number) => void;
    onSizeReductionChannels: (value: number) => void;
    onSizeReductionSampleRateHz: (value: number) => void;
    pauseMinSilenceSeconds: number;
    pauseMinSpeechSeconds: number;
    pausePreprocessDenoise: boolean;
    pauseThreshold: number;
    pauseDetectionAlgorithm: PauseDetectionAlgorithm;
    sizeReductionBitrateKbps: number;
    sizeReductionChannels: number;
    sizeReductionSampleRateHz: number;
    slug: string;
    targetOrd: number;
  } = $props();

  let sourceMetadata = $state<AudioSourceMetadataSummary | null>(null);
  let sourceMetadataErrorText = $state<string | null>(null);
  let sourceMetadataLoading = $state(false);
  let sourceMetadataRequested = false;

  const sourceFilename = $derived(window.__AQE_EDITOR_CONFIG__?.audioFieldSources?.[targetOrd] ?? null);
  const sourceMetadataText = $derived(sourceMetadata ? formatSourceMetadata(sourceMetadata) : null);

  function applyDpdfnetAggressiveness(value: number): void {
    onDpdfnetAttnLimitDb(value);
    onChange();
  }

  function applyPauseDetectionAlgorithm(value: string): void {
    if (value === "silencedetect" || value === "silero_vad") {
      onPauseDetectionAlgorithm(value);
      onChange();
    }
  }

  function applyPauseThreshold(value: number): void {
    onPauseThreshold(value);
    onChange();
  }

  function applyPauseMinSilenceSeconds(value: number): void {
    onPauseMinSilenceSeconds(value);
    onChange();
  }

  function applyPauseMinSpeechSeconds(value: number): void {
    onPauseMinSpeechSeconds(value);
    onChange();
  }

  function applyPausePreprocessDenoise(value: boolean): void {
    onPausePreprocessDenoise(value);
    onChange();
  }

  function applySizeReductionBitrate(value: number): void {
    onSizeReductionBitrateKbps(value);
    onChange();
  }

  function applySizeReductionSampleRate(value: number): void {
    onSizeReductionSampleRateHz(value);
    onChange();
  }

  function applySizeReductionChannels(value: number): void {
    onSizeReductionChannels(value);
    onChange();
  }

  function requestSourceMetadataAfterAdvancedOpen(): void {
    if (command !== "aqe:reduce-size") return;
    if (sourceMetadataRequested || !sourceFilename) return;
    sourceMetadataRequested = true;
    sourceMetadataLoading = true;
    sourceMetadataErrorText = null;
    requestSourceMetadata(targetOrd, sourceFilename)
      .then((metadata) => {
        sourceMetadata = metadata;
        sourceMetadataErrorText = null;
      })
      .catch(() => {
        sourceMetadata = null;
        sourceMetadataErrorText = t("settings.size_reduction_source_metadata.error");
      })
      .finally(() => {
        sourceMetadataLoading = false;
      });
  }

  function isDenoiseCommand(): boolean {
    return (
      command === "aqe:denoise-standard" ||
      command === "aqe:rnnoise" ||
      command === "aqe:dpdfnet" ||
      command === "aqe:voice-only"
    );
  }
</script>

{#if isDenoiseCommand() && denoiseAlgorithm === "dpdfnet"}
  <label class="aqe-split-extra-field">
    <span>{t("settings.dpdfnet_attn_limit_db")}</span>
    <div
      class="aqe-split-presets aqe-split-extra-choice-group"
      data-testid={`aqe-split-${targetOrd}-${slug}-dpdfnet-aggressiveness`}
      role="radiogroup"
      aria-label={t("settings.dpdfnet_attn_limit_db")}
    >
      {#each DPDFNET_ATTENUATION_LIMIT_DB_VALUES as value}
        <AqeTooltip>
          {#snippet trigger({ props })}
            <button
              {...props}
              type="button"
              class="aqe-button aqe-split-preset aqe-tooltip-target"
              data-testid={`aqe-split-${targetOrd}-${slug}-dpdfnet-aggressiveness-${value}`}
              data-aqe-tooltip-content={choiceTooltip(
                formatDpdfnetAggressiveness(value),
                dpdfnetAggressivenessTooltip(value),
              )}
              role="radio"
              aria-checked={dpdfnetAttnLimitDb === value ? "true" : "false"}
              tabindex={dpdfnetAttnLimitDb === value ? 0 : -1}
              onclick={() => applyDpdfnetAggressiveness(value)}
            >
              {formatDpdfnetAggressiveness(value)}
            </button>
          {/snippet}
        </AqeTooltip>
      {/each}
    </div>
  </label>
{/if}
{#if command === "aqe:remove-pauses"}
  <label class="aqe-split-extra-field">
    <span>{t("settings.pause_detection_algorithm")}</span>
    <div
      class="aqe-split-presets aqe-split-extra-choice-group"
      data-testid={`aqe-split-${targetOrd}-${slug}-pause-detection-algorithm`}
      role="radiogroup"
      aria-label={t("settings.pause_detection_algorithm")}
    >
      {#each PAUSE_DETECTION_ALGORITHM_VALUES as value}
        <AqeTooltip>
          {#snippet trigger({ props })}
            <button
              {...props}
              type="button"
              class="aqe-button aqe-split-preset aqe-tooltip-target"
              data-testid={`aqe-split-${targetOrd}-${slug}-pause-detection-algorithm-${value}`}
              data-aqe-tooltip-content={choiceTooltip(
                formatPauseDetectionAlgorithm(value),
                pauseDetectionAlgorithmTooltip(value),
              )}
              role="radio"
              aria-checked={pauseDetectionAlgorithm === value ? "true" : "false"}
              tabindex={pauseDetectionAlgorithm === value ? 0 : -1}
              onclick={() => applyPauseDetectionAlgorithm(value)}
            >
              {formatPauseDetectionAlgorithm(value)}
            </button>
          {/snippet}
        </AqeTooltip>
      {/each}
    </div>
  </label>
  <PauseAdvancedParamsFields
    algorithm={pauseDetectionAlgorithmOrDefault(pauseDetectionAlgorithm)}
    compact={true}
    threshold={pauseThreshold}
    minSilenceSeconds={pauseMinSilenceSeconds}
    minSpeechSeconds={pauseMinSpeechSeconds}
    preprocessDenoise={pausePreprocessDenoise}
    onThreshold={applyPauseThreshold}
    onMinSilenceSeconds={applyPauseMinSilenceSeconds}
    onMinSpeechSeconds={applyPauseMinSpeechSeconds}
    onPreprocessDenoise={applyPausePreprocessDenoise}
    testPrefix={`aqe-split-${targetOrd}-${slug}-pause`}
  />
{/if}
{#if command === "aqe:reduce-size"}
  <SizeReductionAdvancedParamsFields
    compact={true}
    bitrateKbps={sizeReductionBitrateKbps}
    sampleRateHz={sizeReductionSampleRateHz}
    channels={sizeReductionChannels}
    onBitrateKbps={applySizeReductionBitrate}
    onSampleRateHz={applySizeReductionSampleRate}
    onChannels={applySizeReductionChannels}
    onAdvancedOpen={requestSourceMetadataAfterAdvancedOpen}
    {sourceMetadataText}
    {sourceMetadataErrorText}
    {sourceMetadataLoading}
    testPrefix={`aqe-split-${targetOrd}-${slug}-size-reduction`}
  />
{/if}
