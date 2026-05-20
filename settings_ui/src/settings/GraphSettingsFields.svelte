<script lang="ts">
  import CommandIcon from "$lib/CommandIcon.svelte";
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
  <label>
    <span class="label-with-icon">
      <CommandIcon className="settings-label-icon" icon="audio-lines" />
      <span>{t("settings.graph_voice_range")}</span>
    </span>
    <select data-testid="graph-voice-range" bind:value={config.graph_voice_range}>
      <option value={GraphVoiceRange.Bass}>{t("settings.graph_voice_range.bass")}</option>
      <option value={GraphVoiceRange.Low}>{t("settings.graph_voice_range.low")}</option>
      <option value={GraphVoiceRange.General}>{t("settings.graph_voice_range.general")}</option>
      <option value={GraphVoiceRange.High}>{t("settings.graph_voice_range.high")}</option>
      <option value={GraphVoiceRange.Child}>{t("settings.graph_voice_range.child")}</option>
    </select>
  </label>
  <label>
    <span class="label-with-icon">
      <CommandIcon className="settings-label-icon" icon="audio-lines" />
      <span>{t("settings.graph_recording_condition")}</span>
    </span>
    <select data-testid="graph-recording-condition" bind:value={config.graph_recording_condition}>
      <option value={GraphRecordingCondition.Auto}>{t("settings.graph_recording_condition.auto")}</option>
      <option value={GraphRecordingCondition.VeryNoisy}>{t("settings.graph_recording_condition.very_noisy")}</option>
      <option value={GraphRecordingCondition.Noisy}>{t("settings.graph_recording_condition.noisy")}</option>
      <option value={GraphRecordingCondition.Normal}>{t("settings.graph_recording_condition.normal")}</option>
      <option value={GraphRecordingCondition.Clean}>{t("settings.graph_recording_condition.clean")}</option>
      <option value={GraphRecordingCondition.Studio}>{t("settings.graph_recording_condition.studio")}</option>
    </select>
  </label>
  <label>
    <span class="label-with-icon">
      <CommandIcon className="settings-label-icon" icon="audio-lines" />
      <span>{t("settings.graph_smoothness")}</span>
    </span>
    <select data-testid="graph-smoothness" bind:value={config.graph_smoothness}>
      <option value={GraphSmoothness.Raw}>{t("settings.graph_smoothness.raw")}</option>
      <option value={GraphSmoothness.Balanced}>{t("settings.graph_smoothness.balanced")}</option>
      <option value={GraphSmoothness.Smooth}>{t("settings.graph_smoothness.smooth")}</option>
      <option value={GraphSmoothness.VerySmooth}>{t("settings.graph_smoothness.very_smooth")}</option>
    </select>
  </label>
  <label>
    <span class="label-with-icon">
      <CommandIcon className="settings-label-icon" icon="audio-lines" />
      <span>{t("settings.graph_connect_short_dropouts_ms")}</span>
    </span>
    <input
      data-testid="graph-connect-short-dropouts-ms"
      type="number"
      min="0"
      max="150"
      step="30"
      bind:value={config.graph_connect_short_dropouts_ms}
    />
  </label>
  <label>
    <span class="label-with-icon">
      <CommandIcon className="settings-label-icon" icon="audio-lines" />
      <span>{t("settings.graph_voice_lock")}</span>
    </span>
    <select data-testid="graph-voice-lock" bind:value={config.graph_voice_lock}>
      <option value={GraphVoiceLock.Loose}>{t("settings.graph_voice_lock.loose")}</option>
      <option value={GraphVoiceLock.Balanced}>{t("settings.graph_voice_lock.balanced")}</option>
      <option value={GraphVoiceLock.Stable}>{t("settings.graph_voice_lock.stable")}</option>
    </select>
  </label>
</div>
