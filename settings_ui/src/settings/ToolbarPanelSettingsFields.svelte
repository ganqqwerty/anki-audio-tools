<script lang="ts">
  import {
    choiceTooltip,
    denoiseAlgorithmTooltip,
    dpdfnetAggressivenessTooltip,
    pauseAggressivenessTooltip,
    pauseDetectionAlgorithmTooltip,
    pitchHumModeTooltip,
    shareTargetTooltip,
  } from "$lib/audio-option-tooltips.js";
  import {
    DPDFNET_ATTENUATION_LIMIT_DB_VALUES,
    formatDpdfnetAggressiveness,
    formatPauseAggressiveness,
    formatPauseDetectionAlgorithm,
    pauseDetectionAlgorithmOrDefault,
    pausePreset,
    PAUSE_DETECTION_ALGORITHM_VALUES,
  } from "$lib/audio-operation-parameters.js";
  import { t } from "$lib/i18n.js";
  import PauseAdvancedParamsFields from "$lib/PauseAdvancedParamsFields.svelte";
  import UnitNumberInput from "$lib/UnitNumberInput.svelte";
  import { DenoiseAlgorithm, PauseAggressiveness, PitchHumMode, type Config } from "$lib/types.js";
  import type { EditorCommand } from "$lib/editor-toolbar-buttons.js";
  import GraphSettingsFields from "./GraphSettingsFields.svelte";
  import OutputFormatField from "./OutputFormatField.svelte";
  import SettingsChoiceGroup from "./SettingsChoiceGroup.svelte";
  import SettingsHiddenWarning from "./SettingsHiddenWarning.svelte";
  import SettingsSizeReductionFields from "./SettingsSizeReductionFields.svelte";

  let {
    command,
    config = $bindable(),
    visible,
  }: {
    command: EditorCommand;
    config: Config;
    visible: boolean;
  } = $props();

  function pauseAlgorithm() {
    return pauseDetectionAlgorithmOrDefault(config.pause_detection_algorithm);
  }

  function applyPausePreset(value: PauseAggressiveness): void {
    const algorithm = pauseAlgorithm();
    const preset = pausePreset(algorithm, value);
    config.pause_aggressiveness = value;
    if (algorithm === "silero_vad") {
      config.pause_silero_threshold = preset.threshold;
      config.pause_silero_min_silence_seconds = preset.minSilenceSeconds;
      config.pause_silero_min_speech_seconds = preset.minSpeechSeconds;
      config.pause_silero_preprocess_denoise = preset.preprocessDenoise;
      return;
    }
    config.pause_silencedetect_threshold_db = preset.threshold;
    config.pause_silencedetect_min_silence_seconds = preset.minSilenceSeconds;
    config.pause_silencedetect_min_speech_seconds = preset.minSpeechSeconds;
    config.pause_silencedetect_preprocess_denoise = preset.preprocessDenoise;
  }
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
{:else if command === "aqe:convert"}
  <OutputFormatField bind:config />
{:else if command === "aqe:reduce-size"}
  <SettingsSizeReductionFields bind:config />
{:else if command === "aqe:remove-pauses"}
  <label class="settings-field">
    <span>{t("settings.pause_detection_algorithm")}</span>
    <SettingsChoiceGroup
      ariaLabel={t("settings.pause_detection_algorithm")}
      options={PAUSE_DETECTION_ALGORITHM_VALUES.map((value) => ({
        label: formatPauseDetectionAlgorithm(value),
        tooltip: choiceTooltip(formatPauseDetectionAlgorithm(value), pauseDetectionAlgorithmTooltip(value)),
        value,
      }))}
      testId="pause-detection-algorithm"
      value={config.pause_detection_algorithm}
      onSelect={(value) => {
        config.pause_detection_algorithm = value as Config["pause_detection_algorithm"];
      }}
    />
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
        tooltip: choiceTooltip(formatPauseAggressiveness(value), pauseAggressivenessTooltip(value)),
        value,
      }))}
      testId="pause-aggressiveness"
      value={config.pause_aggressiveness}
      onSelect={(value) => applyPausePreset(value as PauseAggressiveness)}
    />
  </label>
  {#if pauseAlgorithm() === "silero_vad"}
    <PauseAdvancedParamsFields
      algorithm="silero_vad"
      bind:threshold={config.pause_silero_threshold}
      bind:minSilenceSeconds={config.pause_silero_min_silence_seconds}
      bind:minSpeechSeconds={config.pause_silero_min_speech_seconds}
      bind:preprocessDenoise={config.pause_silero_preprocess_denoise}
      testPrefix="settings-pause"
    />
  {:else}
    <PauseAdvancedParamsFields
      algorithm="silencedetect"
      bind:threshold={config.pause_silencedetect_threshold_db}
      bind:minSilenceSeconds={config.pause_silencedetect_min_silence_seconds}
      bind:minSpeechSeconds={config.pause_silencedetect_min_speech_seconds}
      bind:preprocessDenoise={config.pause_silencedetect_preprocess_denoise}
      testPrefix="settings-pause"
    />
  {/if}
{:else if command === "aqe:denoise-standard"}
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
        tooltip: choiceTooltip(t(`settings.denoise_algorithm.${value}`), denoiseAlgorithmTooltip(value)),
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
        tooltip: choiceTooltip(formatDpdfnetAggressiveness(value), dpdfnetAggressivenessTooltip(value)),
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
{:else if command === "aqe:pitch-hum"}
  <label class="settings-field">
    <span>{t("settings.pitch_hum_mode")}</span>
    <SettingsChoiceGroup
      ariaLabel={t("settings.pitch_hum_mode")}
      options={[PitchHumMode.Direct, PitchHumMode.PitchTier].map((value) => ({
        label: t(`settings.pitch_hum_mode.${value}`),
        tooltip: choiceTooltip(t(`settings.pitch_hum_mode.${value}`), pitchHumModeTooltip(value)),
        value,
      }))}
      testId="pitch-hum-mode"
      value={config.pitch_hum_mode}
      onSelect={(value) => (config.pitch_hum_mode = value as PitchHumMode)}
    />
  </label>
{:else if command === "aqe:slower"}
  <label class="settings-field">
    <span>{t("settings.speed_step")}</span>
    <UnitNumberInput
      inputClass="settings-input"
      min="1.01"
      max="5"
      step="0.01"
      unit="x"
      unitPosition="prefix"
      bind:value={config.speed_step}
    />
  </label>
  <label class="settings-field">
    <span>{t("settings.min_speed")}</span>
    <UnitNumberInput
      inputClass="settings-input"
      min="0.2"
      max="5"
      step="0.05"
      unit="x"
      unitPosition="prefix"
      bind:value={config.min_speed}
    />
  </label>
{:else if command === "aqe:faster"}
  <label class="settings-field">
    <span>{t("settings.max_speed")}</span>
    <UnitNumberInput
      inputClass="settings-input"
      min="0.2"
      max="5"
      step="0.05"
      unit="x"
      unitPosition="prefix"
      bind:value={config.max_speed}
    />
  </label>
{:else if command === "aqe:volume-down"}
  <label class="settings-field">
    <span>{t("settings.volume_step_db")}</span>
    <UnitNumberInput
      inputClass="settings-input"
      min="1"
      max="40"
      step="0.5"
      unit="dB"
      bind:value={config.volume_step_db}
    />
  </label>
  <label class="settings-field">
    <span>{t("settings.min_volume_db")}</span>
    <UnitNumberInput
      inputClass="settings-input"
      min="-40"
      max="40"
      step="0.5"
      unit="dB"
      bind:value={config.min_volume_db}
    />
  </label>
{:else if command === "aqe:volume-up"}
  <label class="settings-field">
    <span>{t("settings.max_volume_db")}</span>
    <UnitNumberInput
      inputClass="settings-input"
      min="-40"
      max="40"
      step="0.5"
      unit="dB"
      bind:value={config.max_volume_db}
    />
  </label>
{:else if command === "aqe:settings" && !visible}
  <SettingsHiddenWarning />
{/if}
