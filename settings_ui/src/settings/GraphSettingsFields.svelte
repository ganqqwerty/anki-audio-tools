<script lang="ts">
  import AqeTooltip from "$lib/AqeTooltip.svelte";
  import CommandIcon from "$lib/CommandIcon.svelte";
  import {
    graphConnectDropoutsNote,
    graphRecordingConditionNote,
    graphRecordingConditionTooltip,
    graphVoiceLockNote,
    graphVoiceLockTooltip,
    graphVoiceRangeNote,
    graphVoiceRangeTooltip,
    formatGraphRecordingCondition,
    formatGraphVoiceLock,
    formatGraphVoiceRange,
    GRAPH_RECORDING_CONDITIONS,
    GRAPH_SMOOTHNESSES,
    GRAPH_VOICE_LOCKS,
    GRAPH_VOICE_RANGES,
  } from "$lib/graph-option-copy.js";
  import { t } from "$lib/i18n.js";
  import {
    GraphRecordingCondition,
    GraphSmoothness,
    GraphVoiceLock,
    GraphVoiceRange,
  } from "$lib/types.js";
  import type { Config } from "$lib/types.js";

  const { config = $bindable() }: { config: Config } = $props();
</script>

<div class="settings-grid graph-settings-grid">
  <div class="settings-field">
    <span class="settings-label-with-icon">
      <CommandIcon className="settings-label-icon" icon="audio-lines" />
      <span class="settings-label-text">{t("settings.graph_voice_range")}</span>
    </span>
    <span class="settings-field-note">{graphVoiceRangeNote()}</span>
    <div class="settings-choice-group" role="radiogroup" aria-label={t("settings.graph_voice_range")}>
      {#each GRAPH_VOICE_RANGES as option}
        <AqeTooltip>
          {#snippet trigger({ props })}
            <button
              {...props}
              type="button"
              class="settings-choice-button aqe-tooltip-target"
              data-testid={`graph-voice-range-${option}`}
              data-aqe-tooltip-content={graphVoiceRangeTooltip(option)}
              role="radio"
              aria-checked={config.graph_voice_range === option ? "true" : "false"}
              onclick={() => (config.graph_voice_range = option as GraphVoiceRange)}
            >
              {formatGraphVoiceRange(option)}
            </button>
          {/snippet}
        </AqeTooltip>
      {/each}
    </div>
  </div>

  <div class="settings-field">
    <span class="settings-label-with-icon">
      <CommandIcon className="settings-label-icon" icon="mic" />
      <span class="settings-label-text">{t("settings.graph_recording_condition")}</span>
    </span>
    <span class="settings-field-note">{graphRecordingConditionNote()}</span>
    <div class="settings-choice-group" role="radiogroup" aria-label={t("settings.graph_recording_condition")}>
      {#each GRAPH_RECORDING_CONDITIONS as option}
        <AqeTooltip>
          {#snippet trigger({ props })}
            <button
              {...props}
              type="button"
              class="settings-choice-button aqe-tooltip-target"
              data-testid={`graph-recording-condition-${option}`}
              data-aqe-tooltip-content={graphRecordingConditionTooltip(option)}
              role="radio"
              aria-checked={config.graph_recording_condition === option ? "true" : "false"}
              onclick={() => (config.graph_recording_condition = option as GraphRecordingCondition)}
            >
              {formatGraphRecordingCondition(option)}
            </button>
          {/snippet}
        </AqeTooltip>
      {/each}
    </div>
  </div>

  <div class="settings-field">
    <span class="settings-label-with-icon">
      <CommandIcon className="settings-label-icon" icon="audio-lines" />
      <span class="settings-label-text">{t("settings.graph_smoothness")}</span>
    </span>
    <select class="settings-select" data-testid="graph-smoothness" bind:value={config.graph_smoothness}>
      {#each GRAPH_SMOOTHNESSES as option}
        <option value={option as GraphSmoothness}>{t(`settings.graph_smoothness.${option}`)}</option>
      {/each}
    </select>
  </div>

  <div class="settings-field">
    <span class="settings-label-with-icon">
      <CommandIcon className="settings-label-icon" icon="chart-line" />
      <span class="settings-label-text">{t("settings.graph_connect_short_dropouts_ms")}</span>
    </span>
    <span class="settings-field-note">{graphConnectDropoutsNote()}</span>
    <input
      class="settings-input"
      data-testid="graph-connect-short-dropouts-ms"
      type="number"
      min="0"
      max="500"
      step="30"
      bind:value={config.graph_connect_short_dropouts_ms}
    />
  </div>

  <div class="settings-field">
    <span class="settings-label-with-icon">
      <CommandIcon className="settings-label-icon" icon="chart-line" />
      <span class="settings-label-text">{t("settings.graph_voice_lock")}</span>
    </span>
    <span class="settings-field-note">{graphVoiceLockNote()}</span>
    <div class="settings-choice-group" role="radiogroup" aria-label={t("settings.graph_voice_lock")}>
      {#each GRAPH_VOICE_LOCKS as option}
        <AqeTooltip>
          {#snippet trigger({ props })}
            <button
              {...props}
              type="button"
              class="settings-choice-button aqe-tooltip-target"
              data-testid={`graph-voice-lock-${option}`}
              data-aqe-tooltip-content={graphVoiceLockTooltip(option)}
              role="radio"
              aria-checked={config.graph_voice_lock === option ? "true" : "false"}
              onclick={() => (config.graph_voice_lock = option as GraphVoiceLock)}
            >
              {formatGraphVoiceLock(option)}
            </button>
          {/snippet}
        </AqeTooltip>
      {/each}
    </div>
  </div>
</div>
