<script lang="ts">
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
  <button
    type="button"
    class="aqe-button aqe-selection-toolbar-button aqe-selection-toolbar-play"
    data-testid={`aqe-selection-toolbar-play-${target.ord}`}
    data-aqe-button-state="play"
    title="Play selection"
    aria-label="Play selection"
    onpointerdown={(event) => event.stopPropagation()}
    onmousedown={(event) => event.preventDefault()}
    onclick={() => send("aqe:play", target.node, target.ord)}
  >
    <EditorCommandIcon className="aqe-button-icon-default" icon="play" />
    <EditorCommandIcon className="aqe-button-icon-active" icon="pause" />
  </button>
  <button
    type="button"
    class="aqe-button aqe-selection-toolbar-button aqe-delete-region-button"
    data-aqe-command="aqe:delete-selection"
    data-aqe-button-state="default"
    data-testid={`aqe-selection-toolbar-delete-region-${target.ord}`}
    title={t("editor.command.delete_region.title")}
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
    <EditorCommandIcon icon="trash-2" />
  </button>
  <button
    type="button"
    class="aqe-button aqe-selection-toolbar-button aqe-delete-rest-button"
    data-aqe-command="aqe:delete-rest"
    data-aqe-button-state="default"
    data-testid={`aqe-selection-toolbar-delete-rest-${target.ord}`}
    title="Delete audio outside selected region"
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
    <EditorCommandIcon icon="trash-2" />
  </button>
  <button
    type="button"
    class="aqe-button aqe-selection-toolbar-button aqe-selection-toolbar-collapse"
    data-testid={`aqe-selection-toolbar-collapse-${target.ord}`}
    title="Collapse selection actions"
    aria-label="Collapse selection actions"
    onpointerdown={(event) => event.stopPropagation()}
    onmousedown={(event) => event.preventDefault()}
    onclick={() => collapseSelectionToolbarForOrd(target.ord)}
  >
    <EditorCommandIcon icon="x" />
  </button>
</div>
<button
  type="button"
  class="aqe-selection-toolbar-dot"
  data-testid={`aqe-selection-toolbar-dot-${target.ord}`}
  title="Expand selection actions"
  aria-label="Expand selection actions"
  onpointerdown={(event) => event.stopPropagation()}
  onmousedown={(event) => event.preventDefault()}
  onclick={() => expandSelectionToolbarForOrd(target.ord)}
  hidden
></button>
