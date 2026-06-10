<script lang="ts">
  import AqeTooltip from "../lib/AqeTooltip.svelte";
  import { buttonTooltipContent } from "../lib/disabled-tooltip.js";
  import EditorCommandIcon from "./EditorCommandIcon.svelte";
  import { send } from "./actions.js";
  import { sendRegionDelete } from "./region-delete.js";
  import { setSelectionToolbarPreviewForOrd } from "./selection-toolbar-state.js";
  import { t } from "../lib/i18n.js";
  import { buttonDisplayMode } from "../lib/editor-toolbar-buttons.js";
  import { EditorButtonMode } from "../lib/types.js";
  import type { FieldTarget } from "./types.js";

  const {
    buttonModes,
    target,
    visibleCommands,
  }: {
    buttonModes?: Record<string, string>;
    target: FieldTarget;
    visibleCommands?: string[];
  } = $props();
  type SelectionActionCommand = "aqe:delete-selection" | "aqe:delete-rest";

  function commandVisible(command: SelectionActionCommand): boolean {
    return !Array.isArray(visibleCommands) || visibleCommands.includes(command);
  }

  function commandIconOnly(command: SelectionActionCommand): boolean {
    return buttonDisplayMode(command, buttonModes) === EditorButtonMode.Icon;
  }

  const playTooltip = $derived(
    buttonTooltipContent(t("editor.command.play.label"), t("editor.command.play.title_selected")),
  );
  const deleteRegionTooltip = $derived(
    buttonTooltipContent(t("editor.command.delete_region.label"), t("editor.command.delete_region.title")),
  );
  const deleteRestTooltip = $derived(
    buttonTooltipContent(t("editor.command.delete_rest.label"), t("editor.command.delete_rest.title")),
  );
</script>

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
        data-aqe-tooltip-content={playTooltip}
        data-testid={`aqe-selection-toolbar-play-${target.ord}`}
        aria-label={playTooltip}
        onpointerdown={(event) => event.stopPropagation()}
        onmousedown={(event) => event.preventDefault()}
        onclick={() => send("aqe:play", target.node, target.ord)}
      >
        <EditorCommandIcon className="aqe-button-icon-default" icon="play" />
        <EditorCommandIcon className="aqe-button-icon-active" icon="pause" />
      </button>
    {/snippet}
  </AqeTooltip>
  {#if commandVisible("aqe:delete-selection")}
    <AqeTooltip>
      {#snippet trigger({ props })}
        <button
          {...props}
          type="button"
          class:aqe-icon-only={commandIconOnly("aqe:delete-selection")}
          class:aqe-selection-toolbar-command-text={!commandIconOnly("aqe:delete-selection")}
          class="aqe-button aqe-selection-toolbar-button aqe-delete-region-button aqe-tooltip-target"
          data-aqe-command="aqe:delete-selection"
          data-aqe-button-state="default"
          data-aqe-enabled-title={deleteRegionTooltip}
          data-aqe-tooltip-content={deleteRegionTooltip}
          data-testid={`aqe-selection-toolbar-delete-region-${target.ord}`}
          aria-label={deleteRegionTooltip}
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
          <span class="aqe-button-label">{t("editor.command.delete_region.label")}</span>
        </button>
      {/snippet}
    </AqeTooltip>
  {/if}
  {#if commandVisible("aqe:delete-rest")}
    <AqeTooltip>
      {#snippet trigger({ props })}
        <button
          {...props}
          type="button"
          class:aqe-icon-only={commandIconOnly("aqe:delete-rest")}
          class:aqe-selection-toolbar-command-text={!commandIconOnly("aqe:delete-rest")}
          class="aqe-button aqe-selection-toolbar-button aqe-delete-rest-button aqe-tooltip-target"
          data-aqe-command="aqe:delete-rest"
          data-aqe-button-state="default"
          data-aqe-enabled-title={deleteRestTooltip}
          data-aqe-tooltip-content={deleteRestTooltip}
          data-testid={`aqe-selection-toolbar-delete-rest-${target.ord}`}
          aria-label={deleteRestTooltip}
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
          <span class="aqe-button-label">{t("editor.command.delete_rest.label")}</span>
        </button>
      {/snippet}
    </AqeTooltip>
  {/if}
</div>
