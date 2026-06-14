<script lang="ts">
  import {
    DPDFNET_ATTENUATION_LIMIT_DB_VALUES,
    OUTPUT_FORMAT_VALUES,
    PAUSE_DETECTION_ALGORITHM_VALUES,
    formatDpdfnetAggressiveness,
    formatOutputFormat,
    formatPauseAggressiveness,
    formatPauseDetectionAlgorithm,
    pauseDetectionAlgorithmOrDefault,
  } from "$lib/audio-operation-parameters.js";
  import FieldTooltipTarget from "$lib/FieldTooltipTarget.svelte";
  import { t } from "$lib/i18n.js";
  import {
    DenoiseAlgorithm,
    Operation,
    PauseAggressiveness,
    type AudioProcessingPresetParameters,
    type AudioProcessingPresetStep,
    type Config,
  } from "$lib/types.js";
  import SettingsChoiceGroup from "./SettingsChoiceGroup.svelte";
  import {
    TRANSFORM_OPERATIONS,
    applyPauseAggressiveness,
    operationLabel,
    parametersForOperation,
  } from "./preset-settings-helpers.js";

  interface Props {
    canMoveDown: boolean;
    canMoveUp: boolean;
    config: Config;
    index: number;
    onChange: (step: AudioProcessingPresetStep) => void;
    onMoveDown: () => void;
    onMoveUp: () => void;
    onRemove: () => void;
    step: AudioProcessingPresetStep;
  }

  const {
    canMoveDown,
    canMoveUp,
    config,
    index,
    onChange,
    onMoveDown,
    onMoveUp,
    onRemove,
    step,
  }: Props = $props();

  const pauseAlgorithm = $derived(
    pauseDetectionAlgorithmOrDefault(step.parameters.pause_detection_algorithm),
  );

  function changeStepOperation(operation: Operation): void {
    onChange({
      ...step,
      operation,
      parameters: parametersForOperation(operation, config),
    });
  }

  function updateParameters(parameters: Partial<AudioProcessingPresetParameters>): void {
    onChange({
      ...step,
      parameters: {
        ...step.parameters,
        ...parameters,
      },
    });
  }

  function updateNumber(
    parameter: keyof AudioProcessingPresetParameters,
    event: Event,
  ): void {
    const value = (event.currentTarget as HTMLInputElement).valueAsNumber;
    if (Number.isNaN(value)) return;
    updateParameters({ [parameter]: value });
  }

  function applyPause(value: PauseAggressiveness): void {
    const nextStep = structuredClone(step);
    applyPauseAggressiveness(nextStep, value);
    onChange(nextStep);
  }
</script>

