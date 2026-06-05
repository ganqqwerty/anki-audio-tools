<script lang="ts">
  import { t } from "../lib/i18n.js";
  import { PRODUCT_LINKS } from "../lib/product-links.js";
  import UnitNumberInput from "../lib/UnitNumberInput.svelte";
  import ValueSlider from "../lib/ValueSlider.svelte";
  import SplitDefaultSaveButton from "./SplitDefaultSaveButton.svelte";
  import { openEditorExternalLink } from "./external-links.js";
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
    <UnitNumberInput
      inputClass="aqe-split-value-input"
      testId={`aqe-split-${targetOrd}-${slug}-value`}
      min="0"
      max="10"
      step="1"
      value={countdownSeconds}
      unit="s"
      ariaLabel={t("settings.voice_recording_countdown_seconds")}
      onValueInput={apply}
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
  <a
    class="aqe-split-video-link"
    href={PRODUCT_LINKS.editorVideos.recordVoice}
    onclick={(event) => openEditorExternalLink(event, PRODUCT_LINKS.editorVideos.recordVoice)}
    target="_blank"
    rel="noopener noreferrer"
  >
    {t("links.see_video")}
  </a>
</p>
<ValueSlider
  testId={`aqe-split-${targetOrd}-${slug}-slider`}
  min="0"
  max="10"
  step="1"
  value={countdownSeconds}
  ariaLabel={t("settings.voice_recording_countdown_seconds")}
  formatValue={formatVoiceRecordingCountdownSeconds}
  onValueInput={apply}
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
