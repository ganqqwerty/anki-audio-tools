<script lang="ts">
  import CommandIcon from "$lib/CommandIcon.svelte";
  import { t } from "$lib/i18n.js";
  import type { Config } from "$lib/types.js";
  import {
    COMMAND_SLUGS,
    DEFAULT_VISIBLE_EDITOR_BUTTONS,
    toolbarButtons,
  } from "$lib/editor-toolbar-buttons.js";
  import type { EditorCommand } from "$lib/editor-toolbar-buttons.js";

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
</script>

<section class="toolbar-visibility" aria-labelledby="toolbar-visibility-title">
  <div class="toolbar-visibility-header">
    <h3 id="toolbar-visibility-title">{t("settings.toolbar_visibility.title")}</h3>
    <p>{t("settings.toolbar_visibility.summary")}</p>
  </div>
  <div class="toolbar-button-grid" data-testid="toolbar-visibility-buttons">
    {#each buttons as button (button.command)}
      {@const visible = isVisible(button.command)}
      <button
        type="button"
        class:toolbar-button-off={!visible}
        class:toolbar-icon-only={button.iconOnly === true}
        class="toolbar-button"
        data-command={button.command}
        data-testid={`toolbar-visibility-${COMMAND_SLUGS[button.command]}`}
        aria-pressed={visible ? "true" : "false"}
        title={button.title}
        onclick={() => toggle(button.command)}
      >
        <CommandIcon className="toolbar-button-icon" icon={button.icon} />
        <span class="toolbar-button-label">{button.label}</span>
        {#if !visible}
          <span class="toolbar-button-off-label">{t("settings.toolbar_visibility.off")}</span>
        {/if}
      </button>
    {/each}
  </div>
</section>

<style>
  .toolbar-visibility {
    border-top: 1px solid var(--border-subtle, var(--border, currentColor));
    display: grid;
    gap: 12px;
    margin-top: 18px;
    padding-top: 18px;
  }

  .toolbar-visibility-header {
    display: grid;
    gap: 4px;
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
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .toolbar-button {
    align-items: center;
    background: var(--button-bg, transparent);
    border: 1px solid var(--border, currentColor);
    border-radius: 7px;
    color: var(--fg, currentColor);
    cursor: pointer;
    display: inline-flex;
    font: inherit;
    font-size: 0.82rem;
    gap: 6px;
    min-height: 32px;
    padding: 6px 9px;
  }

  .toolbar-button:hover {
    background: var(--button-gradient-start, var(--button-bg, transparent));
    border-color: var(--button-hover-border, var(--border, currentColor));
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

  .toolbar-icon-only {
    gap: 0;
    justify-content: center;
    min-width: 34px;
    padding-left: 8px;
    padding-right: 8px;
  }

  .toolbar-icon-only .toolbar-button-label {
    clip: rect(0 0 0 0);
    clip-path: inset(50%);
    height: 1px;
    overflow: hidden;
    position: absolute;
    white-space: nowrap;
    width: 1px;
  }

  .toolbar-button-off-label {
    border: 1px solid currentColor;
    border-radius: 999px;
    font-size: 0.68rem;
    font-weight: 700;
    line-height: 1;
    padding: 2px 5px;
  }
</style>
