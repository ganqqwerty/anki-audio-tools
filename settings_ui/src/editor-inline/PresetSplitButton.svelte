<script lang="ts">
  import { Popover } from "bits-ui";
  import AqeTooltip from "../lib/AqeTooltip.svelte";
  import { EditorButtonMode } from "../lib/types.js";
  import { t } from "../lib/i18n.js";
  import type { EditorButtonDisplayMode } from "../lib/editor-toolbar-buttons.js";
  import EditorCommandIcon from "./EditorCommandIcon.svelte";
  import { send } from "./actions.js";
  import { COMMAND_SLUGS, testId } from "./commands.js";
  import type { ButtonSpec, EditorRuntimeConfig, FieldTarget } from "./types.js";

  type ProcessingPresetOption = NonNullable<EditorRuntimeConfig["processingPresets"]>[number];

  const {
    button,
    displayMode,
    target,
  }: {
    button: ButtonSpec;
    displayMode: EditorButtonDisplayMode;
    target: FieldTarget;
  } = $props();

  const presets = window.__AQE_EDITOR_CONFIG__?.processingPresets ?? [];
  let open = $state(false);
  let presetId = $state(presets[0]?.id ?? "");
  const selectedPreset = $derived(
    presets.find((preset: ProcessingPresetOption) => preset.id === presetId) ?? presets[0],
  );

  function runPreset(): void {
    if (!selectedPreset) return;
    open = false;
    send(button.command, target.node, target.ord, {
      command: "aqe:preset",
      fieldOrd: target.ord,
      presetId: selectedPreset.id,
    });
  }

  function buttonTitle(): string {
    return selectedPreset
      ? t("editor.status.running_preset", { preset: selectedPreset.name })
      : t("editor.command.preset.title");
  }
</script>

<Popover.Root bind:open>
  <span class="aqe-split-button">
    <AqeTooltip>
      {#snippet trigger({ props })}
        <span
          {...props}
          class="aqe-button-tooltip-target aqe-tooltip-target"
          data-aqe-tooltip-content={buttonTitle()}
        >
          <button
            type="button"
            class:aqe-icon-only={displayMode === EditorButtonMode.Icon}
            class="aqe-button aqe-split-primary"
            data-aqe-command={button.command}
            data-aqe-button-state="default"
            data-aqe-enabled-title={buttonTitle()}
            data-testid={testId(target.ord, button.command)}
            disabled={!selectedPreset}
            aria-label={buttonTitle()}
            onmousedown={(event) => event.preventDefault()}
            onclick={runPreset}
          >
            {#if displayMode === EditorButtonMode.Icon}
              <EditorCommandIcon className="aqe-button-icon-default" icon={button.icon} />
              <span class="aqe-button-label">{button.label}</span>
            {:else}
              <span class="aqe-button-label">{button.label}</span>
            {/if}
          </button>
        </span>
      {/snippet}
    </AqeTooltip>
    <Popover.Trigger
      class="aqe-button aqe-icon-only aqe-split-menu-button"
      data-aqe-tooltip-content={t("editor.split.menu_title", {
        label: button.label,
        value: selectedPreset?.name ?? t("editor.command.preset.label"),
      })}
      data-testid={`aqe-split-${target.ord}-${COMMAND_SLUGS[button.command]}-menu`}
      aria-label={t("editor.split.menu_title", {
        label: button.label,
        value: selectedPreset?.name ?? t("editor.command.preset.label"),
      })}
      disabled={presets.length === 0}
    >
      <EditorCommandIcon icon="chevron-down" />
      <span class="aqe-button-label">{t("editor.split.options")}</span>
    </Popover.Trigger>
    <Popover.Content
      align="center"
      arrowPadding={14}
      class="aqe-split-popover aqe-preset-split-popover"
      collisionPadding={8}
      data-testid={`aqe-split-${target.ord}-${COMMAND_SLUGS[button.command]}-popover`}
      onCloseAutoFocus={(event) => event.preventDefault()}
      side="bottom"
      sideOffset={4}
      strategy="fixed"
      trapFocus={false}
    >
      <Popover.Arrow
        class="aqe-split-popover-arrow"
        data-testid={`aqe-split-${target.ord}-${COMMAND_SLUGS[button.command]}-arrow`}
        height={8}
        width={16}
      />
      <div class="aqe-split-popover-header">
        <span class="aqe-split-popover-title">
          <strong>{button.label}</strong>
        </span>
      </div>
      <label class="aqe-preset-select-field">
        <span>{t("editor.command.preset.label")}</span>
        <select bind:value={presetId} data-testid={`aqe-split-${target.ord}-preset-select`}>
          {#each presets as preset}
            <option value={preset.id}>{preset.name}</option>
          {/each}
        </select>
      </label>
      <div class="aqe-split-popover-footer">
        <button
          type="button"
          class="aqe-button aqe-split-run-button"
          data-testid={`aqe-split-${target.ord}-preset-run`}
          disabled={!selectedPreset}
          onclick={runPreset}
        >
          {t("editor.command.preset.label")}
        </button>
      </div>
    </Popover.Content>
  </span>
</Popover.Root>

<style>
  .aqe-preset-select-field {
    display: grid;
    gap: 6px;
  }

  .aqe-preset-select-field span {
    color: var(--aqe-muted, currentColor);
    font-size: 11px;
    font-weight: 700;
  }

  .aqe-preset-select-field select {
    background: var(--canvas-elevated, Field);
    border: 1px solid var(--border, ButtonBorder);
    border-radius: 6px;
    box-sizing: border-box;
    color: var(--fg, FieldText);
    font: inherit;
    font-size: 11px;
    min-height: 30px;
    padding: 4px 8px;
    width: 100%;
  }
</style>
