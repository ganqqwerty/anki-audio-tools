<script lang="ts">
  import AqeTooltip from "../lib/AqeTooltip.svelte";
  import { t } from "../lib/i18n.js";
  import EditorCommandIcon from "./EditorCommandIcon.svelte";

  const {
    onSave,
    saved = false,
    testId,
  }: {
    onSave: () => void;
    saved?: boolean;
    testId: string;
  } = $props();

  const label = $derived(t("editor.split.save_defaults"));

  function save(event: MouseEvent): void {
    event.preventDefault();
    event.stopPropagation();
    onSave();
  }
</script>

<AqeTooltip>
  {#snippet trigger({ props })}
    <button
      {...props}
      type="button"
      class="aqe-button aqe-icon-only aqe-split-default-save aqe-tooltip-target"
      class:aqe-split-default-save-saved={saved}
      data-aqe-tooltip-content={label}
      data-testid={testId}
      aria-label={label}
      onmousedown={(event) => event.preventDefault()}
      onclick={save}
    >
      <EditorCommandIcon icon="save" />
      <span class="aqe-button-label">{label}</span>
    </button>
  {/snippet}
</AqeTooltip>
