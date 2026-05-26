<script lang="ts">
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
    <select
      data-testid={`aqe-split-${targetOrd}-${slug}-dpdfnet-aggressiveness`}
      value={dpdfnetAttnLimitDb}
      onchange={(event) => applyDpdfnetAggressiveness(Number((event.currentTarget as HTMLSelectElement).value))}
    >
      {#each DPDFNET_ATTENUATION_LIMIT_DB_VALUES as value}
        <option value={value}>{formatDpdfnetAggressiveness(value)}</option>
      {/each}
    </select>
  </label>
{/if}
{#if command === "aqe:remove-pauses"}
  <label class="aqe-split-extra-field">
    <span>{t("settings.pause_detection_algorithm")}</span>
    <select
      data-testid={`aqe-split-${targetOrd}-${slug}-pause-detection-algorithm`}
      value={pauseDetectionAlgorithm}
      onchange={(event) => applyPauseDetectionAlgorithm((event.currentTarget as HTMLSelectElement).value)}
    >
      {#each PAUSE_DETECTION_ALGORITHM_VALUES as value}
        <option value={value}>{formatPauseDetectionAlgorithm(value)}</option>
      {/each}
    </select>
  </label>
{/if}
