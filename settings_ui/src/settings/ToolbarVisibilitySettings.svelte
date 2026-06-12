<script lang="ts">
  import {
    buttonDisplayMode,
    DEFAULT_EDITOR_BUTTON_MODES,
  } from "$lib/editor-toolbar-buttons.js";
  import { COMMAND_SLUGS } from "$lib/editor-toolbar-command-slugs.js";
  import { normalizeVisibleEditorButtons, toolbarPanels } from "$lib/editor-toolbar-visibility.js";
  import { t } from "$lib/i18n.js";
  import { settingsToolbarButtons } from "$lib/settings-toolbar-buttons.js";
  import type { Config } from "$lib/types.js";
  import type { EditorButtonDisplayMode, EditorCommand } from "$lib/editor-toolbar-buttons.js";
  import type { ToolbarPanelSpec } from "$lib/editor-toolbar-visibility.js";
  import ButtonSettingsCard from "./ButtonSettingsCard.svelte";
  import ToolbarPanelSettingsFields from "./ToolbarPanelSettingsFields.svelte";

  let { config = $bindable() }: { config: Config } = $props();
  const buttons = settingsToolbarButtons();
  const panels = toolbarPanels(buttons);

  function visibleSet(): Set<EditorCommand> {
    return new Set(
      normalizeVisibleEditorButtons(
        buttons,
        config.visible_editor_buttons as unknown as EditorCommand[] | undefined,
      ),
    );
  }

  function isVisible(panel: ToolbarPanelSpec): boolean {
    const visible = visibleSet();
    return panel.commands.some((command) => visible.has(command));
  }

  function setVisibleCommands(visible: Set<EditorCommand>): void {
    const selectedCommands = buttons
      .map((button) => button.command)
      .filter((command) => visible.has(command));
    config.visible_editor_buttons = normalizeVisibleEditorButtons(
      buttons,
      selectedCommands,
    ) as Config["visible_editor_buttons"];
  }

  function toggle(panel: ToolbarPanelSpec): void {
    const visible = visibleSet();
    if (panel.commands.some((command) => visible.has(command))) {
      for (const command of panel.commands) visible.delete(command);
    } else {
      for (const command of panel.commands) visible.add(command);
    }
    setVisibleCommands(visible);
  }

  function isCommandVisible(command: EditorCommand): boolean {
    return visibleSet().has(command);
  }

  function setCommandVisible(command: EditorCommand, nextVisible: boolean): void {
    const visible = visibleSet();
    if (nextVisible) {
      visible.add(command);
    } else {
      visible.delete(command);
    }
    setVisibleCommands(visible);
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
      command === "aqe:record-voice" ||
      command === "aqe:share" ||
      command === "aqe:convert" ||
      command === "aqe:reduce-size" ||
      command === "aqe:remove-pauses" ||
      command === "aqe:denoise-standard" ||
      command === "aqe:pitch-hum" ||
      command === "aqe:slower" ||
      command === "aqe:faster" ||
      command === "aqe:volume-down" ||
      command === "aqe:volume-up" ||
      command === "aqe:undo" ||
      command === "aqe:redo"
    );
  }

  function panelHasSettings(panel: ToolbarPanelSpec, visible: boolean): boolean {
    return (
      panel.commands.some((command) => hasSettings(command)) ||
      (panel.commands.includes("aqe:settings") && !visible)
    );
  }

  function modeControls(panel: ToolbarPanelSpec) {
    if (panel.buttons.length === 1) return undefined;
    return panel.buttons.map((button) => ({
      description: button.title,
      icon: button.icon,
      label: button.label,
      mode: displayMode(button.command),
      onToggleVisible: panel.atomicVisibility
        ? undefined
        : (nextVisible: boolean) => setCommandVisible(button.command, nextVisible),
      onSetMode: (nextMode: EditorButtonDisplayMode) => setDisplayMode(button.command, nextMode),
      testId: `button-settings-${COMMAND_SLUGS[button.command]}`,
      visible: isCommandVisible(button.command),
    }));
  }
</script>

<section class="toolbar-visibility settings-section" aria-labelledby="toolbar-visibility-title">
  <div class="toolbar-visibility-header settings-section-header">
    <h3 id="toolbar-visibility-title">{t("settings.toolbar_visibility.title")}</h3>
    <p>{t("settings.toolbar_visibility.summary")}</p>
  </div>

  <label class="settings-toggle">
    <input
      data-testid="enable-reviewer-editor"
      type="checkbox"
      bind:checked={config.enable_reviewer_editor}
    />
    <span class="settings-label-text">{t("settings.enable_reviewer_editor")}</span>
  </label>

  <div class="button-settings-grid" data-testid="toolbar-visibility-buttons">
    {#each panels as panel (panel.slug)}
      {@const visible = isVisible(panel)}
      {@const button = panel.primaryButton}
      {@const mode = displayMode(button.command)}
      <ButtonSettingsCard
        description={panel.description}
        hasSettings={panelHasSettings(panel, visible)}
        icon={panel.icon}
        mode={mode}
        modeControls={modeControls(panel)}
        onSetMode={(nextMode) => setDisplayMode(button.command, nextMode)}
        onToggle={() => toggle(panel)}
        testId={`button-settings-${panel.slug}`}
        title={panel.label}
        {visible}
      >
        <ToolbarPanelSettingsFields bind:config command={button.command} {visible} />
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
