<script lang="ts">
  import { t } from "../lib/i18n.js";
  import SplitDefaultSaveButton from "./SplitDefaultSaveButton.svelte";
  import { formatVoiceRecordingCountdownSeconds } from "./split-button-state.js";

  const {
    countdownSeconds,
    onCountdownSeconds,
    onSaveDefault,
    saveDefaultSaved,
    slug,
    targetOrd,
  }: {
    countdownSeconds: number;
    onCountdownSeconds: (value: number) => void;
    onSaveDefault: () => void;
    saveDefaultSaved: boolean;
    slug: string;
    targetOrd: number;
  } = $props();

  const presets = [0, 3, 5] as const;

  function apply(value: number): void {
    if (!Number.isFinite(value)) return;
    onCountdownSeconds(value);
  }
</script>

<div class="aqe-split-popover-header aqe-split-popover-header-with-action">
  <span class="aqe-split-popover-title">
    <strong>{t("settings.voice_recording_countdown_seconds")}</strong>
    <input
      class="aqe-split-value-input"
      data-testid={`aqe-split-${targetOrd}-${slug}-value`}
      type="number"
      min="0"
      max="10"
      step="1"
      value={countdownSeconds}
      aria-label={t("settings.voice_recording_countdown_seconds")}
      oninput={(event) => apply((event.currentTarget as HTMLInputElement).valueAsNumber)}
    />
  </span>
  <SplitDefaultSaveButton
    onSave={onSaveDefault}
    saved={saveDefaultSaved}
    testId={`aqe-split-${targetOrd}-${slug}-save-default`}
  />
</div>
<p class="aqe-split-popover-description">
  {t("editor.split.description_record_voice")}
</p>
<input
  data-testid={`aqe-split-${targetOrd}-${slug}-slider`}
  type="range"
  min="0"
  max="10"
  step="1"
  value={countdownSeconds}
  oninput={(event) => apply(Number((event.currentTarget as HTMLInputElement).value))}
/>
<div class="aqe-split-range-labels">
  <span>{formatVoiceRecordingCountdownSeconds(0)}</span>
  <span>{formatVoiceRecordingCountdownSeconds(10)}</span>
</div>
<div class="aqe-split-presets">
  {#each presets as preset}
    <button
      type="button"
      class="aqe-button aqe-split-preset"
      data-testid={`aqe-split-${targetOrd}-${slug}-preset-${preset}`}
      aria-pressed={countdownSeconds === preset ? "true" : "false"}
      onclick={() => apply(preset)}
    >
      {formatVoiceRecordingCountdownSeconds(preset)}
    </button>
  {/each}
</div>
