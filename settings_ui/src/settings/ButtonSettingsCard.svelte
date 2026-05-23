<script lang="ts">
  import CommandIcon from "$lib/CommandIcon.svelte";
  import { t } from "$lib/i18n.js";
  import { EditorButtonMode } from "$lib/types.js";
  import type { CommandIconName } from "$lib/icon-types.js";
  import type { EditorButtonDisplayMode } from "$lib/editor-toolbar-buttons.js";
  import type { Snippet } from "svelte";

  const {
    icon,
    mode,
    onSetMode,
    onToggle,
    testId,
    title,
    visible,
    children,
  }: {
    children?: Snippet;
    icon: CommandIconName;
    mode: EditorButtonDisplayMode;
    onSetMode: (mode: EditorButtonDisplayMode) => void;
    onToggle: () => void;
    testId: string;
    title: string;
    visible: boolean;
  } = $props();
</script>

<section class:button-settings-card-hidden={!visible} class="button-settings-card" data-testid={testId}>
  <header class="button-settings-card-header">
    <span class="button-settings-card-title">
      <CommandIcon className="button-settings-card-icon" {icon} />
      <h4>{title}</h4>
    </span>

    <span class="button-settings-controls">
      <label class="button-settings-checkbox">
        <input
          checked={visible}
          data-testid={`${testId}-visibility-show`}
          type="checkbox"
          onchange={(event) => {
            if ((event.currentTarget as HTMLInputElement).checked !== visible) onToggle();
          }}
        />
        <span>{t("settings.toolbar_visibility.show")}</span>
      </label>

      <label class="button-settings-checkbox">
        <input
          checked={mode === EditorButtonMode.Icon}
          data-testid={`${testId}-mode-icon`}
          type="checkbox"
          onchange={(event) =>
            onSetMode((event.currentTarget as HTMLInputElement).checked ? EditorButtonMode.Icon : EditorButtonMode.Text)}
        />
        <span>{t("settings.toolbar_visibility.icon")}</span>
      </label>
    </span>
  </header>

  <div class="button-settings-card-body">
    {#if children}
      {@render children()}
    {/if}
  </div>
</section>

<style>
  .button-settings-card {
    align-content: start;
    align-self: start;
    display: grid;
    gap: 8px 16px;
    grid-template-columns: minmax(130px, 190px) minmax(0, 1fr);
    padding: 10px 0 12px;
  }

  .button-settings-card-hidden {
    color: var(--fg-subtle, currentColor);
  }

  .button-settings-card-header {
    align-content: start;
    display: grid;
    gap: 6px;
    min-height: 27px;
  }

  .button-settings-card-title {
    align-items: center;
    display: flex;
    gap: 8px;
    min-width: 0;
  }

  .button-settings-card-header h4 {
    font-size: 0.9rem;
    margin: 0;
  }

  :global(.button-settings-card-icon) {
    align-items: center;
    color: var(--fg, currentColor);
    display: inline-flex;
    flex: 0 0 auto;
  }

  .button-settings-controls {
    align-items: start;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
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

  .button-settings-card-body {
    display: grid;
    grid-column: 2;
    gap: 12px;
  }

  .button-settings-card-body:empty {
    display: none;
  }

  @media (max-width: 720px) {
    .button-settings-card {
      grid-template-columns: 1fr;
    }

    .button-settings-card-body {
      grid-column: 1;
    }
  }
</style>
