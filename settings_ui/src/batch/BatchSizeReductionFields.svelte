<script lang="ts">
  import FieldTooltipTarget from "$lib/FieldTooltipTarget.svelte";
  import { choiceTooltip, sizeReductionModeTooltip } from "$lib/audio-option-tooltips.js";
  import { tooltipWithDisabledClarification } from "$lib/disabled-tooltip.js";
  import { t } from "$lib/i18n.js";
  import SizeReductionAdvancedParamsFields from "$lib/SizeReductionAdvancedParamsFields.svelte";
  import {
    formatSizeReductionMode,
    SIZE_REDUCTION_MODE_VALUES,
  } from "$lib/size-reduction-parameters.js";
  import { applyBatchSizeReductionPreset, type BatchFormState } from "./batch-state.js";

  let {
    disabled,
    disabledReason,
    form = $bindable(),
  }: {
    disabled: boolean;
    disabledReason?: string | null | undefined;
    form: BatchFormState;
  } = $props();

  function clarifiedTooltip(content: string): string {
    return tooltipWithDisabledClarification(content, disabledReason);
  }
</script>

<label>
  <span>{t("settings.size_reduction_mode")}</span>
  <div class="batch-choice-group" role="radiogroup" aria-label={t("settings.size_reduction_mode")}>
    {#each SIZE_REDUCTION_MODE_VALUES as value}
      {@const tooltip = choiceTooltip(
        formatSizeReductionMode(value),
        sizeReductionModeTooltip(value),
      )}
      <FieldTooltipTarget content={tooltip} {disabledReason}>
        <button
          type="button"
          class="batch-choice-button aqe-tooltip-target"
          {disabled}
          data-testid={`batch-size-reduction-mode-${value}`}
          data-aqe-tooltip-content={clarifiedTooltip(tooltip)}
          role="radio"
          aria-checked={form.sizeReductionMode === value ? "true" : "false"}
          onclick={() => applyBatchSizeReductionPreset(form, value)}
        >
          {formatSizeReductionMode(value)}
        </button>
      </FieldTooltipTarget>
    {/each}
  </div>
</label>
<SizeReductionAdvancedParamsFields
  bind:bitrateKbps={form.sizeReductionBitrateKbps}
  bind:sampleRateHz={form.sizeReductionSampleRateHz}
  bind:channels={form.sizeReductionChannels}
  {disabled}
  {disabledReason}
  testPrefix="batch-size-reduction"
/>
