<script lang="ts">
  import AqeTooltip from "$lib/AqeTooltip.svelte";

  type ChoiceValue = number | string;
  type ChoiceOption = {
    label: string;
    tooltip?: string;
    value: ChoiceValue;
  };

  const {
    ariaLabel,
    onSelect,
    options,
    testId,
    value,
  }: {
    ariaLabel: string;
    onSelect: (value: ChoiceValue) => void;
    options: readonly ChoiceOption[];
    testId: string;
    value: ChoiceValue;
  } = $props();
</script>

<div class="settings-choice-group" data-testid={testId} role="radiogroup" aria-label={ariaLabel}>
  {#each options as option}
    <AqeTooltip disabled={!option.tooltip}>
      {#snippet trigger({ props })}
        <button
          {...props}
          type="button"
          class="settings-choice-button"
          class:aqe-tooltip-target={Boolean(option.tooltip)}
          data-testid={`${testId}-${option.value}`}
          data-aqe-tooltip-content={option.tooltip ?? undefined}
          role="radio"
          aria-checked={value === option.value ? "true" : "false"}
          onclick={() => onSelect(option.value)}
        >
          {option.label}
        </button>
      {/snippet}
    </AqeTooltip>
  {/each}
</div>
