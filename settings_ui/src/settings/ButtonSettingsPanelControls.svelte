<script lang="ts" module>
  import type { EditorButtonDisplayMode } from "$lib/editor-toolbar-buttons.js";
  import type { CommandIconName } from "$lib/icon-types.js";

  export interface ButtonSettingsPanelControl {
    description?: string;
    icon: CommandIconName;
    label: string;
    mode: EditorButtonDisplayMode;
    modeLocked?: boolean;
    onSetMode: (mode: EditorButtonDisplayMode) => void;
    onToggleVisible?: ((visible: boolean) => void) | undefined;
    testId: string;
    visible?: boolean | undefined;
  }
</script>

<script lang="ts">
  import CommandIcon from "$lib/CommandIcon.svelte";
  import FieldTooltipTarget from "$lib/FieldTooltipTarget.svelte";
  import { t } from "$lib/i18n.js";
  import { EditorButtonMode } from "$lib/types.js";

  const {
    controls,
    testId,
  }: {
    controls: readonly ButtonSettingsPanelControl[];
    testId: string;
  } = $props();

  function lockedModeReason(locked: boolean | undefined): string | undefined {
    return locked ? t("settings.toolbar_visibility.mode_locked_tooltip") : undefined;
  }
</script>

<div class="button-settings-panel" data-testid={`${testId}-panel-controls`}>
  {#each controls as control (control.testId)}
    <div
      class:button-settings-panel-row-hidden={control.visible === false}
      class="button-settings-panel-row"
      data-testid={`${control.testId}-row`}
    >
      <span class="button-settings-panel-title-copy">
        <span class="button-settings-panel-title">
          <CommandIcon className="button-settings-panel-icon" icon={control.icon} />
          <span>{control.label}</span>
        </span>
        {#if control.description}
          <span class="button-settings-panel-description">{control.description}</span>
        {/if}
      </span>

      <span class="button-settings-panel-controls">
        {#if control.onToggleVisible}
          <label class="button-settings-checkbox">
            <input
              checked={control.visible !== false}
              data-testid={`${control.testId}-visibility-show`}
              type="checkbox"
              onchange={(event) => control.onToggleVisible?.((event.currentTarget as HTMLInputElement).checked)}
            />
            <span>{t("settings.toolbar_visibility.show")}</span>
          </label>
        {/if}

        <label class="button-settings-checkbox">
          <FieldTooltipTarget content={t("settings.toolbar_visibility.icon")} disabledReason={lockedModeReason(control.modeLocked)}>
            <input
              checked={control.mode === EditorButtonMode.Icon}
              data-testid={`${control.testId}-mode-icon`}
              disabled={control.modeLocked ?? false}
              type="checkbox"
              onchange={(event) =>
                control.onSetMode(
                  (event.currentTarget as HTMLInputElement).checked
                    ? EditorButtonMode.Icon
                    : EditorButtonMode.Text,
                )}
            />
          </FieldTooltipTarget>
          <span>{t("settings.toolbar_visibility.icon")}</span>
        </label>
      </span>
    </div>
  {/each}
</div>

<style>
  .button-settings-panel {
    align-content: start;
    background: var(--canvas-inset, rgba(0, 0, 0, 0.03));
    border: 1px solid var(--border, rgba(0, 0, 0, 0.12));
    border-radius: 6px;
    box-shadow: inset 3px 0 0 var(--button-bg, rgba(0, 0, 0, 0.18));
    display: grid;
    gap: 0;
    grid-column: 2;
    min-width: 0;
    padding: 4px 10px;
  }

  .button-settings-panel-row {
    align-items: center;
    display: grid;
    gap: 10px;
    grid-template-columns: minmax(0, 1fr) auto;
    min-height: 38px;
    padding: 6px 0;
  }

  .button-settings-panel-row + .button-settings-panel-row {
    border-top: 1px solid var(--border, rgba(0, 0, 0, 0.12));
  }

  .button-settings-panel-row-hidden {
    color: var(--fg-subtle, currentColor);
  }

  .button-settings-panel-title {
    align-items: center;
    display: flex;
    font-size: 0.86rem;
    gap: 8px;
    min-width: 0;
  }

  .button-settings-panel-title span {
    overflow-wrap: anywhere;
  }

  .button-settings-panel-title-copy {
    display: grid;
    gap: 3px;
    min-width: 0;
  }

  .button-settings-panel-description {
    color: var(--fg-subtle, currentColor);
    font-size: 0.78rem;
    line-height: 1.35;
    overflow-wrap: anywhere;
  }

  :global(.button-settings-panel-icon) {
    align-items: center;
    color: var(--fg, currentColor);
    display: inline-flex;
    flex: 0 0 auto;
  }

  .button-settings-panel-controls {
    align-items: center;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: end;
  }

  .button-settings-checkbox {
    align-items: center;
    cursor: pointer;
    display: inline-flex;
    font-size: 12px;
    font-weight: 400;
    gap: 4px;
    min-height: 27px;
  }

  .button-settings-checkbox input {
    margin: 0;
  }

  @media (max-width: 720px) {
    .button-settings-panel {
      grid-column: 1;
    }

    .button-settings-panel-row {
      grid-template-columns: 1fr;
    }

    .button-settings-panel-controls {
      justify-content: start;
    }
  }
</style>
