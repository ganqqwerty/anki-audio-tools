<script lang="ts">
  import { t } from "../lib/i18n.js";
  import {
    formatDenoiseAlgorithm,
    formatDpdfnetAggressiveness,
    formatOutputFormat,
    formatPauseAggressiveness,
    formatPitchHumMode,
    formatShareTarget,
    formatSpeedStep,
    formatVolumeDb,
  } from "./split-button-state.js";
  import { COMMAND_SLUGS } from "./commands.js";
  import {
    DPDFNET_ATTENUATION_LIMIT_DB_VALUES,
    isOutputFormatValue,
    OUTPUT_FORMAT_VALUES,
  } from "../lib/audio-operation-parameters.js";
  import SplitDefaultSaveButton from "./SplitDefaultSaveButton.svelte";
  import type { ButtonSpec, FieldSplitButtonState } from "./types.js";

  type DenoiseAlgorithm = FieldSplitButtonState["denoiseAlgorithm"];
  type OutputFormatValue = FieldSplitButtonState["outputFormat"];
  type PitchHumMode = FieldSplitButtonState["pitchHumMode"];
  type ShareTarget = FieldSplitButtonState["shareTarget"];

  const {
    button,
    denoiseAlgorithm,
    dpdfnetAttnLimitDb,
    onChange,
    onDenoiseAlgorithm,
    onDpdfnetAttnLimitDb,
    onOutputFormat,
    onPauseAggressiveness,
    onPitchHumMode,
    onSaveDefault,
    onRun,
    onShareTarget,
    onSpeedStep,
    onVolumeStep,
    pauseAggressiveness,
    outputFormat,
    pitchHumMode,
    saveDefaultSaved,
    shareTarget,
    showSaveDefault,
    speedStep,
    targetOrd,
    volumeStepDb,
  }: {
    button: ButtonSpec;
    denoiseAlgorithm: DenoiseAlgorithm;
    dpdfnetAttnLimitDb: number;
    onChange: () => void;
    onDenoiseAlgorithm: (value: DenoiseAlgorithm) => void;
    onDpdfnetAttnLimitDb: (value: number) => void;
    onOutputFormat: (value: OutputFormatValue) => void;
    onPauseAggressiveness: (value: "gentle" | "normal" | "aggressive") => void;
    onPitchHumMode: (value: PitchHumMode) => void;
    onSaveDefault: () => void;
    onRun: () => void;
    onShareTarget: (value: ShareTarget) => void;
    onSpeedStep: (value: number) => void;
    onVolumeStep: (value: number) => void;
    pauseAggressiveness: "gentle" | "normal" | "aggressive";
    outputFormat: OutputFormatValue;
    pitchHumMode: PitchHumMode;
    saveDefaultSaved: boolean;
    shareTarget: ShareTarget;
    showSaveDefault: boolean;
    speedStep: number;
    targetOrd: number;
    volumeStepDb: number;
  } = $props();

  const slug = $derived(COMMAND_SLUGS[button.command]);
  const options = $derived(optionValues());

  function descriptionText(): string {
    return button.command === "aqe:analyze"
      ? t("editor.split.description_graph", { value: descriptionValueLabel() })
      : t("editor.split.description", { label: button.label, value: descriptionValueLabel() });
  }

  function selectedOptionLabel(): string {
    if (button.command === "aqe:volume-up" || button.command === "aqe:volume-down") return formatVolumeDb(volumeStepDb);
    if (button.command === "aqe:faster" || button.command === "aqe:slower") return formatSpeedStep(speedStep, button.command);
    if (button.command === "aqe:remove-pauses") return formatPauseAggressiveness(pauseAggressiveness);
    if (button.command === "aqe:convert") return formatOutputFormat(outputFormat);
    if (button.command === "aqe:share") return formatShareTarget(shareTarget);
    if (
      button.command === "aqe:denoise-standard" ||
      button.command === "aqe:rnnoise" ||
      button.command === "aqe:dpdfnet" ||
      button.command === "aqe:voice-only"
    ) {
      return formatDenoiseAlgorithm(denoiseAlgorithm);
    }
    if (button.command === "aqe:pitch-hum") return formatPitchHumMode(pitchHumMode);
    return "";
  }

  function descriptionValueLabel(): string {
    return denoiseAlgorithm === "dpdfnet" && (
      button.command === "aqe:denoise-standard" ||
      button.command === "aqe:rnnoise" ||
      button.command === "aqe:dpdfnet" ||
      button.command === "aqe:voice-only"
    )
      ? `${selectedOptionLabel()} (${formatDpdfnetAggressiveness(dpdfnetAttnLimitDb)})`
      : selectedOptionLabel();
  }

  function sliderValue(): number {
    if (button.command === "aqe:volume-up" || button.command === "aqe:volume-down") return volumeStepDb;
    if (button.command === "aqe:faster" || button.command === "aqe:slower") return speedStep;
    return 0;
  }

  function sliderConfig(): { min: string; max: string; step: string; labels: string[]; presets: number[] } {
    if (button.command === "aqe:volume-up" || button.command === "aqe:volume-down") {
      return { min: "0.5", max: "12", step: "0.5", labels: ["0.5 dB", "12 dB"], presets: [1, 3, 6, 9] };
    }
    if (button.command === "aqe:faster" || button.command === "aqe:slower") {
      return { min: "0.01", max: "0.25", step: "0.01", labels: ["x1.01", "x1.25"], presets: [0.03, 0.05, 0.1, 0.2] };
    }
    return { min: "0", max: "0", step: "1", labels: ["", ""], presets: [] };
  }

  function valueInputConfig(): { min: string; max: string; step: string; label: string } {
    if (button.command === "aqe:volume-up" || button.command === "aqe:volume-down") {
      return { min: "0.5", max: "12", step: "0.5", label: "Volume step in dB" };
    }
    if (button.command === "aqe:faster") return { min: "1.01", max: "1.25", step: "0.01", label: "Faster speed multiplier" };
    if (button.command === "aqe:slower") return { min: "0.75", max: "0.99", step: "0.01", label: "Slower speed multiplier" };
    return { min: "0", max: "0", step: "1", label: "" };
  }

  function valueInputValue(): number {
    if (button.command === "aqe:faster") return Number((1 + speedStep).toFixed(2));
    if (button.command === "aqe:slower") return Number((1 - speedStep).toFixed(2));
    return sliderValue();
  }

  function applyValueInput(value: number): void {
    if (!Number.isFinite(value)) return;
    if (button.command === "aqe:faster") applyValue(value - 1);
    else if (button.command === "aqe:slower") applyValue(1 - value);
    else applyValue(value);
  }

  function applyValue(value: number): void {
    if (button.command === "aqe:volume-up" || button.command === "aqe:volume-down") onVolumeStep(value);
    else if (button.command === "aqe:faster" || button.command === "aqe:slower") onSpeedStep(value);
    onChange();
  }

  function optionValues(): string[] {
    if (button.command === "aqe:remove-pauses") return ["gentle", "normal", "aggressive"];
    if (
      button.command === "aqe:denoise-standard" ||
      button.command === "aqe:rnnoise" ||
      button.command === "aqe:dpdfnet" ||
      button.command === "aqe:voice-only"
    ) {
      return ["standard", "rnnoise", "dpdfnet", "voice_only"];
    }
    if (button.command === "aqe:convert") return [...OUTPUT_FORMAT_VALUES];
    if (button.command === "aqe:share") return ["catbox", "litterbox"];
    if (button.command === "aqe:pitch-hum") return ["direct", "pitch_tier"];
    return [];
  }

  function optionLabel(value: string): string {
    if (value === "catbox") return t("editor.share.target.catbox");
    if (value === "litterbox") return t("editor.share.target.litterbox");
    if (isOutputFormatValue(value)) return formatOutputFormat(value);
    if (value === "direct" || value === "pitch_tier") return formatPitchHumMode(value);
    if (value === "rnnoise") return "RNNoise";
    if (value === "dpdfnet") return "DPDFNet";
    if (value === "voice_only") return t("settings.denoise_algorithm.voice_only");
    if (value === "aggressive") return t("settings.pause_aggressiveness.aggressive");
    if (value === "gentle") return t("settings.pause_aggressiveness.gentle");
    return value === "standard" ? t("settings.denoise_algorithm.standard") : t("settings.pause_aggressiveness.normal");
  }

  function optionTitle(value: string): string {
    if (value === "dpdfnet") {
      return t("editor.command.dpdfnet.title", {
        level: formatDpdfnetAggressiveness(dpdfnetAttnLimitDb),
      });
    }
    if (value === "pitch_tier") return t("editor.pitch_hum.mode.pitch_tier.title");
    if (value === "direct") return t("editor.command.pitch_hum.title");
    return optionLabel(value);
  }

  function applyOption(value: string): void {
    if (value === "catbox" || value === "litterbox") onShareTarget(value);
    if (value === "gentle" || value === "normal" || value === "aggressive") onPauseAggressiveness(value);
    if (value === "standard" || value === "rnnoise" || value === "dpdfnet" || value === "voice_only") onDenoiseAlgorithm(value);
    if (isOutputFormatValue(value)) onOutputFormat(value);
    if (value === "direct" || value === "pitch_tier") onPitchHumMode(value);
    onChange();
  }

  function applyDpdfnetAggressiveness(value: number): void {
    onDpdfnetAttnLimitDb(value);
    onChange();
  }

  function presetLabel(value: number): string {
    if (button.command === "aqe:volume-up" || button.command === "aqe:volume-down") return formatVolumeDb(value);
    if (button.command === "aqe:faster" || button.command === "aqe:slower") return formatSpeedStep(value, button.command);
    return "";
  }
