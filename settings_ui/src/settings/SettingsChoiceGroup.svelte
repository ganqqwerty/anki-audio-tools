<script lang="ts">
  type ChoiceValue = number | string;
  type ChoiceOption = {
    label: string;
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
    <button
      type="button"
      class="settings-choice-button"
      data-testid={`${testId}-${option.value}`}
      role="radio"
      aria-checked={value === option.value ? "true" : "false"}
      onclick={() => onSelect(option.value)}
    >
      {option.label}
    </button>
  {/each}
</div>
