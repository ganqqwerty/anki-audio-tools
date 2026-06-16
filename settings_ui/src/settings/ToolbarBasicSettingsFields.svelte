<script lang="ts">
  import {
    choiceTooltip,
    shareTargetTooltip,
  } from "$lib/audio-option-tooltips.js";
  import AqeTooltip from "$lib/AqeTooltip.svelte";
  import { t } from "$lib/i18n.js";
  import UnitNumberInput from "$lib/UnitNumberInput.svelte";
  import selectionMarkerShiftButtonsDemoUrl from "./assets/settings-selection-marker-shift-buttons-demo-800x180.gif?inline";
  import type { Config } from "$lib/types.js";
  import type { EditorCommand } from "$lib/editor-toolbar-buttons.js";
  import GraphSettingsFields from "./GraphSettingsFields.svelte";
  import SettingsChoiceGroup from "./SettingsChoiceGroup.svelte";

  let { command, config = $bindable() }: {
    command: EditorCommand;
    config: Config;
  } = $props();
</script>

{#if command === "aqe:play"}
  <label class="settings-toggle">
    <input
      data-testid="repeat-playback-by-default"
      type="checkbox"
      bind:checked={config.repeat_playback_by_default}
    />
    <span class="settings-label-text">{t("settings.repeat_playback_by_default")}</span>
  </label>
  <label class="settings-field">
    <span>{t("settings.repeat_pause_seconds")}</span>
    <UnitNumberInput
      inputClass="settings-input"
      testId="repeat-pause-seconds"
      min="0"
      max="10"
      step="0.1"
      unit="s"
      bind:value={config.repeat_pause_seconds}
    />
  </label>
{:else if command === "aqe:analyze"}
  {@const selectionMarkerShiftTooltip = t("settings.selection_marker_shift_buttons_enabled.tooltip")}
  <AqeTooltip content={selectionMarkerShiftTooltip} side="bottom" align="start" sideOffset={6}>
    {#snippet trigger({ props })}
      <label
        {...props}
        class="settings-toggle aqe-tooltip-target"
        data-aqe-tooltip-content={selectionMarkerShiftTooltip}
      >
        <input
          data-testid="selection-marker-shift-buttons-enabled"
          type="checkbox"
          bind:checked={config.selection_marker_shift_buttons_enabled}
        />
        <span class="settings-label-text">{t("settings.selection_marker_shift_buttons_enabled")}</span>
      </label>
    {/snippet}
    {#snippet richContent()}
      <div class="selection-marker-shift-tooltip">
        <p>{selectionMarkerShiftTooltip}</p>
        <img
          src={selectionMarkerShiftButtonsDemoUrl}
          alt=""
          aria-hidden="true"
          class="selection-marker-shift-tooltip-image"
          width="320"
          height="72"
        />
      </div>
    {/snippet}
  </AqeTooltip>
  <label class="settings-toggle">
    <input
      data-testid="show-graph-by-default"
      type="checkbox"
      bind:checked={config.show_graph_by_default}
    />
    <span class="settings-label-text">{t("settings.show_graph_by_default")}</span>
  </label>
  <GraphSettingsFields bind:config />
{:else if command === "aqe:record-voice"}
  <label class="settings-field">
    <span>{t("settings.voice_recording_countdown_seconds")}</span>
    <UnitNumberInput
      inputClass="settings-input"
      testId="voice-recording-countdown-seconds"
      min="0"
      max="10"
      step="1"
      unit="s"
      bind:value={config.voice_recording_countdown_seconds}
    />
    <span class="settings-field-note">{t("settings.voice_recording_countdown_seconds.help")}</span>
  </label>
{:else if command === "aqe:chorusing-practice"}
  <label class="settings-field">
    <span>{t("settings.chorusing_pause_seconds")}</span>
    <UnitNumberInput
      inputClass="settings-input"
      testId="chorusing-pause-seconds"
      min="0"
      max="10"
      step="0.1"
      unit="s"
      bind:value={config.chorusing_pause_seconds}
    />
  </label>
  <label class="settings-toggle">
    <input
      data-testid="chorusing-auto-advance-by-default"
      type="checkbox"
      bind:checked={config.chorusing_auto_advance_by_default}
    />
    <span class="settings-label-text">{t("settings.chorusing_auto_advance_by_default")}</span>
  </label>
  <label class="settings-field">
    <span>{t("settings.chorusing_auto_advance_repeats")}</span>
    <UnitNumberInput
      inputClass="settings-input"
      testId="chorusing-auto-advance-repeats"
      min="1"
      max="20"
      step="1"
      unit="x"
      bind:value={config.chorusing_auto_advance_repeats}
    />
  </label>
  <label class="settings-field">
    <span>{t("settings.chorusing_marker_interval_ms")}</span>
    <UnitNumberInput
      inputClass="settings-input"
      testId="chorusing-marker-interval-ms"
      min="50"
      max="10000"
      step="50"
      unit="ms"
      bind:value={config.chorusing_marker_interval_ms}
    />
  </label>
{:else if command === "aqe:share"}
  <label class="settings-field">
    <span>{t("settings.share_target")}</span>
    <SettingsChoiceGroup
      ariaLabel={t("settings.share_target")}
      options={["litterbox", "catbox"].map((value) => ({
        label: t(`editor.share.target.${value}`),
        tooltip: choiceTooltip(t(`editor.share.target.${value}`), shareTargetTooltip(value)),
        value,
      }))}
      testId="share-target"
      value={config.share_target}
      onSelect={(value) => (config.share_target = value as Config["share_target"])}
    />
  </label>
{/if}

<style>
  .selection-marker-shift-tooltip {
    display: grid;
    gap: 8px;
  }

  .selection-marker-shift-tooltip p {
    color: inherit;
    margin: 0;
  }

  .selection-marker-shift-tooltip-image {
    border: 1px solid color-mix(in srgb, var(--border, ButtonBorder) 72%, transparent);
    border-radius: 6px;
    display: block;
    height: auto;
    max-width: 100%;
    width: min(320px, calc(100vw - 48px));
  }
</style>
