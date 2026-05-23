<script lang="ts">
  import CommandIcon from "$lib/CommandIcon.svelte";
  import {
    buttonDisplayMode,
    DEFAULT_EDITOR_BUTTON_MODES,
  } from "$lib/editor-toolbar-buttons.js";
  import { t } from "$lib/i18n.js";
  import type { Config } from "$lib/types.js";
  import {
    COMMAND_SLUGS,
    DEFAULT_VISIBLE_EDITOR_BUTTONS,
    toolbarButtons,
  } from "$lib/editor-toolbar-buttons.js";
  import { EditorButtonMode } from "$lib/types.js";
  import type {
    EditorButtonDisplayMode,
    EditorCommand,
  } from "$lib/editor-toolbar-buttons.js";

  const { config = $bindable() }: { config: Config } = $props();
  const buttons = toolbarButtons();

  function visibleSet(): Set<EditorCommand> {
    if (!Array.isArray(config.visible_editor_buttons)) {
      return new Set(DEFAULT_VISIBLE_EDITOR_BUTTONS);
    }
    return new Set(config.visible_editor_buttons as unknown as EditorCommand[]);
  }

  function isVisible(command: EditorCommand): boolean {
    return visibleSet().has(command);
  }

  function toggle(command: EditorCommand): void {
    const visible = visibleSet();
    if (visible.has(command)) {
      visible.delete(command);
    } else {
      visible.add(command);
    }
    config.visible_editor_buttons = DEFAULT_VISIBLE_EDITOR_BUTTONS.filter((item) => visible.has(item)) as Config[
      "visible_editor_buttons"
    ];
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
</script>

<section class="toolbar-visibility settings-section" aria-labelledby="toolbar-visibility-title">
  <div class="toolbar-visibility-header settings-section-header">
    <h3 id="toolbar-visibility-title">{t("settings.toolbar_visibility.title")}</h3>
    <p>{t("settings.toolbar_visibility.summary")}</p>
  </div>
  <div class="toolbar-button-grid" data-testid="toolbar-visibility-buttons">
    {#each buttons as button (button.command)}
      {@const visible = isVisible(button.command)}
      {@const mode = displayMode(button.command)}
      <div class="toolbar-button-card" data-command={button.command}>
        <button
          type="button"
          class:toolbar-button-off={!visible}
          class="toolbar-button"
          data-testid={`toolbar-visibility-${COMMAND_SLUGS[button.command]}`}
          aria-pressed={visible ? "true" : "false"}
          title={button.title}
          onclick={() => toggle(button.command)}
        >
          {#if mode === EditorButtonMode.Icon}
            <CommandIcon className="toolbar-button-icon" icon={button.icon} />
            <span class="toolbar-button-label">{button.label}</span>
          {:else}
            <span class="toolbar-button-label">{button.label}</span>
          {/if}
          {#if !visible}
            <span class="toolbar-button-off-label">{t("settings.toolbar_visibility.off")}</span>
          {/if}
        </button>
        <div class="toolbar-mode-toggle" role="group" aria-label={button.label}>
          <button
            type="button"
            class:toolbar-mode-active={mode === EditorButtonMode.Text}
            data-testid={`toolbar-mode-${COMMAND_SLUGS[button.command]}-text`}
            aria-pressed={mode === EditorButtonMode.Text ? "true" : "false"}
            onclick={() => setDisplayMode(button.command, EditorButtonMode.Text)}
          >
            {t("settings.toolbar_visibility.text_only")}
          </button>
          <button
            type="button"
            class:toolbar-mode-active={mode === EditorButtonMode.Icon}
            data-testid={`toolbar-mode-${COMMAND_SLUGS[button.command]}-icon`}
            aria-pressed={mode === EditorButtonMode.Icon ? "true" : "false"}
            onclick={() => setDisplayMode(button.command, EditorButtonMode.Icon)}
          >
            {t("settings.toolbar_visibility.icon_only")}
          </button>
        </div>
      </div>
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

  .toolbar-button-grid {
    display: grid;
    gap: 10px;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  }

  .toolbar-button-card {
    display: grid;
    gap: 8px;
  }

  .toolbar-button {
    align-items: center;
    background: color-mix(in srgb, var(--canvas-inset, transparent) 58%, transparent);
    border: 1px solid color-mix(in srgb, var(--border-subtle, var(--border, currentColor)) 72%, transparent);
    border-radius: 18px;
    color: var(--fg, currentColor);
    cursor: pointer;
    display: inline-flex;
    font: inherit;
    font-size: 0.84rem;
    gap: 6px;
    justify-content: flex-start;
    min-height: 44px;
    padding: 10px 12px;
    transition:
      background-color 120ms ease,
      border-color 120ms ease,
      transform 120ms ease;
  }

  .toolbar-button:hover {
    background: var(--button-gradient-start, var(--button-bg, transparent));
    border-color: var(--button-hover-border, var(--border, currentColor));
    transform: translateY(-1px);
  }

  .toolbar-button-off {
    background: color-mix(in srgb, var(--accent-danger, #b42318) 9%, transparent);
    border-color: color-mix(in srgb, var(--accent-danger, #b42318) 48%, var(--border, currentColor));
    color: color-mix(in srgb, var(--accent-danger, #b42318) 72%, var(--fg, currentColor));
  }

  :global(.toolbar-button-icon) {
    align-items: center;
    display: inline-flex;
    flex: 0 0 auto;
  }

  .toolbar-button-off-label {
    border: 1px solid currentColor;
    border-radius: 999px;
    font-size: 0.68rem;
    font-weight: 700;
    line-height: 1;
    padding: 2px 5px;
  }

  .toolbar-mode-toggle {
    display: grid;
    gap: 8px;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .toolbar-mode-toggle button {
    background: color-mix(in srgb, var(--canvas-inset, transparent) 58%, transparent);
    border: 1px solid color-mix(in srgb, var(--border-subtle, var(--border, currentColor)) 72%, transparent);
    border-radius: 14px;
    color: var(--fg, currentColor);
    cursor: pointer;
    font: inherit;
    font-size: 0.76rem;
    min-height: 38px;
    padding: 7px 10px;
    transition:
      background-color 120ms ease,
      border-color 120ms ease,
      transform 120ms ease;
  }

  .toolbar-mode-toggle button:hover {
    background: var(--button-gradient-start, var(--button-bg, transparent));
    border-color: var(--button-hover-border, var(--border, currentColor));
    transform: translateY(-1px);
  }

  .toolbar-mode-active {
    background: color-mix(in srgb, var(--button-gradient-start, var(--button-bg, transparent)) 72%, transparent);
    border-color: var(--border-focus, var(--border, currentColor));
    font-weight: 700;
  }
</style>
