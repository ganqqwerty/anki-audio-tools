<script lang="ts">
  import { clsx } from "clsx";

  interface Props {
    ariaLabel?: string | undefined;
    block?: boolean;
    density?: "compact" | "comfortable";
    disabled?: boolean;
    inputClass?: string | undefined;
    max?: number | string;
    min?: number | string;
    onValueInput?: ((value: number) => void) | undefined;
    step?: number | string;
    testId?: string | undefined;
    unit?: string;
    unitPosition?: "prefix" | "suffix";
    value: number;
    wrapperClass?: string | undefined;
  }

  let {
    ariaLabel,
    block = false,
    density = "compact",
    disabled = false,
    inputClass,
    max,
    min,
    onValueInput,
    step,
    testId,
    unit = "",
    unitPosition = "suffix",
    value = $bindable(),
    wrapperClass,
  }: Props = $props();

  function handleInput(event: Event): void {
    onValueInput?.((event.currentTarget as HTMLInputElement).valueAsNumber);
  }
</script>

<span
  class={clsx(
    "aqe-unit-number-input",
    block && "aqe-unit-number-input-block",
    density === "comfortable" && "aqe-unit-number-input-comfortable",
    wrapperClass,
  )}
  data-unit={unit || undefined}
  data-unit-position={unitPosition}
>
  <input
    bind:value
    aria-label={ariaLabel}
    class={clsx("aqe-unit-number-input-field", inputClass)}
    data-testid={testId}
    disabled={disabled}
    {max}
    {min}
    {step}
    type="number"
    oninput={handleInput}
  />
</span>

<style>
  .aqe-unit-number-input {
    align-items: center;
    display: inline-flex;
    gap: 4px;
    max-width: 100%;
    min-width: 0;
    vertical-align: middle;
  }

  .aqe-unit-number-input-block {
    display: flex;
    width: 100%;
  }

  .aqe-unit-number-input-field {
    background: var(--canvas-elevated, Field);
    border: 1px solid var(--border, ButtonBorder);
    border-radius: 6px;
    box-sizing: border-box;
    color: var(--fg, FieldText);
    font: inherit;
    font-size: 11px;
    min-height: 24px;
    min-width: 0;
    padding: 2px 4px;
    text-align: right;
    max-width: 100%;
    width: var(--aqe-unit-number-input-width, 5.5em);
  }

  .aqe-unit-number-input-block .aqe-unit-number-input-field {
    width: 100%;
  }

  .aqe-unit-number-input-comfortable .aqe-unit-number-input-field {
    border-radius: 6px;
    font-size: inherit;
    min-height: 34px;
    padding: 6px 8px;
  }

  .aqe-unit-number-input[data-unit]::before,
  .aqe-unit-number-input[data-unit]::after {
    color: var(--aqe-text-muted-color, var(--fg-subtle, currentColor));
    flex: 0 0 auto;
    font-size: 11px;
    font-weight: 700;
    line-height: 1;
    white-space: nowrap;
  }

  .aqe-unit-number-input[data-unit][data-unit-position="prefix"]::before {
    content: attr(data-unit);
  }

  .aqe-unit-number-input[data-unit][data-unit-position="suffix"]::after {
    content: attr(data-unit);
  }
</style>
