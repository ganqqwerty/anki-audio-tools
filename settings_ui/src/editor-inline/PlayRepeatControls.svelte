<script lang="ts">
  import { t } from "../lib/i18n.js";
  import UnitNumberInput from "../lib/UnitNumberInput.svelte";
  import ValueSlider from "../lib/ValueSlider.svelte";
  import { formatRepeatPauseSeconds } from "./split-button-state.js";

  const PRESETS = [0, 0.5, 2, 10] as const;

  const {
    onValueInput,
    repeatPauseSeconds,
    targetOrd,
  }: {
    onValueInput: (value: number) => void;
    repeatPauseSeconds: number;
    targetOrd: number;
  } = $props();
</script>

<div class="aqe-split-popover-header">
  <strong>{t("editor.repeat.pause_seconds")}</strong>
  <UnitNumberInput
    inputClass="aqe-split-value-input"
    testId={`aqe-split-${targetOrd}-repeat-value`}
    min="0"
    max="10"
    step="0.1"
    value={repeatPauseSeconds}
    unit="s"
    ariaLabel={t("editor.repeat.pause_seconds")}
    onValueInput={onValueInput}
  />
</div>
<ValueSlider
  testId={`aqe-split-${targetOrd}-repeat-slider`}
  min="0"
  max="10"
  step="0.1"
  value={repeatPauseSeconds}
  ariaLabel={t("editor.repeat.pause_seconds")}
  formatValue={formatRepeatPauseSeconds}
  onValueInput={onValueInput}
/>
<div class="aqe-split-range-labels">
  <span>0 s</span>
  <span>10 s</span>
</div>
<div class="aqe-split-presets">
  {#each PRESETS as preset}
    <button
      type="button"
      class="aqe-button aqe-split-preset"
      data-testid={`aqe-split-${targetOrd}-repeat-preset-${preset}`}
      aria-pressed={repeatPauseSeconds === preset ? "true" : "false"}
      onclick={() => onValueInput(preset)}
    >
      {formatRepeatPauseSeconds(preset)}
    </button>
  {/each}
</div>
