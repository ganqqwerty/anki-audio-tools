<script lang="ts">
  import { clsx } from "clsx";

  interface Props {
    ariaLabel?: string | undefined;
    disabled?: boolean;
    formatValue?: ((value: number) => string) | undefined;
    inputClass?: string | undefined;
    max: number | string;
    min: number | string;
    onValueInput?: ((value: number) => void) | undefined;
    step: number | string;
    testId?: string | undefined;
    value: number;
    wrapperClass?: string | undefined;
  }

  let {
    ariaLabel,
    disabled = false,
    formatValue = (currentValue: number) => String(currentValue),
    inputClass,
    max,
    min,
    onValueInput,
    step,
    testId,
    value = $bindable(),
    wrapperClass,
  }: Props = $props();

  const numericMin = $derived(Number(min));
  const numericMax = $derived(Number(max));
  const numericValue = $derived(Number(value));
  const sliderRatio = $derived(
    Number.isFinite(numericMin) &&
      Number.isFinite(numericMax) &&
      Number.isFinite(numericValue) &&
      numericMax > numericMin
      ? Math.max(0, Math.min(1, (numericValue - numericMin) / (numericMax - numericMin)))
      : 0,
  );
  const valueLabel = $derived(formatValue(numericValue));

  function handleInput(event: Event): void {
    const nextValue = (event.currentTarget as HTMLInputElement).valueAsNumber;
    if (!Number.isFinite(nextValue)) return;
    value = nextValue;
    onValueInput?.(nextValue);
  }
</script>

<span
  class={clsx("aqe-value-slider", wrapperClass)}
  style={`--aqe-value-slider-ratio: ${sliderRatio};`}
>
  <span class="aqe-value-slider-pin" aria-hidden="true">{valueLabel}</span>
  <input
    aria-label={ariaLabel}
    aria-valuetext={valueLabel}
    class={inputClass}
    data-testid={testId}
    disabled={disabled}
    {max}
    {min}
    {step}
    type="range"
    {value}
    oninput={handleInput}
  />
</span>

<style>
  .aqe-value-slider {
    display: block;
    padding-top: 24px;
    position: relative;
    width: 100%;
  }

  .aqe-value-slider input {
    display: block;
    margin: 0;
    width: 100%;
  }

  .aqe-value-slider-pin {
    align-items: center;
    background: var(--aqe-surface-elevated-color, var(--canvas-elevated, ButtonFace));
    border: 1px solid var(--aqe-border-color, var(--border, ButtonBorder));
    border-radius: 999px;
    box-shadow: 0 1px 3px rgb(0 0 0 / 18%);
    box-sizing: border-box;
    color: var(--aqe-text-color, var(--fg, ButtonText));
    display: inline-flex;
    font-size: 10px;
    font-weight: 700;
    justify-content: center;
    left: calc(10px + (100% - 20px) * var(--aqe-value-slider-ratio));
    line-height: 1;
    max-width: 62px;
    min-height: 18px;
    min-width: 24px;
    overflow: hidden;
    padding: 3px 6px;
    pointer-events: none;
    position: absolute;
    text-overflow: ellipsis;
    top: 0;
    transform: translateX(-50%);
    white-space: nowrap;
    z-index: 1;
  }

  .aqe-value-slider-pin::after {
    background: inherit;
    border-bottom: 1px solid var(--aqe-border-color, var(--border, ButtonBorder));
    border-right: 1px solid var(--aqe-border-color, var(--border, ButtonBorder));
    bottom: -4px;
    content: "";
    height: 7px;
    left: 50%;
    position: absolute;
    transform: translateX(-50%) rotate(45deg);
    width: 7px;
    z-index: -1;
  }
</style>
