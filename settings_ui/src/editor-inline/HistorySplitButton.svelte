<script lang="ts">
  import { onMount } from "svelte";
  import { Popover } from "bits-ui";
  import { t } from "../lib/i18n.js";

  import EditorCommandIcon from "./EditorCommandIcon.svelte";
  import SplitButtonPrimary from "./SplitButtonPrimary.svelte";
  import { send } from "./actions.js";
  import { historySnapshot } from "./control-actions.js";
  import { COMMAND_SLUGS } from "./commands.js";
  import type { ButtonSpec, FieldTarget, HistorySnapshotItem } from "./types.js";
  import type { EditorButtonDisplayMode } from "../lib/editor-toolbar-buttons.js";

  const {
    button,
    disabledTitle,
    displayMode,
    target,
  }: {
    button: ButtonSpec;
    disabledTitle?: string | undefined;
    displayMode: EditorButtonDisplayMode;
    target: FieldTarget;
  } = $props();

  let open = $state(false);
  let currentSnapshot = $state(historySnapshot(target.ord));
  const direction = $derived(button.command === "aqe:redo" ? "redo" : "undo");
  const slug = $derived(COMMAND_SLUGS[button.command]);
  const items = $derived(direction === "undo" ? currentSnapshot.undoItems : currentSnapshot.redoItems);
  const available = $derived(direction === "undo" ? currentSnapshot.canUndo : currentSnapshot.canRedo);
  const menuTitle = $derived(t("editor.history.menu_title", { label: button.label }));
  const primaryTitle = $derived(button.title);

  onMount(() => {
    currentSnapshot = historySnapshot(target.ord);
    function syncSnapshot(event: Event): void {
      const detail = (event as CustomEvent<{ ord?: number }>).detail;
      if (detail?.ord !== target.ord) return;
      currentSnapshot = historySnapshot(target.ord);
    }
    window.addEventListener("aqe-history-snapshot", syncSnapshot);
    return () => window.removeEventListener("aqe-history-snapshot", syncSnapshot);
  });

  function dispatchPrimary(): void {
    send(button.command, target.node, target.ord);
  }

  function dispatchJump(index: number): void {
    open = false;
    send("aqe:history-jump", target.node, target.ord, {
      command: "aqe:history-jump",
      direction,
      fieldOrd: target.ord,
      steps: index + 1,
    });
  }

  function rowLabel(item: HistorySnapshotItem): string {
    return item.label || (direction === "undo" ? t("editor.history.undo_empty_label") : t("editor.history.redo_empty_label"));
  }
</script>

<Popover.Root bind:open>
  <span class="aqe-split-button">
    <SplitButtonPrimary
      ariaLabel={primaryTitle}
      command={button.command}
      disabled={!available}
      disabledReason={disabledTitle}
      {displayMode}
      icon={button.icon}
      label={button.label}
      onClick={dispatchPrimary}
      ord={target.ord}
      primaryClass="aqe-button aqe-split-primary"
      slug={slug}
      title={primaryTitle}
    />
    <Popover.Trigger
      class="aqe-button aqe-icon-only aqe-split-menu-button"
      data-aqe-tooltip-content={menuTitle}
      data-testid={`aqe-split-${target.ord}-${slug}-menu`}
      disabled={!available || items.length === 0}
      aria-label={menuTitle}
    >
      <EditorCommandIcon icon="chevron-down" />
      <span class="aqe-button-label">{t("editor.split.options")}</span>
    </Popover.Trigger>
    <Popover.Content
      align="center"
      arrowPadding={14}
      class="aqe-ui-root aqe-split-popover aqe-history-split-popover"
      collisionPadding={8}
      data-testid={`aqe-split-${target.ord}-${slug}-popover`}
      onCloseAutoFocus={(event) => event.preventDefault()}
      side="bottom"
      sideOffset={4}
      strategy="fixed"
      trapFocus={false}
    >
      <Popover.Arrow class="aqe-split-popover-arrow" height={8} width={16} />
      <div class="aqe-history-menu" role="menu" aria-label={menuTitle}>
        {#each items as item, index (item.id)}
          <button
            class="aqe-history-menu-item"
            data-testid={`aqe-history-${target.ord}-${direction}-${index + 1}`}
            role="menuitem"
            type="button"
            onclick={() => dispatchJump(index)}
          >
            {rowLabel(item)}
          </button>
        {/each}
      </div>
    </Popover.Content>
  </span>
</Popover.Root>

<style>
  .aqe-history-menu {
    display: grid;
    gap: 2px;
    max-height: 280px;
    min-width: 180px;
    overflow: auto;
  }

  .aqe-history-menu-item {
    background: transparent;
    border: 0;
    color: inherit;
    font: inherit;
    padding: 6px 8px;
    text-align: left;
    width: 100%;
  }

  .aqe-history-menu-item:hover,
  .aqe-history-menu-item:focus-visible {
    background: var(--button-hover-bg, rgba(127, 127, 127, 0.14));
  }
</style>
