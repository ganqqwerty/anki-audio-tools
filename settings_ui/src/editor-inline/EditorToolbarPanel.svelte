<script lang="ts">
  import AqeTooltip from "../lib/AqeTooltip.svelte";
  import type { Snippet } from "svelte";

  const {
    children,
    description = "",
    label,
    panelClass = "",
    testId,
  }: {
    children: Snippet;
    description?: string;
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
  <AqeTooltip content={description}>
    {#snippet trigger({ props })}
      <span
        {...props}
        class="aqe-toolbar-panel-label aqe-tooltip-target"
        data-aqe-tooltip-content={description || undefined}
        aria-hidden="true"
      >{label}</span>
    {/snippet}
  </AqeTooltip>
  {@render children()}
</span>
