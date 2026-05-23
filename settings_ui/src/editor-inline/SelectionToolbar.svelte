<script lang="ts">
  import AqeTooltip from "../lib/AqeTooltip.svelte";
  import EditorCommandIcon from "./EditorCommandIcon.svelte";
  import { send } from "./actions.js";
  import { sendRegionDelete } from "./region-delete.js";
  import {
    collapseSelectionToolbarForOrd,
    expandSelectionToolbarForOrd,
    setSelectionToolbarPreviewForOrd,
  } from "./selection-toolbar-state.js";
  import { t } from "../lib/i18n.js";
  import type { FieldTarget } from "./types.js";

  const { target }: { target: FieldTarget } = $props();

  function expandCollapsedToolbar(): void {
    expandSelectionToolbarForOrd(target.ord);
  }

  function expandCollapsedToolbarFromKeyboard(event: KeyboardEvent): void {
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    event.stopPropagation();
    expandCollapsedToolbar();
  }
</script>

<div class="aqe-selection-rest-preview aqe-selection-rest-preview-before" aria-hidden="true"></div>
<div class="aqe-selection-rest-preview aqe-selection-rest-preview-after" aria-hidden="true"></div>
<div
  class="aqe-selection-toolbar"
  data-testid={`aqe-selection-toolbar-${target.ord}`}
  role="toolbar"
  aria-label="Selection actions"
  hidden
>
  <AqeTooltip>
    {#snippet trigger({ props })}
      <button
        {...props}
        type="button"
        class="aqe-button aqe-selection-toolbar-button aqe-selection-toolbar-play aqe-tooltip-target"
        data-aqe-button-state="play"
        data-aqe-tooltip-content="Play selection"
        data-testid={`aqe-selection-toolbar-play-${target.ord}`}
        aria-label="Play selection"
        onpointerdown={(event) => event.stopPropagation()}
        onmousedown={(event) => event.preventDefault()}
        onclick={() => send("aqe:play", target.node, target.ord)}
      >
        <EditorCommandIcon className="aqe-button-icon-default" icon="play" />
        <EditorCommandIcon className="aqe-button-icon-active" icon="pause" />
      </button>
    {/snippet}
  </AqeTooltip>
  <AqeTooltip>
    {#snippet trigger({ props })}
      <button
        {...props}
        type="button"
        class="aqe-button aqe-selection-toolbar-button aqe-delete-region-button aqe-tooltip-target"
        data-aqe-command="aqe:delete-selection"
        data-aqe-button-state="default"
        data-aqe-tooltip-content={t("editor.command.delete_region.title")}
        data-testid={`aqe-selection-toolbar-delete-region-${target.ord}`}
        aria-label={t("editor.command.delete_region.title")}
        hidden
        onpointerdown={(event) => event.stopPropagation()}
        onmousedown={(event) => event.preventDefault()}
        onfocus={() => setSelectionToolbarPreviewForOrd(target.ord, "region")}
        onblur={() => setSelectionToolbarPreviewForOrd(target.ord, "none")}
        onmouseenter={() => setSelectionToolbarPreviewForOrd(target.ord, "region")}
        onmouseleave={() => setSelectionToolbarPreviewForOrd(target.ord, "none")}
        onclick={() => sendRegionDelete("button", target.node, target.ord)}
      >
        <EditorCommandIcon icon="selection-remove-inside" />
      </button>
    {/snippet}
  </AqeTooltip>
  <AqeTooltip>
    {#snippet trigger({ props })}
      <button
        {...props}
        type="button"
        class="aqe-button aqe-selection-toolbar-button aqe-delete-rest-button aqe-tooltip-target"
        data-aqe-command="aqe:delete-rest"
        data-aqe-button-state="default"
        data-aqe-tooltip-content="Delete audio outside selected region"
        data-testid={`aqe-selection-toolbar-delete-rest-${target.ord}`}
        aria-label="Delete audio outside selected region"
        hidden
        onpointerdown={(event) => event.stopPropagation()}
        onmousedown={(event) => event.preventDefault()}
        onfocus={() => setSelectionToolbarPreviewForOrd(target.ord, "rest")}
        onblur={() => setSelectionToolbarPreviewForOrd(target.ord, "none")}
        onmouseenter={() => setSelectionToolbarPreviewForOrd(target.ord, "rest")}
        onmouseleave={() => setSelectionToolbarPreviewForOrd(target.ord, "none")}
        onclick={() => sendRegionDelete("button", target.node, target.ord, "delete-rest")}
      >
        <EditorCommandIcon icon="selection-remove-outside" />
      </button>
    {/snippet}
  </AqeTooltip>
  <AqeTooltip>
    {#snippet trigger({ props })}
      <button
        {...props}
        type="button"
        class="aqe-button aqe-selection-toolbar-button aqe-selection-toolbar-collapse aqe-tooltip-target"
        data-aqe-tooltip-content="Collapse selection actions"
        data-testid={`aqe-selection-toolbar-collapse-${target.ord}`}
        aria-label="Collapse selection actions"
        onpointerdown={(event) => event.stopPropagation()}
        onmousedown={(event) => event.preventDefault()}
        onclick={() => collapseSelectionToolbarForOrd(target.ord)}
      >
        <EditorCommandIcon icon="x" />
      </button>
    {/snippet}
  </AqeTooltip>
</div>
<AqeTooltip>
  {#snippet trigger({ props })}
    <svg
      {...props}
      class="aqe-selection-toolbar-dot aqe-tooltip-target"
      data-aqe-tooltip-content="Expand selection actions"
      data-testid={`aqe-selection-toolbar-dot-${target.ord}`}
      viewBox="0 0 18 18"
      role="button"
      tabindex="0"
      aria-label="Expand selection actions"
      onpointerdown={(event) => event.stopPropagation()}
      onmousedown={(event) => event.preventDefault()}
      onkeydown={expandCollapsedToolbarFromKeyboard}
      onclick={expandCollapsedToolbar}
      aria-hidden="true"
    >
      <circle class="aqe-selection-toolbar-dot-halo" cx="9" cy="9" r="6.25"></circle>
      <circle class="aqe-selection-toolbar-dot-ring" cx="9" cy="9" r="4.75"></circle>
    </svg>
  {/snippet}
</AqeTooltip>
