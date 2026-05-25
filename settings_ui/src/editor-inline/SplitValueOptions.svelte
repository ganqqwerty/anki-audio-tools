<script lang="ts">
  import AqeTooltip from "../lib/AqeTooltip.svelte";
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
  import { openEditorExternalLink } from "./external-links.js";
  import { DPDFNET_ATTENUATION_LIMIT_DB_VALUES, isOutputFormatValue } from "../lib/audio-operation-parameters.js";
  import {
    splitMenuDescription,
    splitMenuVideoLink,
    splitOptionDescription,
    splitOptionLabel,
    splitOptionTitle,
    splitOptionValues,
  } from "./split-menu-content.js";
  import SplitDefaultSaveButton from "./SplitDefaultSaveButton.svelte";
  import SplitRunButtons from "./SplitRunButtons.svelte";
  import type { ButtonSpec, FieldSplitButtonState } from "./types.js";

  type DenoiseAlgorithm = FieldSplitButtonState["denoiseAlgorithm"];
  type OutputFormatValue = FieldSplitButtonState["outputFormat"];
  type PitchHumMode = FieldSplitButtonState["pitchHumMode"];
  type ShareTarget = FieldSplitButtonState["shareTarget"];

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
    onPitchHumMode,
    onSaveDefault,
    onRunCommand,
    onShareTarget,
    onSpeedStep,
    onVolumeStep,
    pauseAggressiveness,
    outputFormat,
    pitchHumMode,
    saveDefaultSaved,
    shareTarget,
    showRunButton,
    showSaveDefault,
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
    onPitchHumMode: (value: PitchHumMode) => void;
    onSaveDefault: () => void;
    onRunCommand: (command: ButtonSpec["command"]) => void;
    onShareTarget: (value: ShareTarget) => void;
    onSpeedStep: (value: number) => void;
    onVolumeStep: (value: number) => void;
    pauseAggressiveness: "gentle" | "normal" | "aggressive";
    outputFormat: OutputFormatValue;
    pitchHumMode: PitchHumMode;
    saveDefaultSaved: boolean;
    shareTarget: ShareTarget;
    showRunButton: boolean;
    showSaveDefault: boolean;
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

  function descriptionText(): string {
    return splitMenuDescription(button.command, groupSlug, menuLabel);
  }

  function selectedOptionLabel(): string {
    if (isVolumeControl()) return formatVolumeDb(volumeStepDb);
    if (groupSlug === "speed") return groupedSpeedLabel(speedStep);
    if (isSpeedControl()) return formatSpeedStep(speedStep, button.command);
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

  function sliderValue(): number {
    if (isVolumeControl()) return volumeStepDb;
    if (isSpeedControl()) return speedStep;
    return 0;
  }

  function sliderConfig(): { min: string; max: string; step: string; labels: string[]; presets: number[] } {
    if (isVolumeControl()) {
      return { min: "1", max: "40", step: "0.5", labels: ["1 dB", "40 dB"], presets: [3, 6, 15, 24, 40] };
    }
    if (groupSlug === "speed") {
      return {
        min: "1.01",
        max: "5",
        step: "0.01",
        labels: [groupedSpeedLabel(1.01), groupedSpeedLabel(5)],
        presets: [1.25, 1.5, 2, 3, 5],
      };
    }
    if (isSpeedControl()) {
      return { min: "1.01", max: "5", step: "0.01", labels: ["x1.01", "x5"], presets: [1.25, 1.5, 2, 3, 5] };
    }
    return { min: "0", max: "0", step: "1", labels: ["", ""], presets: [] };
  }

  function valueInputConfig(): { min: string; max: string; step: string; label: string } {
    if (isVolumeControl()) {
      return { min: "1", max: "40", step: "0.5", label: t("settings.volume_step_db") };
    }
    if (groupSlug === "speed") {
      return { min: "1.01", max: "5", step: "0.01", label: t("settings.speed_step") };
    }
    if (isSpeedControl()) return { min: "1.01", max: "5", step: "0.01", label: t("settings.speed_step") };
    return { min: "0", max: "0", step: "1", label: "" };
  }

  function valueInputValue(): number {
    if (isSpeedControl()) return speedStep;
    return sliderValue();
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

  function optionTitle(value: string): string {
    return splitOptionTitle(value, dpdfnetAttnLimitDb);
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
<p class="aqe-split-popover-description">
  {descriptionText()}
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
  <div class="aqe-split-presets">
    {#each options as option}
      <AqeTooltip>
        {#snippet trigger({ props })}
          <button
            {...props}
            type="button"
            class="aqe-button aqe-split-preset aqe-tooltip-target"
            data-aqe-tooltip-content={optionTitle(option)}
            data-testid={`aqe-split-${targetOrd}-${slug}-preset-${option}`}
            aria-pressed={selectedOptionLabel() === optionLabel(option) ? "true" : "false"}
            onclick={() => applyOption(option)}
          >
            <span class="aqe-split-preset-label">{optionLabel(option)}</span>
            {#if splitOptionDescription(option)}
              <span class="aqe-split-preset-description">{splitOptionDescription(option)}</span>
            {/if}
          </button>
        {/snippet}
      </AqeTooltip>
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
