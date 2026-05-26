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
  } from "../lib/audio-operation-parameters.js";
  import {
    formatDpdfnetAggressiveness,
    formatPauseDetectionAlgorithm,
  } from "./split-button-state.js";
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
    pauseDetectionAlgorithm,
    slug,
    targetOrd,
  }: {
    command: ButtonSpec["command"];
    denoiseAlgorithm: DenoiseAlgorithm;
    dpdfnetAttnLimitDb: number;
    onChange: () => void;
    onDpdfnetAttnLimitDb: (value: number) => void;
    onPauseDetectionAlgorithm: (value: PauseDetectionAlgorithm) => void;
    pauseDetectionAlgorithm: PauseDetectionAlgorithm;
    slug: string;
    targetOrd: number;
  } = $props();

  function applyDpdfnetAggressiveness(value: number): void {
    onDpdfnetAttnLimitDb(value);
    onChange();
  }

  function applyPauseDetectionAlgorithm(value: string): void {
    if (value === "deep_filter" || value === "silero_vad") {
      onPauseDetectionAlgorithm(value);
      onChange();
    }
  }
</script>

{#if denoiseAlgorithm === "dpdfnet"}
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
{/if}
