<script lang="ts">
  import FieldTooltipTarget from "$lib/FieldTooltipTarget.svelte";
  import { tooltipWithDisabledClarification } from "$lib/disabled-tooltip.js";

  type ChoiceValue = number | string;
  type ChoiceOption = {
    label: string;
    tooltip?: string;
    value: ChoiceValue;
  };

  const {
    ariaLabel,
    disabled = false,
    disabledReason,
    onSelect,
    options,
    testId,
    value,
  }: {
    ariaLabel: string;
    disabled?: boolean;
    disabledReason?: string | null | undefined;
    onSelect: (value: ChoiceValue) => void;
    options: readonly ChoiceOption[];
    testId: string;
    value: ChoiceValue;
  } = $props();

  function clarifiedTooltip(content: string | undefined): string {
    return tooltipWithDisabledClarification(content, disabled ? disabledReason : undefined);
  }
</script>

<div class="settings-choice-group" data-testid={testId} role="radiogroup" aria-label={ariaLabel}>
  {#each options as option}
    <FieldTooltipTarget content={option.tooltip} disabledReason={disabled ? disabledReason : undefined}>
      <button
        type="button"
        class="settings-choice-button"
        class:aqe-tooltip-target={Boolean(option.tooltip)}
        disabled={disabled}
        data-testid={`${testId}-${option.value}`}
        data-aqe-tooltip-content={clarifiedTooltip(option.tooltip) || undefined}
        role="radio"
        aria-checked={value === option.value ? "true" : "false"}
        onclick={() => {
          if (!disabled) onSelect(option.value);
        }}
      >
        {option.label}
      </button>
    </FieldTooltipTarget>
  {/each}
</div>