</script>

<div class="aqe-split-popover-header aqe-split-popover-header-with-action">
  <span class="aqe-split-popover-title">
    <strong>{button.label}</strong>
    {#if !options.length}
      <input
        class="aqe-split-value-input"
        data-testid={`aqe-split-${targetOrd}-${slug}-value`}
        type="number"
        min={valueInputConfig().min}
        max={valueInputConfig().max}
        step={valueInputConfig().step}
        value={valueInputValue()}
        aria-label={valueInputConfig().label}
        oninput={(event) => applyValueInput((event.currentTarget as HTMLInputElement).valueAsNumber)}
      />
    {/if}
  </span>
  {#if showSaveDefault}
    <SplitDefaultSaveButton
      onSave={onSaveDefault}
      saved={saveDefaultSaved}
      testId={`aqe-split-${targetOrd}-${slug}-save-default`}
    />
  {/if}
</div>
<p class="aqe-split-popover-description">{descriptionText()}</p>
{#if options.length}
  <div class="aqe-split-presets">
    {#each options as option}
      <button
        type="button"
        class="aqe-button aqe-split-preset"
        data-testid={`aqe-split-${targetOrd}-${slug}-preset-${option}`}
        aria-pressed={selectedOptionLabel() === optionLabel(option) ? "true" : "false"}
        title={optionTitle(option)}
        onclick={() => applyOption(option)}
      >
        {optionLabel(option)}
      </button>
    {/each}
  </div>
  {#if denoiseAlgorithm === "dpdfnet"}
    <label class="aqe-split-extra-field">
      <span>{t("settings.dpdfnet_attn_limit_db")}</span>
      <select
        data-testid={`aqe-split-${targetOrd}-${slug}-dpdfnet-aggressiveness`}
        value={dpdfnetAttnLimitDb}
        onchange={(event) => applyDpdfnetAggressiveness(Number((event.currentTarget as HTMLSelectElement).value))}
      >
        {#each DPDFNET_ATTENUATION_LIMIT_DB_VALUES as value}
          <option value={value}>{formatDpdfnetAggressiveness(value)}</option>
        {/each}
      </select>
    </label>
  {/if}
{:else}
  <input
    data-testid={`aqe-split-${targetOrd}-${slug}-slider`}
    type="range"
    min={sliderConfig().min}
    max={sliderConfig().max}
    step={sliderConfig().step}
    value={sliderValue()}
    oninput={(event) => applyValue(Number((event.currentTarget as HTMLInputElement).value))}
  />
  <div class="aqe-split-range-labels">
    <span>{sliderConfig().labels[0]}</span>
    <span>{sliderConfig().labels[1]}</span>
  </div>
  <div class="aqe-split-presets">
    {#each sliderConfig().presets as preset}
      <button
        type="button"
        class="aqe-button aqe-split-preset"
        data-testid={`aqe-split-${targetOrd}-${slug}-preset-${preset}`}
        aria-pressed={sliderValue() === preset ? "true" : "false"}
        onclick={() => applyValue(preset)}
      >
        {presetLabel(preset)}
      </button>
    {/each}
  </div>
{/if}
<div class="aqe-split-popover-footer">
  <button
    type="button"
    class="aqe-button aqe-split-run-button"
    data-testid={`aqe-split-${targetOrd}-${slug}-run`}
    title={t("editor.split.run_title", { label: button.label })}
    aria-label={t("editor.split.run_title", { label: button.label })}
    onclick={onRun}
  >
    {t("editor.split.run")}
  </button>
</div>

<style>
  .aqe-split-extra-field {
    display: grid;
    gap: 6px;
    margin-top: 10px;
  }

  .aqe-split-extra-field span {
    font-size: 0.8rem;
    font-weight: 700;
  }

  .aqe-split-extra-field select {
    background: var(--canvas-elevated, Field);
    border: 1px solid var(--border, ButtonBorder);
    border-radius: 6px;
    color: var(--fg, FieldText);
    font: inherit;
    min-height: 30px;
    padding: 4px 8px;
  }
</style>
