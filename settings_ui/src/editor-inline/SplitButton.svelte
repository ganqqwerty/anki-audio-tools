<script lang="ts">
  import { onMount } from "svelte";

  import EditorCommandIcon from "./EditorCommandIcon.svelte";
  import { send } from "./actions.js";
  import {
    buildSplitCommandPayload,
    formatDenoiseAlgorithm,
    formatPauseAggressiveness,
    formatSpeedStep,
    formatTrimMs,
    formatVolumeDb,
    getSplitButtonState,
    setDenoiseAlgorithmForField,
    setPauseAggressivenessForField,
    setSpeedStepForField,
    setTrimStepForField,
    setVolumeStepForField,
  } from "./split-button-state.js";
  import { COMMAND_SLUGS } from "./commands.js";
  import { t } from "../lib/i18n.js";
  import type { ButtonSpec, FieldTarget } from "./types.js";

  const { button, target }: { button: ButtonSpec; target: FieldTarget } = $props();
  let wrapper: HTMLSpanElement;
  let open = $state(false);
  let trimStepMs = $state(100);
  let volumeStepDb = $state(3);
  let speedStep = $state(0.05);
  let pauseAggressiveness = $state<"gentle" | "normal" | "aggressive">("normal");
  let denoiseAlgorithm = $state<"standard" | "rnnoise">("standard");

  function slug(): string {
    return COMMAND_SLUGS[button.command];
  }

  function close(): void {
    open = false;
  }

  function toggle(event: MouseEvent): void {
    event.preventDefault();
    event.stopPropagation();
    open = !open;
  }

  function applyTrimStep(value: number): void {
    trimStepMs = setTrimStepForField(target.ord, value).trimStepMs;
  }

  function applyVolumeStep(value: number): void {
    volumeStepDb = setVolumeStepForField(target.ord, value).volumeStepDb;
  }

  function applySpeedStep(value: number): void {
    speedStep = setSpeedStepForField(target.ord, value).speedStep;
  }

  function applyPauseAggressiveness(value: "gentle" | "normal" | "aggressive"): void {
    pauseAggressiveness = setPauseAggressivenessForField(target.ord, value).pauseAggressiveness;
  }

  function applyDenoiseAlgorithm(value: "standard" | "rnnoise"): void {
    denoiseAlgorithm = setDenoiseAlgorithmForField(target.ord, value).denoiseAlgorithm;
  }

  function dispatchPrimary(): void {
    close();
    send(button.command, target.node, target.ord, buildSplitCommandPayload(button.command, target.ord));
  }

  function valueLabel(): string {
    if (button.command === "aqe:volume-up" || button.command === "aqe:volume-down") {
      return formatVolumeDb(volumeStepDb);
    }
    if (button.command === "aqe:faster" || button.command === "aqe:slower") {
      return formatSpeedStep(speedStep, button.command);
    }
    if (button.command === "aqe:remove-pauses") return formatPauseAggressiveness(pauseAggressiveness);
    if (button.command === "aqe:denoise-standard" || button.command === "aqe:rnnoise") {
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
    if (button.command === "aqe:faster") {
      return { min: "1.01", max: "1.25", step: "0.01", label: "Faster speed multiplier" };
    }
    if (button.command === "aqe:slower") {
      return { min: "0.75", max: "0.99", step: "0.01", label: "Slower speed multiplier" };
    }
    return { min: "50", max: "10000", step: "50", label: "Trim step in milliseconds" };
  }

  function valueInputValue(): number {
    if (button.command === "aqe:faster") return Number((1 + speedStep).toFixed(2));
    if (button.command === "aqe:slower") return Number((1 - speedStep).toFixed(2));
    return sliderValue();
  }

  function applyValueInput(value: number): void {
    if (!Number.isFinite(value)) return;
    if (button.command === "aqe:faster") {
      applySpeedStep(value - 1);
      return;
    }
    if (button.command === "aqe:slower") {
      applySpeedStep(1 - value);
      return;
    }
    applyValue(value);
  }

  function applyValue(value: number): void {
    if (button.command === "aqe:volume-up" || button.command === "aqe:volume-down") {
      applyVolumeStep(value);
      return;
    }
    if (button.command === "aqe:faster" || button.command === "aqe:slower") {
      applySpeedStep(value);
      return;
    }
    applyTrimStep(value);
  }

  function optionValues(): string[] {
    if (button.command === "aqe:remove-pauses") return ["gentle", "normal", "aggressive"];
    if (button.command === "aqe:denoise-standard" || button.command === "aqe:rnnoise") return ["standard", "rnnoise"];
    return [];
  }

  function optionLabel(value: string): string {
    if (value === "rnnoise") return "RNNoise";
    if (value === "aggressive") return t("settings.pause_aggressiveness.aggressive");
    if (value === "gentle") return t("settings.pause_aggressiveness.gentle");
    return value === "standard" ? t("settings.denoise_algorithm.standard") : t("settings.pause_aggressiveness.normal");
  }

  function applyOption(value: string): void {
    if (value === "gentle" || value === "normal" || value === "aggressive") {
      applyPauseAggressiveness(value);
    }
    if (value === "standard" || value === "rnnoise") {
      applyDenoiseAlgorithm(value);
    }
  }

  function onDocumentPointerDown(event: MouseEvent): void {
    if (!open || !wrapper) return;
    if (event.target instanceof Node && wrapper.contains(event.target)) return;
    close();
  }

  function onDocumentKeyDown(event: KeyboardEvent): void {
    if (event.key === "Escape") close();
  }

  onMount(() => {
    const state = getSplitButtonState(target.ord);
    trimStepMs = state.trimStepMs;
    volumeStepDb = state.volumeStepDb;
    speedStep = state.speedStep;
    pauseAggressiveness = state.pauseAggressiveness;
    denoiseAlgorithm = state.denoiseAlgorithm;
    document.addEventListener("mousedown", onDocumentPointerDown, true);
    document.addEventListener("keydown", onDocumentKeyDown, true);
    return () => {
      document.removeEventListener("mousedown", onDocumentPointerDown, true);
      document.removeEventListener("keydown", onDocumentKeyDown, true);
    };
  });
</script>

<span class="aqe-split-button" bind:this={wrapper}>
  <button
    type="button"
    class:aqe-icon-only={button.iconOnly === true}
    class="aqe-button aqe-split-primary"
    data-aqe-command={button.command}
    data-aqe-button-state="default"
    data-testid={`aqe-button-${target.ord}-${slug()}`}
    title={button.title}
    aria-label={button.title}
    onmousedown={(event) => event.preventDefault()}
    onclick={dispatchPrimary}
  >
    <EditorCommandIcon icon={button.icon} />
    <span class="aqe-button-label">{button.label}</span>
  </button>
  <button
    type="button"
    class="aqe-button aqe-icon-only aqe-split-menu-button"
    data-testid={`aqe-split-${target.ord}-${slug()}-menu`}
    title={t("editor.split.options")}
    aria-label={t("editor.split.options")}
    aria-expanded={open ? "true" : "false"}
    onmousedown={(event) => event.preventDefault()}
    onclick={toggle}
  >
    <EditorCommandIcon icon="chevron-down" />
    <span class="aqe-button-label">{t("editor.split.options")}</span>
  </button>
  {#if open}
    <div class="aqe-split-popover" data-testid={`aqe-split-${target.ord}-${slug()}-popover`}>
      <div class="aqe-split-popover-header">
        <strong>{button.label}</strong>
        {#if optionValues().length}
          <span>{valueLabel()}</span>
        {:else}
          <input
            class="aqe-split-value-input"
            data-testid={`aqe-split-${target.ord}-${slug()}-value`}
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
      {#if optionValues().length}
        <div class="aqe-split-presets">
          {#each optionValues() as option}
            <button
              type="button"
              class="aqe-button aqe-split-preset"
              data-testid={`aqe-split-${target.ord}-${slug()}-preset-${option}`}
              aria-pressed={valueLabel() === optionLabel(option) ? "true" : "false"}
              onclick={() => applyOption(option)}
            >
              {optionLabel(option)}
            </button>
          {/each}
        </div>
      {:else}
        <input
          data-testid={`aqe-split-${target.ord}-${slug()}-slider`}
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
            data-testid={`aqe-split-${target.ord}-${slug()}-preset-${preset}`}
            aria-pressed={sliderValue() === preset ? "true" : "false"}
            onclick={() => applyValue(preset)}
          >
            {button.command === "aqe:volume-up" || button.command === "aqe:volume-down"
              ? formatVolumeDb(preset)
              : button.command === "aqe:faster" || button.command === "aqe:slower"
                ? formatSpeedStep(preset, button.command)
                : formatTrimMs(preset)}
          </button>
          {/each}
        </div>
      {/if}
    </div>
  {/if}
</span>
