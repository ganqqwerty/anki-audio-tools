<script lang="ts">
  import {
    DPDFNET_ATTENUATION_LIMIT_DB_VALUES,
    formatDpdfnetAggressiveness,
    formatPauseAggressiveness,
  } from "$lib/audio-operation-parameters.js";
  import {
    buttonDisplayMode,
    COMMAND_SLUGS,
    DEFAULT_EDITOR_BUTTON_MODES,
    DEFAULT_VISIBLE_EDITOR_BUTTONS,
    toolbarButtons,
  } from "$lib/editor-toolbar-buttons.js";
  import { t } from "$lib/i18n.js";
  import {
    DenoiseAlgorithm,
    PauseAggressiveness,
    PitchHumMode,
    type Config,
  } from "$lib/types.js";
  import type {
    EditorButtonDisplayMode,
    EditorCommand,
  } from "$lib/editor-toolbar-buttons.js";
  import ButtonSettingsCard from "./ButtonSettingsCard.svelte";
  import GraphSettingsFields from "./GraphSettingsFields.svelte";
  import OutputFormatField from "./OutputFormatField.svelte";
  import SettingsChoiceGroup from "./SettingsChoiceGroup.svelte";

  let { config = $bindable() }: { config: Config } = $props();
  const buttons = toolbarButtons();
  const buttonOrder = buttons.map((button) => button.command);

  function visibleSet(): Set<EditorCommand> {
    if (!Array.isArray(config.visible_editor_buttons)) {
      return new Set(DEFAULT_VISIBLE_EDITOR_BUTTONS);
    }
    return new Set(config.visible_editor_buttons as unknown as EditorCommand[]);
  }

  function isVisible(command: EditorCommand): boolean {
    return visibleSet().has(command);
  }

  function toggle(command: EditorCommand): void {
    const visible = visibleSet();
    if (visible.has(command)) {
      visible.delete(command);
    } else {
      visible.add(command);
    }
    config.visible_editor_buttons = buttonOrder.filter((item) => visible.has(item)) as Config[
      "visible_editor_buttons"
    ];
  }

  function displayMode(command: EditorCommand): EditorButtonDisplayMode {
    return buttonDisplayMode(command, config.editor_button_modes);
  }

  function setDisplayMode(command: EditorCommand, mode: EditorButtonDisplayMode): void {
    config.editor_button_modes = {
      ...DEFAULT_EDITOR_BUTTON_MODES,
      ...(config.editor_button_modes ?? {}),
      [command]: mode,
    };
  }

  function hasSettings(command: EditorCommand): boolean {
    return (
      command === "aqe:play" ||
      command === "aqe:analyze" ||
      command === "aqe:convert" ||
      command === "aqe:remove-pauses" ||
      command === "aqe:denoise-standard" ||
      command === "aqe:pitch-hum" ||
      command === "aqe:slower" ||
      command === "aqe:faster" ||
      command === "aqe:volume-down" ||
      command === "aqe:volume-up"
    );
  }
</script>

