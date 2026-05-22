<script lang="ts">
  import CommandIcon from "$lib/CommandIcon.svelte";
  import {
    DPDFNET_ATTENUATION_LIMIT_DB_VALUES,
    formatDpdfnetAggressiveness,
  } from "$lib/audio-operation-parameters.js";
  import { t } from "$lib/i18n.js";
  import GraphSettingsFields from "./GraphSettingsFields.svelte";
  import ToolbarVisibilitySettings from "./ToolbarVisibilitySettings.svelte";
  import type { Config } from "$lib/types.js";

  let {
    config = $bindable(),
    saveError,
  }: {
    config: Config;
    saveError: string;
  } = $props();
</script>

<div class="card">
  <h2>{t("settings.tab.general")}</h2>
  <label class="toggle">
    <input type="checkbox" bind:checked={config.debug_logging} />
    <span>{t("settings.debug_logging")}</span>
  </label>
  <label class="toggle">
    <input type="checkbox" bind:checked={config.show_ffmpeg_commands} />
    <span>{t("settings.show_ffmpeg_commands")}</span>
  </label>
  <label class="toggle">
    <input
      data-testid="repeat-playback-by-default"
      type="checkbox"
      bind:checked={config.repeat_playback_by_default}
    />
    <span class="label-with-icon">
      <CommandIcon className="settings-label-icon" icon="repeat-2" />
      <span>{t("settings.repeat_playback_by_default")}</span>
    </span>
  </label>
  <label class="field-row repeat-pause-row">
    <span class="label-with-icon">
      <CommandIcon className="settings-label-icon" icon="repeat-2" />
      <span>{t("settings.repeat_pause_seconds")}</span>
    </span>
    <input
      data-testid="repeat-pause-seconds"
      type="number"
      min="0"
      max="10"
      step="0.1"
      bind:value={config.repeat_pause_seconds}
    />
  </label>
  <label class="toggle">
    <input
      data-testid="show-graph-by-default"
      type="checkbox"
      bind:checked={config.show_graph_by_default}
    />
    <span class="label-with-icon">
      <CommandIcon className="settings-label-icon" icon="audio-lines" />
      <span>{t("settings.show_graph_by_default")}</span>
    </span>
  </label>
  <ToolbarVisibilitySettings bind:config />
  <GraphSettingsFields bind:config />
  <label class="field-row">
    <span>{t("settings.ffmpeg_path")}</span>
    <input
      type="text"
      bind:value={config.ffmpeg_path}
      placeholder={t("settings.ffmpeg_path.placeholder")}
    />
  </label>
  <label class="field-row">
    <span>{t("settings.deep_filter_path")}</span>
    <input
      type="text"
      bind:value={config.deep_filter_path}
      placeholder={t("settings.deep_filter_path.placeholder")}
    />
  </label>
  <label class="toggle">
    <input type="checkbox" bind:checked={config.deep_filter_post_filter} />
    <span class="label-with-icon">
      <CommandIcon className="settings-label-icon" icon="volume-x" />
      <span>{t("settings.deep_filter_post_filter")}</span>
    </span>
  </label>
  <label class="field-row">
    <span>{t("settings.dpdfnet_attn_limit_db")}</span>
    <select
      data-testid="dpdfnet-attn-limit-db"
      bind:value={config.dpdfnet_attn_limit_db}
    >
      {#each DPDFNET_ATTENUATION_LIMIT_DB_VALUES as value}
        <option value={value}>{formatDpdfnetAggressiveness(value)}</option>
      {/each}
    </select>
  </label>
  <div class="settings-grid">
    <label>
      <span class="label-with-icon">
        <CommandIcon className="settings-label-icon" icon="scissors" />
        <span>{t("settings.manual_trim_small_ms")}</span>
      </span>
      <input type="number" min="1" bind:value={config.manual_trim_small_ms} />
    </label>
    <label>
      <span class="label-with-icon">
        <CommandIcon className="settings-label-icon" icon="scissors" />
        <span>{t("settings.manual_trim_large_ms")}</span>
      </span>
      <input type="number" min="1" bind:value={config.manual_trim_large_ms} />
    </label>
    <label>
      <span class="label-with-icon">
        <CommandIcon className="settings-label-icon" icon="hare-running" />
        <span>{t("settings.speed_step")}</span>
      </span>
      <input type="number" min="0.01" step="0.01" bind:value={config.speed_step} />
    </label>
    <label>
      <span class="label-with-icon">
        <CommandIcon className="settings-label-icon" icon="snail" />
        <span>{t("settings.min_speed")}</span>
      </span>
      <input type="number" min="0.1" step="0.05" bind:value={config.min_speed} />
    </label>
    <label>
      <span class="label-with-icon">
        <CommandIcon className="settings-label-icon" icon="hare-running" />
        <span>{t("settings.max_speed")}</span>
      </span>
      <input type="number" min="0.1" step="0.05" bind:value={config.max_speed} />
    </label>
    <label>
      <span class="label-with-icon">
        <CommandIcon className="settings-label-icon" icon="volume-2" />
        <span>{t("settings.volume_step_db")}</span>
      </span>
      <input type="number" min="0.1" step="0.1" bind:value={config.volume_step_db} />
    </label>
    <label>
      <span class="label-with-icon">
        <CommandIcon className="settings-label-icon" icon="volume-1" />
        <span>{t("settings.min_volume_db")}</span>
      </span>
      <input type="number" step="0.1" bind:value={config.min_volume_db} />
    </label>
    <label>
      <span class="label-with-icon">
        <CommandIcon className="settings-label-icon" icon="volume-2" />
        <span>{t("settings.max_volume_db")}</span>
      </span>
      <input type="number" step="0.1" bind:value={config.max_volume_db} />
    </label>
    <label>
      <span class="label-with-icon">
        <CommandIcon className="settings-label-icon" icon="timer-reset" />
        <span>{t("settings.internal_pause_silence_threshold_db")}</span>
      </span>
      <input type="number" bind:value={config.internal_pause_silence_threshold_db} />
    </label>
    <label>
      <span class="label-with-icon">
        <CommandIcon className="settings-label-icon" icon="timer-reset" />
        <span>{t("settings.internal_pause_threshold_ms")}</span>
      </span>
      <input type="number" min="1" bind:value={config.internal_pause_threshold_ms} />
    </label>
    <label>
      <span class="label-with-icon">
        <CommandIcon className="settings-label-icon" icon="timer-reset" />
        <span>{t("settings.internal_pause_target_gap_ms")}</span>
      </span>
      <input type="number" min="1" bind:value={config.internal_pause_target_gap_ms} />
    </label>
    <label>
      <span class="label-with-icon">
        <CommandIcon className="settings-label-icon" icon="timer-reset" />
        <span>{t("settings.pause_aggressiveness")}</span>
      </span>
      <select bind:value={config.pause_aggressiveness}>
        <option value="gentle">{t("settings.pause_aggressiveness.gentle")}</option>
        <option value="normal">{t("settings.pause_aggressiveness.normal")}</option>
        <option value="aggressive">{t("settings.pause_aggressiveness.aggressive")}</option>
      </select>
    </label>
    <label>
      <span class="label-with-icon">
        <CommandIcon className="settings-label-icon" icon="sparkles" />
        <span>{t("settings.denoise_algorithm")}</span>
      </span>
      <select bind:value={config.denoise_algorithm}>
        <option value="standard">{t("settings.denoise_algorithm.standard")}</option>
        <option value="rnnoise">{t("settings.denoise_algorithm.rnnoise")}</option>
        <option value="dpdfnet">{t("settings.denoise_algorithm.dpdfnet")}</option>
        <option value="voice_only">{t("settings.denoise_algorithm.voice_only")}</option>
      </select>
    </label>
    <label>
      <span class="label-with-icon">
        <CommandIcon className="settings-label-icon" icon="waves" />
        <span>{t("settings.pitch_hum_mode")}</span>
      </span>
      <select data-testid="pitch-hum-mode" bind:value={config.pitch_hum_mode}>
        <option value="direct">{t("settings.pitch_hum_mode.direct")}</option>
        <option value="pitch_tier">{t("settings.pitch_hum_mode.pitch_tier")}</option>
      </select>
    </label>
  </div>
  {#if saveError}
    <p class="error" data-testid="save-error">{saveError}</p>
  {/if}
</div>

<style>
  .card {
    background: var(--canvas-elevated, transparent);
    border: 1px solid var(--border, currentColor);
    border-radius: 24px;
    box-shadow: none;
    color: var(--fg, currentColor);
    padding: 24px;
  }

  h2 { margin-top: 0; }

  .toggle {
    align-items: center;
    display: flex;
    gap: 12px;
    padding: 12px 0;
  }

  .field-row,
  .settings-grid label {
    display: grid;
    font-weight: 700;
    gap: 6px;
  }

  .field-row {
    margin: 14px 0;
  }

  .label-with-icon {
    align-items: center;
    display: inline-flex;
    gap: 8px;
    min-width: 0;
  }

  :global(.settings-label-icon) {
    align-items: center;
    color: var(--fg-subtle, currentColor);
    display: inline-flex;
    flex: 0 0 auto;
  }

  .settings-grid {
    display: grid;
    gap: 14px;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    margin-top: 18px;
  }

  input[type="text"],
  input[type="number"],
  select {
    background: var(--canvas-inset, Field);
    border: 1px solid var(--border, currentColor);
    border-radius: 12px;
    color: var(--fg, FieldText);
    font: inherit;
    font-weight: 500;
    padding: 10px 12px;
  }

  input[type="text"]::placeholder,
  input[type="number"]::placeholder {
    color: var(--fg-subtle, currentColor);
  }

  input[type="text"]:focus,
  input[type="number"]:focus,
  select:focus {
    border-color: var(--border-focus, var(--border, currentColor));
    outline: 1px solid var(--border-focus, currentColor);
  }

  .error { color: var(--accent-danger, currentColor); font-weight: 600; }
</style>
