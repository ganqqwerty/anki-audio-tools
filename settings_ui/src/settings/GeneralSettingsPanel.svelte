<script lang="ts">
  import CommandIcon from "$lib/CommandIcon.svelte";
  import {
    DPDFNET_ATTENUATION_LIMIT_DB_VALUES,
    formatDpdfnetAggressiveness,
  } from "$lib/audio-operation-parameters.js";
  import { t } from "$lib/i18n.js";
  import GraphSettingsFields from "./GraphSettingsFields.svelte";
  import OutputFormatField from "./OutputFormatField.svelte";
  import ToolbarVisibilitySettings from "./ToolbarVisibilitySettings.svelte";
  import type { Config } from "$lib/types.js";

  let { config = $bindable(), saveError }: {
    config: Config;
    saveError: string;
  } = $props();
</script>

<div class="settings-card settings-stack">
  <h2>{t("settings.tab.general")}</h2>
  <div class="settings-section">
    <label class="settings-toggle">
      <input type="checkbox" bind:checked={config.debug_logging} />
      <span class="settings-label-text">{t("settings.debug_logging")}</span>
    </label>
    <label class="settings-toggle">
      <input type="checkbox" bind:checked={config.show_ffmpeg_commands} />
      <span class="settings-label-text">{t("settings.show_ffmpeg_commands")}</span>
    </label>
    <label class="settings-toggle">
      <input
        data-testid="repeat-playback-by-default"
        type="checkbox"
        bind:checked={config.repeat_playback_by_default}
      />
      <span class="settings-label-with-icon">
        <CommandIcon className="settings-label-icon" icon="repeat-2" />
        <span class="settings-label-text">{t("settings.repeat_playback_by_default")}</span>
      </span>
    </label>
    <label class="settings-field">
      <span class="settings-label-with-icon">
        <CommandIcon className="settings-label-icon" icon="repeat-2" />
        <span class="settings-label-text">{t("settings.repeat_pause_seconds")}</span>
      </span>
      <input
        class="settings-input"
        data-testid="repeat-pause-seconds"
        type="number"
        min="0"
        max="10"
        step="0.1"
        bind:value={config.repeat_pause_seconds}
      />
    </label>
    <label class="settings-toggle">
      <input
        data-testid="show-graph-by-default"
        type="checkbox"
        bind:checked={config.show_graph_by_default}
      />
      <span class="settings-label-with-icon">
        <CommandIcon className="settings-label-icon" icon="audio-lines" />
        <span class="settings-label-text">{t("settings.show_graph_by_default")}</span>
      </span>
    </label>
  </div>

  <ToolbarVisibilitySettings bind:config />

  <div class="settings-section">
    <GraphSettingsFields bind:config />
  </div>

  <div class="settings-section settings-grid">
    <label class="settings-field">
      <span>{t("settings.ffmpeg_path")}</span>
      <input
        class="settings-input"
        type="text"
        bind:value={config.ffmpeg_path}
        placeholder={t("settings.ffmpeg_path.placeholder")}
      />
    </label>
    <label class="settings-field">
      <span>{t("settings.deep_filter_path")}</span>
      <input
        class="settings-input"
        type="text"
        bind:value={config.deep_filter_path}
        placeholder={t("settings.deep_filter_path.placeholder")}
      />
    </label>
    <label class="settings-toggle">
      <input type="checkbox" bind:checked={config.deep_filter_post_filter} />
      <span class="settings-label-with-icon">
        <CommandIcon className="settings-label-icon" icon="volume-x" />
        <span class="settings-label-text">{t("settings.deep_filter_post_filter")}</span>
      </span>
    </label>
    <label class="settings-field">
      <span>{t("settings.dpdfnet_attn_limit_db")}</span>
      <select
        class="settings-select"
        data-testid="dpdfnet-attn-limit-db"
        bind:value={config.dpdfnet_attn_limit_db}
      >
        {#each DPDFNET_ATTENUATION_LIMIT_DB_VALUES as value}
          <option value={value}>{formatDpdfnetAggressiveness(value)}</option>
        {/each}
      </select>
    </label>
  </div>

  <div class="settings-grid">
    <label class="settings-field">
      <span class="settings-label-with-icon">
        <CommandIcon className="settings-label-icon" icon="hare-running" />
        <span class="settings-label-text">{t("settings.speed_step")}</span>
      </span>
      <input class="settings-input" type="number" min="0.01" step="0.01" bind:value={config.speed_step} />
    </label>
    <label class="settings-field">
      <span class="settings-label-with-icon">
        <CommandIcon className="settings-label-icon" icon="snail" />
        <span class="settings-label-text">{t("settings.min_speed")}</span>
      </span>
      <input class="settings-input" type="number" min="0.1" step="0.05" bind:value={config.min_speed} />
    </label>
    <label class="settings-field">
      <span class="settings-label-with-icon">
        <CommandIcon className="settings-label-icon" icon="hare-running" />
        <span class="settings-label-text">{t("settings.max_speed")}</span>
      </span>
      <input class="settings-input" type="number" min="0.1" step="0.05" bind:value={config.max_speed} />
    </label>
    <label class="settings-field">
      <span class="settings-label-with-icon">
        <CommandIcon className="settings-label-icon" icon="volume-2" />
        <span class="settings-label-text">{t("settings.volume_step_db")}</span>
      </span>
      <input class="settings-input" type="number" min="0.1" step="0.1" bind:value={config.volume_step_db} />
    </label>
    <label class="settings-field">
      <span class="settings-label-with-icon">
        <CommandIcon className="settings-label-icon" icon="volume-1" />
        <span class="settings-label-text">{t("settings.min_volume_db")}</span>
      </span>
      <input class="settings-input" type="number" step="0.1" bind:value={config.min_volume_db} />
    </label>
    <label class="settings-field">
      <span class="settings-label-with-icon">
        <CommandIcon className="settings-label-icon" icon="volume-2" />
        <span class="settings-label-text">{t("settings.max_volume_db")}</span>
      </span>
      <input class="settings-input" type="number" step="0.1" bind:value={config.max_volume_db} />
    </label>
    <label class="settings-field">
      <span class="settings-label-with-icon">
        <CommandIcon className="settings-label-icon" icon="timer-reset" />
        <span class="settings-label-text">{t("settings.internal_pause_silence_threshold_db")}</span>
      </span>
      <input class="settings-input" type="number" bind:value={config.internal_pause_silence_threshold_db} />
    </label>
    <label class="settings-field">
      <span class="settings-label-with-icon">
        <CommandIcon className="settings-label-icon" icon="timer-reset" />
        <span class="settings-label-text">{t("settings.internal_pause_threshold_ms")}</span>
      </span>
      <input class="settings-input" type="number" min="1" bind:value={config.internal_pause_threshold_ms} />
    </label>
    <label class="settings-field">
      <span class="settings-label-with-icon">
        <CommandIcon className="settings-label-icon" icon="timer-reset" />
        <span class="settings-label-text">{t("settings.internal_pause_target_gap_ms")}</span>
      </span>
      <input class="settings-input" type="number" min="1" bind:value={config.internal_pause_target_gap_ms} />
    </label>
    <label class="settings-field">
      <span class="settings-label-with-icon">
        <CommandIcon className="settings-label-icon" icon="timer-reset" />
        <span class="settings-label-text">{t("settings.pause_aggressiveness")}</span>
      </span>
      <select class="settings-select" bind:value={config.pause_aggressiveness}>
        <option value="gentle">{t("settings.pause_aggressiveness.gentle")}</option>
        <option value="normal">{t("settings.pause_aggressiveness.normal")}</option>
        <option value="aggressive">{t("settings.pause_aggressiveness.aggressive")}</option>
      </select>
    </label>
    <OutputFormatField bind:config />
    <label class="settings-field">
      <span class="settings-label-with-icon">
        <CommandIcon className="settings-label-icon" icon="sparkles" />
        <span class="settings-label-text">{t("settings.denoise_algorithm")}</span>
      </span>
      <select class="settings-select" bind:value={config.denoise_algorithm}>
        <option value="standard">{t("settings.denoise_algorithm.standard")}</option>
        <option value="rnnoise">{t("settings.denoise_algorithm.rnnoise")}</option>
        <option value="dpdfnet">{t("settings.denoise_algorithm.dpdfnet")}</option>
        <option value="voice_only">{t("settings.denoise_algorithm.voice_only")}</option>
      </select>
    </label>
    <label class="settings-field">
      <span class="settings-label-with-icon">
        <CommandIcon className="settings-label-icon" icon="waves" />
        <span class="settings-label-text">{t("settings.pitch_hum_mode")}</span>
      </span>
      <select class="settings-select" data-testid="pitch-hum-mode" bind:value={config.pitch_hum_mode}>
        <option value="direct">{t("settings.pitch_hum_mode.direct")}</option>
        <option value="pitch_tier">{t("settings.pitch_hum_mode.pitch_tier")}</option>
      </select>
    </label>
  </div>
  {#if saveError}
    <p class="settings-error" data-testid="save-error">{saveError}</p>
  {/if}
</div>
