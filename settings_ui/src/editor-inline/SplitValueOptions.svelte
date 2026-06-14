<script lang="ts">
  import { t } from "../lib/i18n.js";
  import AqeTooltip from "../lib/AqeTooltip.svelte";
  import {
    formatDenoiseAlgorithm,
    formatOutputFormat,
    formatPauseAggressiveness,
    formatPitchHumMode,
    formatShareTarget,
    formatSizeReductionMode,
    formatSpeedStep,
    formatVolumeDb,
  } from "./split-button-state.js";
  import { COMMAND_SLUGS } from "./commands.js";
  import { openEditorExternalLink } from "./external-links.js";
  import { isOutputFormatValue } from "../lib/audio-operation-parameters.js";
  import {
    splitMenuDescription,
    splitMenuVideoLink,
    splitOptionLabel,
    splitOptionValues,
  } from "./split-menu-content.js";
  import SplitDefaultSaveButton from "./SplitDefaultSaveButton.svelte";
  import SplitExtraFields from "./SplitExtraFields.svelte";
  import SplitValuePresetGrid from "./SplitValuePresetGrid.svelte";
  import SplitRunButtons from "./SplitRunButtons.svelte";
  import UnitNumberInput from "../lib/UnitNumberInput.svelte";
  import ValueSlider from "../lib/ValueSlider.svelte";
  import type { ButtonSpec, FieldSplitButtonState } from "./types.js";

  type DenoiseAlgorithm = FieldSplitButtonState["denoiseAlgorithm"];
  type OutputFormatValue = FieldSplitButtonState["outputFormat"];
  type PauseDetectionAlgorithm = FieldSplitButtonState["pauseDetectionAlgorithm"];
  type PitchHumMode = FieldSplitButtonState["pitchHumMode"];
  type ShareTarget = FieldSplitButtonState["shareTarget"];
  type SizeReductionMode = FieldSplitButtonState["sizeReductionMode"];
  const {
    button,
    denoiseAlgorithm,
    dpdfnetAttnLimitDb,
    groupSlug,
    menuLabel,
    onChange,
    onDenoiseAlgorithm,
    onDpdfnetAttnLimitDb,
    onOutputFormat,
    onPauseAggressiveness,
    onPauseDetectionAlgorithm,
    onPauseMinSilenceSeconds,
    onPauseMinSpeechSeconds,
    onPausePreprocessDenoise,
    onPauseThreshold,
    onPitchHumMode,
    onSaveDefault,
    onRunCommand,
    onShareTarget,
    onSizeReductionBitrateKbps,
    onSizeReductionChannels,
    onSizeReductionMode,
    onSizeReductionSampleRateHz,
    onSpeedStep,
    onVolumeStep,
    pauseAggressiveness,
    pauseDetectionAlgorithm,
    pauseMinSilenceSeconds,
    pauseMinSpeechSeconds,
    pausePreprocessDenoise,
    pauseThreshold,
    outputFormat,
    pitchHumMode,
    saveDefaultSaved,
    shareTarget,
    showRunButton,
    showSaveDefault,
    sizeReductionMode,
    sizeReductionBitrateKbps,
    sizeReductionSampleRateHz,
    sizeReductionChannels,
    sourceFilename = null,
    speedStep,
    targetOrd,
    volumeStepDb,
  }: {
    button: ButtonSpec;
    denoiseAlgorithm: DenoiseAlgorithm;
    dpdfnetAttnLimitDb: number;
    groupSlug?: "speed" | "volume" | undefined;
    menuLabel: string;
    onChange: () => void;
    onDenoiseAlgorithm: (value: DenoiseAlgorithm) => void;
    onDpdfnetAttnLimitDb: (value: number) => void;
    onOutputFormat: (value: OutputFormatValue) => void;
    onPauseAggressiveness: (value: "gentle" | "normal" | "aggressive") => void;
    onPauseDetectionAlgorithm: (value: PauseDetectionAlgorithm) => void;
    onPauseMinSilenceSeconds: (value: number) => void;
    onPauseMinSpeechSeconds: (value: number) => void;
    onPausePreprocessDenoise: (value: boolean) => void;
    onPauseThreshold: (value: number) => void;
    onPitchHumMode: (value: PitchHumMode) => void;
    onSaveDefault: () => void;
    onRunCommand: (command: ButtonSpec["command"]) => void;
    onShareTarget: (value: ShareTarget) => void;
    onSizeReductionBitrateKbps: (value: number) => void;
    onSizeReductionChannels: (value: number) => void;
    onSizeReductionMode: (value: SizeReductionMode) => void;
    onSizeReductionSampleRateHz: (value: number) => void;
    onSpeedStep: (value: number) => void;
    onVolumeStep: (value: number) => void;
    pauseAggressiveness: "gentle" | "normal" | "aggressive";
    pauseDetectionAlgorithm: PauseDetectionAlgorithm;
    pauseMinSilenceSeconds: number;
    pauseMinSpeechSeconds: number;
    pausePreprocessDenoise: boolean;
    pauseThreshold: number;
    outputFormat: OutputFormatValue;
    pitchHumMode: PitchHumMode;
    saveDefaultSaved: boolean;
    shareTarget: ShareTarget;
    showRunButton: boolean;
    showSaveDefault: boolean;
    sizeReductionMode: SizeReductionMode;
    sizeReductionBitrateKbps: number;
    sizeReductionSampleRateHz: number;
    sizeReductionChannels: number;
    sourceFilename?: string | null;
    speedStep: number;
    targetOrd: number;
    volumeStepDb: number;
  } = $props();

  const slug = $derived(groupSlug ?? COMMAND_SLUGS[button.command]);
  const options = $derived(optionValues());
  const videoLink = $derived(splitMenuVideoLink(button.command, groupSlug));
  const SPEED_RUN_COMMANDS = ["aqe:slower", "aqe:faster"] as const satisfies readonly ButtonSpec["command"][];
  const VOLUME_RUN_COMMANDS = ["aqe:volume-down", "aqe:volume-up"] as const satisfies readonly ButtonSpec["command"][];

  function isVolumeControl(): boolean {
    return (
      groupSlug === "volume" ||
      button.command === "aqe:volume-up" ||
      button.command === "aqe:volume-down"
    );
  }

  function isSpeedControl(): boolean {
    return groupSlug === "speed" || button.command === "aqe:faster" || button.command === "aqe:slower";
  }

  function groupedSpeedLabel(value: number): string {
    return formatSpeedStep(value, "aqe:faster");
  }

  function selectedOptionLabel(): string {
    if (isVolumeControl()) return formatVolumeDb(volumeStepDb);
    if (groupSlug === "speed") return groupedSpeedLabel(speedStep);
    if (isSpeedControl()) return formatSpeedStep(speedStep, button.command);
    if (button.command === "aqe:remove-pauses") return formatPauseAggressiveness(pauseAggressiveness);
    if (button.command === "aqe:reduce-size") return formatSizeReductionMode(sizeReductionMode);
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

  function sliderValue(): number {
    if (isVolumeControl()) return volumeStepDb;
    if (isSpeedControl()) return speedStep;
    return 0;
  }

  function sliderConfig(): { min: string; max: string; step: string; labels: string[]; presets: number[] } {
    if (isVolumeControl()) {
      return { min: "1", max: "40", step: "0.5", labels: ["1 dB", "40 dB"], presets: [3, 6, 15, 24, 40] };
    }
    if (isSpeedControl()) {
      return {
        min: "1.01",
        max: "5",
        step: "0.01",
        labels: groupSlug === "speed" ? [groupedSpeedLabel(1.01), groupedSpeedLabel(5)] : ["x1.01", "x5"],
        presets: [1.25, 1.5, 2, 3, 5],
      };
    }
    return { min: "0", max: "0", step: "1", labels: ["", ""], presets: [] };
  }

  function valueInputConfig(): { min: string; max: string; step: string; label: string } {
    if (isVolumeControl()) {
      return { min: "1", max: "40", step: "0.5", label: t("settings.volume_step_db") };
    }
    if (isSpeedControl()) return { min: "1.01", max: "5", step: "0.01", label: t("settings.speed_step") };
    return { min: "0", max: "0", step: "1", label: "" };
  }

  function valueUnitConfig(): { unit: string; unitPosition: "prefix" | "suffix" } {
    return isVolumeControl()
      ? { unit: "dB", unitPosition: "suffix" }
      : { unit: isSpeedControl() ? "x" : "", unitPosition: isSpeedControl() ? "prefix" : "suffix" };
  }

  function applyValueInput(value: number): void {
    if (!Number.isFinite(value)) return;
    applyValue(value);
  }

  function applyValue(value: number): void {
    if (isVolumeControl()) onVolumeStep(value);
    else if (isSpeedControl()) onSpeedStep(value);
    onChange();
  }

  function optionValues(): string[] {
    return splitOptionValues(button.command);
  }

  function optionLabel(value: string): string {
    return splitOptionLabel(value);
  }

  function applyOption(value: string): void {
    if (value === "catbox" || value === "litterbox") onShareTarget(value);
    if (value === "gentle" || value === "normal" || value === "aggressive") {
      if (button.command === "aqe:reduce-size") onSizeReductionMode(value);
      else onPauseAggressiveness(value);
    }
    if (value === "standard" || value === "rnnoise" || value === "dpdfnet" || value === "voice_only") onDenoiseAlgorithm(value);
    if (isOutputFormatValue(value)) onOutputFormat(value);
    if (value === "direct" || value === "pitch_tier") onPitchHumMode(value);
    onChange();
  }

  function presetLabel(value: number): string {
    if (isVolumeControl()) return formatVolumeDb(value);
    if (groupSlug === "speed") return groupedSpeedLabel(value);
    if (isSpeedControl()) return formatSpeedStep(value, button.command);
    return "";
  }

  function runCommands(): readonly ButtonSpec["command"][] {
    if (groupSlug === "speed") return SPEED_RUN_COMMANDS;
    if (groupSlug === "volume") return VOLUME_RUN_COMMANDS;
    return showRunButton ? [button.command] : [];
  }

  function runLabel(command: ButtonSpec["command"]): string {
    if (command === "aqe:share") return t("editor.share.upload_and_copy_link");
    if (command === "aqe:pitch-hum") return t("editor.pitch_hum.hum_it_now");
    if (command === "aqe:slower") return t("editor.split.action.make_slower");
    if (command === "aqe:faster") return t("editor.split.action.make_faster");
    if (command === "aqe:volume-down") return t("editor.split.action.make_quieter");
    if (command === "aqe:volume-up") return t("editor.split.action.make_louder");
    return t("editor.split.run");
  }

  function runTitle(command: ButtonSpec["command"]): string {
    if (command === "aqe:share") return t("editor.command.share.title");
    if (command === "aqe:convert") return t("editor.command.convert.title", { format: formatOutputFormat(outputFormat) });
    if (command === "aqe:reduce-size") {
      return t("editor.command.reduce_size.title", { level: formatSizeReductionMode(sizeReductionMode) });
    }
    if (command === "aqe:remove-pauses") return t("editor.command.shorten_pauses.title");
    if (command === "aqe:pitch-hum") return t("editor.command.pitch_hum.title");
    if (command === "aqe:slower") return t("editor.command.slower.title");
    if (command === "aqe:faster") return t("editor.command.faster.title");
    if (command === "aqe:volume-down") return t("editor.command.volume_down.title");
    if (command === "aqe:volume-up") return t("editor.command.volume_up.title");
    if (
      command === "aqe:denoise-standard" ||
      command === "aqe:rnnoise" ||
      command === "aqe:dpdfnet" ||
      command === "aqe:voice-only"
    ) {
      return t("editor.command.denoise.title", { algorithm: formatDenoiseAlgorithm(denoiseAlgorithm) });
    }
    return t("editor.split.run_title", { label: menuLabel });
  }
</script>

<div class="aqe-split-popover-header aqe-split-popover-header-with-action">
  <span class="aqe-split-popover-title">
    <strong>{menuLabel}</strong>
    {#if !options.length}
      <UnitNumberInput
        inputClass="aqe-split-value-input"
        testId={`aqe-split-${targetOrd}-${slug}-value`}
        min={valueInputConfig().min}
        max={valueInputConfig().max}
        step={valueInputConfig().step}
        value={isSpeedControl() ? speedStep : sliderValue()}
        unit={valueUnitConfig().unit}
        unitPosition={valueUnitConfig().unitPosition}
        ariaLabel={valueInputConfig().label}
        onValueInput={applyValueInput}
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
<p class="aqe-split-popover-description">
  {splitMenuDescription(button.command, groupSlug, menuLabel)}
  {#if videoLink}
    <a
      class="aqe-split-video-link"
      href={videoLink}
      onclick={(event) => openEditorExternalLink(event, videoLink)}
      target="_blank"
      rel="noopener noreferrer"
    >
      {t("links.see_video")}
    </a>
  {/if}
</p>
{#if options.length}
  <SplitValuePresetGrid
    command={button.command}
    {dpdfnetAttnLimitDb}
    onSelect={applyOption}
    {optionLabel}
    {options}
    selectedLabel={selectedOptionLabel()}
    {slug}
    {targetOrd}
  />
  <SplitExtraFields
    command={button.command}
    {denoiseAlgorithm}
    {dpdfnetAttnLimitDb}
    {onChange}
    {onDpdfnetAttnLimitDb}
    {onPauseDetectionAlgorithm}
    {onPauseMinSilenceSeconds} {onPauseMinSpeechSeconds}
    {onPausePreprocessDenoise} {onPauseThreshold}
    {pauseMinSilenceSeconds} {pauseMinSpeechSeconds}
    {pausePreprocessDenoise} {pauseThreshold}
    {pauseDetectionAlgorithm}
    {onSizeReductionBitrateKbps} {onSizeReductionChannels}
    {onSizeReductionSampleRateHz} {sizeReductionBitrateKbps}
    {sizeReductionChannels} {sizeReductionSampleRateHz}
    {slug}
    {sourceFilename}
    {targetOrd}
  />
{:else}
  <ValueSlider
    testId={`aqe-split-${targetOrd}-${slug}-slider`}
    min={sliderConfig().min}
    max={sliderConfig().max}
    step={sliderConfig().step}
    value={sliderValue()}
    ariaLabel={valueInputConfig().label}
    formatValue={presetLabel}
    onValueInput={applyValue}
  />
  <div class="aqe-split-range-labels">
    <span>{sliderConfig().labels[0]}</span>
    <span>{sliderConfig().labels[1]}</span>
  </div>
  <div class="aqe-split-presets">
    {#each sliderConfig().presets as preset}
      <AqeTooltip>{#snippet trigger({ props })}
          <button
            {...props}
            type="button" class="aqe-button aqe-split-preset aqe-tooltip-target" data-aqe-tooltip-content={presetLabel(preset)}
            data-testid={`aqe-split-${targetOrd}-${slug}-preset-${preset}`}
            aria-pressed={sliderValue() === preset ? "true" : "false"} onclick={() => applyValue(preset)}>
            {presetLabel(preset)}
          </button>
        {/snippet}
      </AqeTooltip>
    {/each}
  </div>
{/if}
{#if showRunButton || groupSlug === "speed" || groupSlug === "volume"}
  <div class="aqe-split-popover-footer">
    <SplitRunButtons
      commands={runCommands()}
      labelFor={runLabel}
      onRun={onRunCommand}
      {slug}
      {targetOrd}
      titleFor={runTitle}
    />
  </div>
{/if}
