<script lang="ts">
  import { t } from "../lib/i18n.js";
  import {
    formatDenoiseAlgorithm,
    formatPauseAggressiveness,
    formatSpeedStep,
    formatTrimMs,
    formatVolumeDb,
  } from "./split-button-state.js";
  import { COMMAND_SLUGS } from "./commands.js";
  import type { ButtonSpec, FieldSplitButtonState } from "./types.js";

  type DenoiseAlgorithm = FieldSplitButtonState["denoiseAlgorithm"];

  const {
    button,
    denoiseAlgorithm,
    onChange,
    onDenoiseAlgorithm,
    onPauseAggressiveness,
    onSpeedStep,
    onTrimStep,
    onVolumeStep,
    pauseAggressiveness,
    speedStep,
    targetOrd,
    trimStepMs,
    volumeStepDb,
  }: {
    button: ButtonSpec;
    denoiseAlgorithm: DenoiseAlgorithm;
    onChange: () => void;
    onDenoiseAlgorithm: (value: DenoiseAlgorithm) => void;
    onPauseAggressiveness: (value: "gentle" | "normal" | "aggressive") => void;
    onSpeedStep: (value: number) => void;
    onTrimStep: (value: number) => void;
    onVolumeStep: (value: number) => void;
    pauseAggressiveness: "gentle" | "normal" | "aggressive";
    speedStep: number;
    targetOrd: number;
    trimStepMs: number;
    volumeStepDb: number;
  } = $props();

  const slug = $derived(COMMAND_SLUGS[button.command]);
  const options = $derived(optionValues());

  function valueLabel(): string {
    if (button.command === "aqe:volume-up" || button.command === "aqe:volume-down") return formatVolumeDb(volumeStepDb);
    if (button.command === "aqe:faster" || button.command === "aqe:slower") return formatSpeedStep(speedStep, button.command);
    if (button.command === "aqe:remove-pauses") return formatPauseAggressiveness(pauseAggressiveness);
    if (
      button.command === "aqe:denoise-standard" ||
      button.command === "aqe:rnnoise" ||
      button.command === "aqe:dpdfnet" ||
      button.command === "aqe:voice-only"
    ) {
      return formatDenoiseAlgorithm(denoiseAlgorithm);
    }
    return formatTrimMs(trimStepMs);
  }

  function sliderValue(): number {
    if (button.command === "aqe:volume-up" || button.command === "aqe:volume-down") return volumeStepDb;
    if (button.command === "aqe:faster" || button.command === "aqe:slower") return speedStep;
    return trimStepMs;
  }

  function sliderConfig(): { min: string; max: string; step: string; labels: string[]; presets: number[] } {
    if (button.command === "aqe:volume-up" || button.command === "aqe:volume-down") {
      return { min: "0.5", max: "12", step: "0.5", labels: ["0.5 dB", "12 dB"], presets: [1, 3, 6, 9] };
    }
    if (button.command === "aqe:faster" || button.command === "aqe:slower") {
      return { min: "0.01", max: "0.25", step: "0.01", labels: ["x1.01", "x1.25"], presets: [0.03, 0.05, 0.1, 0.2] };
    }
    return { min: "50", max: "10000", step: "50", labels: ["50 ms", "10 s"], presets: [100, 200, 500, 1000] };
  }

  function valueInputConfig(): { min: string; max: string; step: string; label: string } {
    if (button.command === "aqe:volume-up" || button.command === "aqe:volume-down") {
      return { min: "0.5", max: "12", step: "0.5", label: "Volume step in dB" };
    }
    if (button.command === "aqe:faster") return { min: "1.01", max: "1.25", step: "0.01", label: "Faster speed multiplier" };
    if (button.command === "aqe:slower") return { min: "0.75", max: "0.99", step: "0.01", label: "Slower speed multiplier" };
    return { min: "50", max: "10000", step: "50", label: "Trim step in milliseconds" };
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
    else onTrimStep(value);
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
    return [];
  }

  function optionLabel(value: string): string {
    if (value === "rnnoise") return "RNNoise";
    if (value === "dpdfnet") return "DPDFNet";
    if (value === "voice_only") return t("settings.denoise_algorithm.voice_only");
    if (value === "aggressive") return t("settings.pause_aggressiveness.aggressive");
    if (value === "gentle") return t("settings.pause_aggressiveness.gentle");
    return value === "standard" ? t("settings.denoise_algorithm.standard") : t("settings.pause_aggressiveness.normal");
  }

  function optionTitle(value: string): string {
    if (value === "dpdfnet") {
      const db = window.__AQE_EDITOR_CONFIG__?.splitButtonDefaults?.dpdfnetAttnLimitDb ?? 12;
      return t("editor.command.dpdfnet.title", { db });
    }
    return optionLabel(value);
  }

  function applyOption(value: string): void {
    if (value === "gentle" || value === "normal" || value === "aggressive") onPauseAggressiveness(value);
    if (value === "standard" || value === "rnnoise" || value === "dpdfnet" || value === "voice_only") onDenoiseAlgorithm(value);
    onChange();
  }

  function presetLabel(value: number): string {
    if (button.command === "aqe:volume-up" || button.command === "aqe:volume-down") return formatVolumeDb(value);
    if (button.command === "aqe:faster" || button.command === "aqe:slower") return formatSpeedStep(value, button.command);
    return formatTrimMs(value);
  }
</script>

<div class="aqe-split-popover-header">
  <strong>{button.label}</strong>
  {#if options.length}
    <span>{valueLabel()}</span>
  {:else}
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
</div>
{#if options.length}
  <div class="aqe-split-presets">
    {#each options as option}
      <button
        type="button"
        class="aqe-button aqe-split-preset"
        data-testid={`aqe-split-${targetOrd}-${slug}-preset-${option}`}
        aria-pressed={valueLabel() === optionLabel(option) ? "true" : "false"}
        title={optionTitle(option)}
        onclick={() => applyOption(option)}
      >
        {optionLabel(option)}
      </button>
    {/each}
  </div>
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
