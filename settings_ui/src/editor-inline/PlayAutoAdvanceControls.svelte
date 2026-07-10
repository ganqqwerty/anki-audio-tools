<script lang="ts">
  import { t } from "../lib/i18n.js";
  import UnitNumberInput from "../lib/UnitNumberInput.svelte";

  const {
    autoAdvance,
    autoAdvanceRepeats,
    disabled = false,
    onAutoAdvanceChange,
    onRepeatsInput,
    targetOrd,
  }: {
    autoAdvance: boolean;
    autoAdvanceRepeats: number;
    disabled?: boolean;
    onAutoAdvanceChange: (enabled: boolean) => void;
    onRepeatsInput: (value: number) => void;
    targetOrd: number;
  } = $props();
</script>

<label class="aqe-split-checkbox-row">
  <input
    type="checkbox"
    checked={autoAdvance}
    disabled={disabled}
    data-testid={`aqe-split-${targetOrd}-play-auto-advance`}
    onchange={(event) => onAutoAdvanceChange((event.currentTarget as HTMLInputElement).checked)}
  />
  <span>{t("editor.play.auto_advance")}</span>
</label>
<div class="aqe-split-popover-header">
  <span>{t("editor.play.auto_advance_repeats")}</span>
  <UnitNumberInput
    inputClass="aqe-split-value-input"
    testId={`aqe-split-${targetOrd}-play-auto-advance-repeats`}
    min="1"
    max="20"
    step="1"
    value={autoAdvanceRepeats}
    {disabled}
    unit="x"
    ariaLabel={t("editor.play.auto_advance_repeats")}
    onValueInput={onRepeatsInput}
  />
</div>