<section class="preset-step" data-testid={`preset-step-${index}`}>
  <header>
    <strong>{index + 1}. {operationLabel(step.operation)}</strong>
    <span class="preset-step-actions">
      <FieldTooltipTarget content={t("settings.presets.move_up.tooltip")}>
        <button type="button" class="settings-button" disabled={!canMoveUp} onclick={onMoveUp}>
          {t("settings.presets.move_up")}
        </button>
      </FieldTooltipTarget>
      <FieldTooltipTarget content={t("settings.presets.move_down.tooltip")}>
        <button type="button" class="settings-button" disabled={!canMoveDown} onclick={onMoveDown}>
          {t("settings.presets.move_down")}
        </button>
      </FieldTooltipTarget>
      <FieldTooltipTarget content={t("settings.presets.remove_step.tooltip")}>
        <button type="button" class="settings-button" onclick={onRemove}>
          {t("settings.presets.remove_step")}
        </button>
      </FieldTooltipTarget>
    </span>
  </header>

  <div class="settings-grid">
    <FieldTooltipTarget block content={t("settings.presets.operation.tooltip")}>
      <label class="settings-field">
        <span>{t("settings.presets.operation")}</span>
        <select
          class="settings-select"
          value={step.operation}
          onchange={(event) => changeStepOperation((event.currentTarget as HTMLSelectElement).value as Operation)}
        >
          {#each TRANSFORM_OPERATIONS as operation}
            <option value={operation}>{operationLabel(operation)}</option>
          {/each}
        </select>
      </label>
    </FieldTooltipTarget>

    {#if step.operation === Operation.Convert}
      <FieldTooltipTarget block content={t("settings.output_format.tooltip")}>
        <label class="settings-field">
          <span>{t("settings.output_format")}</span>
          <select
            class="settings-select"
            value={step.parameters.target_format ?? config.output_format}
            onchange={(event) => updateParameters({ target_format: (event.currentTarget as HTMLSelectElement).value as Config["output_format"] })}
          >
            {#each OUTPUT_FORMAT_VALUES as format}
              <option value={format}>{formatOutputFormat(format)}</option>
            {/each}
          </select>
        </label>
      </FieldTooltipTarget>
    {:else if step.operation === Operation.Denoise}
      <FieldTooltipTarget block content={t("settings.denoise_algorithm.tooltip")}>
        <label class="settings-field">
          <span>{t("settings.denoise_algorithm")}</span>
          <SettingsChoiceGroup
            ariaLabel={t("settings.denoise_algorithm")}
            options={[DenoiseAlgorithm.Standard, DenoiseAlgorithm.Rnnoise, DenoiseAlgorithm.Dpdfnet, DenoiseAlgorithm.VoiceOnly].map((value) => ({
              label: t(`settings.denoise_algorithm.${value}`),
              tooltip: t(`settings.denoise_algorithm.${value}.tooltip`),
              value,
            }))}
            testId={`preset-step-${index}-denoise`}
            value={step.parameters.denoise_algorithm ?? DenoiseAlgorithm.Standard}
            onSelect={(value) => updateParameters({ denoise_algorithm: value as DenoiseAlgorithm })}
          />
        </label>
      </FieldTooltipTarget>
      {#if step.parameters.denoise_algorithm === DenoiseAlgorithm.Dpdfnet}
        <FieldTooltipTarget block content={t("settings.dpdfnet_attn_limit_db.tooltip")}>
          <label class="settings-field">
            <span>{t("settings.dpdfnet_attn_limit_db")}</span>
            <SettingsChoiceGroup
              ariaLabel={t("settings.dpdfnet_attn_limit_db")}
              options={DPDFNET_ATTENUATION_LIMIT_DB_VALUES.map((value) => ({
                label: formatDpdfnetAggressiveness(value),
                tooltip: t(`settings.dpdfnet_attn_limit_db.${value === 6 ? "gentle" : value === 12 ? "normal" : "aggressive"}.tooltip`),
                value,
              }))}
              testId={`preset-step-${index}-dpdfnet`}
              value={step.parameters.dpdfnet_attn_limit_db ?? config.dpdfnet_attn_limit_db}
              onSelect={(value) => updateParameters({ dpdfnet_attn_limit_db: Number(value) })}
            />
          </label>
        </FieldTooltipTarget>
      {/if}
    {:else if step.operation === Operation.RemovePauses}
      <FieldTooltipTarget block content={t("settings.pause_aggressiveness.tooltip")}>
        <label class="settings-field">
          <span>{t("settings.pause_aggressiveness")}</span>
          <SettingsChoiceGroup
            ariaLabel={t("settings.pause_aggressiveness")}
            options={[PauseAggressiveness.Gentle, PauseAggressiveness.Normal, PauseAggressiveness.Aggressive].map((value) => ({
              label: formatPauseAggressiveness(value),
              tooltip: t(`editor.split.option.pause.${value}.description`),
              value,
            }))}
            testId={`preset-step-${index}-pause-aggressiveness`}
            value={step.parameters.pause_aggressiveness ?? PauseAggressiveness.Normal}
            onSelect={(value) => applyPause(value as PauseAggressiveness)}
          />
        </label>
      </FieldTooltipTarget>
      <FieldTooltipTarget block content={t("settings.pause_detection_algorithm.tooltip")}>
        <label class="settings-field">
          <span>{t("settings.pause_detection_algorithm")}</span>
          <select
            class="settings-select"
            value={pauseAlgorithm}
            onchange={(event) => updateParameters({ pause_detection_algorithm: (event.currentTarget as HTMLSelectElement).value as Config["pause_detection_algorithm"] })}
          >
            {#each PAUSE_DETECTION_ALGORITHM_VALUES as value}
              <option value={value}>{formatPauseDetectionAlgorithm(value)}</option>
            {/each}
          </select>
        </label>
      </FieldTooltipTarget>
      <FieldTooltipTarget block content={t("settings.pause_threshold_db.help")}>
        <label class="settings-field">
          <span>{t("settings.pause_threshold_db")}</span>
          <input
            class="settings-input"
            type="number"
            step="0.01"
            value={step.parameters.pause_threshold ?? config.pause_silencedetect_threshold_db}
            oninput={(event) => updateNumber("pause_threshold", event)}
          />
        </label>
      </FieldTooltipTarget>
      <FieldTooltipTarget block content={t("settings.pause_min_silence_seconds.help")}>
        <label class="settings-field">
          <span>{t("settings.pause_min_silence_seconds")}</span>
          <input
            class="settings-input"
            type="number"
            min="0"
            step="0.01"
            value={step.parameters.pause_min_silence_seconds ?? config.pause_silencedetect_min_silence_seconds}
            oninput={(event) => updateNumber("pause_min_silence_seconds", event)}
          />
        </label>
      </FieldTooltipTarget>
      <FieldTooltipTarget block content={t("settings.pause_min_speech_seconds.help")}>
        <label class="settings-field">
          <span>{t("settings.pause_min_speech_seconds")}</span>
          <input
            class="settings-input"
            type="number"
            min="0"
            step="0.01"
            value={step.parameters.pause_min_speech_seconds ?? config.pause_silencedetect_min_speech_seconds}
            oninput={(event) => updateNumber("pause_min_speech_seconds", event)}
          />
        </label>
      </FieldTooltipTarget>
      <FieldTooltipTarget block content={t("settings.pause_preprocess_denoise.help")}>
        <label class="settings-toggle">
          <input
            type="checkbox"
            checked={step.parameters.pause_preprocess_denoise ?? config.pause_silencedetect_preprocess_denoise}
            onchange={(event) => updateParameters({ pause_preprocess_denoise: (event.currentTarget as HTMLInputElement).checked })}
          />
          <span class="settings-label-text">{t("settings.pause_preprocess_denoise")}</span>
        </label>
      </FieldTooltipTarget>
    {:else if step.operation === Operation.Slower || step.operation === Operation.Faster}
      <FieldTooltipTarget block content={t("settings.speed_step.tooltip")}>
        <label class="settings-field">
          <span>{t("settings.speed_step")}</span>
          <input
            class="settings-input"
            type="number"
            min="1.01"
            max="5"
            step="0.01"
            value={step.parameters.speed_step ?? config.speed_step}
            oninput={(event) => updateNumber("speed_step", event)}
          />
        </label>
      </FieldTooltipTarget>
    {:else if step.operation === Operation.VolumeDown || step.operation === Operation.VolumeUp}
      <FieldTooltipTarget block content={t("settings.volume_step_db.tooltip")}>
        <label class="settings-field">
          <span>{t("settings.volume_step_db")}</span>
          <input
            class="settings-input"
            type="number"
            min="1"
            max="40"
            step="0.5"
            value={step.parameters.volume_step_db ?? config.volume_step_db}
            oninput={(event) => updateNumber("volume_step_db", event)}
          />
        </label>
      </FieldTooltipTarget>
    {/if}
  </div>
</section>