<section class="toolbar-visibility settings-section" aria-labelledby="toolbar-visibility-title">
  <div class="toolbar-visibility-header settings-section-header">
    <h3 id="toolbar-visibility-title">{t("settings.toolbar_visibility.title")}</h3>
    <p>{t("settings.toolbar_visibility.summary")}</p>
  </div>

  <div class="button-settings-grid" data-testid="toolbar-visibility-buttons">
    {#each buttons as button (button.command)}
      {@const visible = isVisible(button.command)}
      {@const mode = displayMode(button.command)}
      <ButtonSettingsCard
        hasSettings={hasSettings(button.command)}
        icon={button.icon}
        mode={mode}
        onSetMode={(nextMode) => setDisplayMode(button.command, nextMode)}
        onToggle={() => toggle(button.command)}
        testId={`button-settings-${COMMAND_SLUGS[button.command]}`}
        title={button.label}
        {visible}
      >
        {#if button.command === "aqe:play"}
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
        {:else if button.command === "aqe:analyze"}
          <label class="settings-toggle">
            <input
              data-testid="show-graph-by-default"
              type="checkbox"
              bind:checked={config.show_graph_by_default}
            />
            <span class="settings-label-text">{t("settings.show_graph_by_default")}</span>
          </label>
          <GraphSettingsFields bind:config />
        {:else if button.command === "aqe:convert"}
          <OutputFormatField bind:config />
        {:else if button.command === "aqe:remove-pauses"}
          <label class="settings-field">
            <span>{t("settings.internal_pause_silence_threshold_db")}</span>
            <input class="settings-input" type="number" bind:value={config.internal_pause_silence_threshold_db} />
          </label>
          <label class="settings-field">
            <span>{t("settings.internal_pause_threshold_ms")}</span>
            <input class="settings-input" type="number" min="1" bind:value={config.internal_pause_threshold_ms} />
          </label>
          <label class="settings-field">
            <span>{t("settings.internal_pause_target_gap_ms")}</span>
            <input class="settings-input" type="number" min="1" bind:value={config.internal_pause_target_gap_ms} />
          </label>
          <label class="settings-field">
            <span>{t("settings.pause_aggressiveness")}</span>
            <SettingsChoiceGroup
              ariaLabel={t("settings.pause_aggressiveness")}
              options={[
                PauseAggressiveness.Gentle,
                PauseAggressiveness.Normal,
                PauseAggressiveness.Aggressive,
              ].map((value) => ({
                label: formatPauseAggressiveness(value),
                value,
              }))}
              testId="pause-aggressiveness"
              value={config.pause_aggressiveness}
              onSelect={(value) => (config.pause_aggressiveness = value as PauseAggressiveness)}
            />
          </label>
        {:else if button.command === "aqe:denoise-standard"}
          <label class="settings-field">
            <span>{t("settings.denoise_algorithm")}</span>
            <SettingsChoiceGroup
              ariaLabel={t("settings.denoise_algorithm")}
              options={[
                DenoiseAlgorithm.Standard,
                DenoiseAlgorithm.Rnnoise,
                DenoiseAlgorithm.Dpdfnet,
                DenoiseAlgorithm.VoiceOnly,
              ].map((value) => ({
                label: t(`settings.denoise_algorithm.${value}`),
                value,
              }))}
              testId="denoise-algorithm"
              value={config.denoise_algorithm}
              onSelect={(value) => (config.denoise_algorithm = value as DenoiseAlgorithm)}
            />
          </label>
          <label class="settings-field">
            <span>{t("settings.dpdfnet_attn_limit_db")}</span>
            <SettingsChoiceGroup
              ariaLabel={t("settings.dpdfnet_attn_limit_db")}
              options={DPDFNET_ATTENUATION_LIMIT_DB_VALUES.map((value) => ({
                label: formatDpdfnetAggressiveness(value),
                value,
              }))}
              testId="dpdfnet-attn-limit-db"
              value={config.dpdfnet_attn_limit_db}
              onSelect={(value) => (config.dpdfnet_attn_limit_db = Number(value))}
            />
          </label>
          <label class="settings-toggle">
            <input type="checkbox" bind:checked={config.deep_filter_post_filter} />
            <span class="settings-label-text">{t("settings.deep_filter_post_filter")}</span>
          </label>
        {:else if button.command === "aqe:pitch-hum"}
          <label class="settings-field">
            <span>{t("settings.pitch_hum_mode")}</span>
            <SettingsChoiceGroup
              ariaLabel={t("settings.pitch_hum_mode")}
              options={[PitchHumMode.Direct, PitchHumMode.PitchTier].map((value) => ({
                label: t(`settings.pitch_hum_mode.${value}`),
                value,
              }))}
              testId="pitch-hum-mode"
              value={config.pitch_hum_mode}
              onSelect={(value) => (config.pitch_hum_mode = value as PitchHumMode)}
            />
          </label>
        {:else if button.command === "aqe:slower"}
          <label class="settings-field">
            <span>{t("settings.speed_step")}</span>
            <input class="settings-input" type="number" min="0.01" step="0.01" bind:value={config.speed_step} />
          </label>
          <label class="settings-field">
            <span>{t("settings.min_speed")}</span>
            <input class="settings-input" type="number" min="0.1" step="0.05" bind:value={config.min_speed} />
          </label>
        {:else if button.command === "aqe:faster"}
          <label class="settings-field">
            <span>{t("settings.max_speed")}</span>
            <input class="settings-input" type="number" min="0.1" step="0.05" bind:value={config.max_speed} />
          </label>
        {:else if button.command === "aqe:volume-down"}
          <label class="settings-field">
            <span>{t("settings.volume_step_db")}</span>
            <input class="settings-input" type="number" min="0.1" step="0.1" bind:value={config.volume_step_db} />
          </label>
          <label class="settings-field">
            <span>{t("settings.min_volume_db")}</span>
            <input class="settings-input" type="number" step="0.1" bind:value={config.min_volume_db} />
          </label>
        {:else if button.command === "aqe:volume-up"}
          <label class="settings-field">
            <span>{t("settings.max_volume_db")}</span>
            <input class="settings-input" type="number" step="0.1" bind:value={config.max_volume_db} />
          </label>
        {/if}
      </ButtonSettingsCard>
    {/each}
  </div>
</section>

<style>
  .toolbar-visibility {
    margin-top: 2px;
  }

  h3 {
    font-size: 1rem;
    margin: 0;
  }

  p {
    color: var(--fg-subtle, currentColor);
    margin: 0;
  }

  .button-settings-grid {
    display: grid;
    gap: 0;
  }
</style>
