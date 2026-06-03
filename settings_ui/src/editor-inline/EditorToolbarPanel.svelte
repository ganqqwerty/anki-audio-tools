<script lang="ts">
  import type { Snippet } from "svelte";

  const {
    children,
    label,
    panelClass = "",
    testId,
  }: {
    children: Snippet;
    label: string;
    panelClass?: string;
    testId: string;
  } = $props();

  const classes = $derived(["aqe-toolbar-panel", panelClass].filter(Boolean).join(" "));
</script>

<span
  class={classes}
  data-aqe-toolbar-button-container="true"
  data-testid={testId}
  role="group"
  aria-label={label}
>
  <span class="aqe-toolbar-panel-label" aria-hidden="true">{label}</span>
  {@render children()}
</span>
