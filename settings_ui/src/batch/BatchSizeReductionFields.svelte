<script lang="ts">
  import AqeTooltip from "$lib/AqeTooltip.svelte";
  import { choiceTooltip, sizeReductionModeTooltip } from "$lib/audio-option-tooltips.js";
  import { t } from "$lib/i18n.js";
  import SizeReductionAdvancedParamsFields from "$lib/SizeReductionAdvancedParamsFields.svelte";
  import {
    formatSizeReductionMode,
    SIZE_REDUCTION_MODE_VALUES,
    type SizeReductionMode,
  } from "$lib/size-reduction-parameters.js";
  import { applyBatchSizeReductionPreset, type BatchFormState } from "./batch-state.js";

  let { disabled, form = $bindable() }: { disabled: boolean; form: BatchFormState } = $props();
</script>

<label>
  <span>{t("settings.size_reduction_mode")}</span>
  <div class="batch-choice-group" role="radiogroup" aria-label={t("settings.size_reduction_mode")}>
    {#each SIZE_REDUCTION_MODE_VALUES as value}
      <AqeTooltip>
        {#snippet trigger({ props })}
          <button
            {...props}
            type="button"
            class="batch-choice-button aqe-tooltip-target"
            {disabled}
            data-testid={`batch-size-reduction-mode-${value}`}
            data-aqe-tooltip-content={choiceTooltip(
              formatSizeReductionMode(value),
              sizeReductionModeTooltip(value),
            )}
            role="radio"
            aria-checked={form.sizeReductionMode === value ? "true" : "false"}
            onclick={() => applyBatchSizeReductionPreset(form, value as SizeReductionMode)}
          >
            {formatSizeReductionMode(value)}
          </button>
        {/snippet}
      </AqeTooltip>
    {/each}
  </div>
</label>
<SizeReductionAdvancedParamsFields
  bind:bitrateKbps={form.sizeReductionBitrateKbps}
  bind:sampleRateHz={form.sizeReductionSampleRateHz}
  bind:channels={form.sizeReductionChannels}
  {disabled}
  testPrefix="batch-size-reduction"
/>
