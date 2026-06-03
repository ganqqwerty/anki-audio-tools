<script lang="ts">
  import type { Snippet } from "svelte";

  import AqeTooltip from "$lib/AqeTooltip.svelte";
  import { tooltipWithDisabledClarification } from "$lib/disabled-tooltip.js";

  const {
    block = false,
    children,
    content,
    disabledReason,
  }: {
    block?: boolean;
    children: Snippet;
    content?: string | null | undefined;
    disabledReason?: string | null | undefined;
  } = $props();

  const tooltipContent = $derived(tooltipWithDisabledClarification(content, disabledReason));
</script>

<AqeTooltip disabled={tooltipContent.length === 0}>
  {#snippet trigger({ props })}
    <span
      {...props}
      class="field-tooltip-target aqe-tooltip-target"
      class:field-tooltip-target-block={block}
      data-aqe-tooltip-content={tooltipContent || undefined}
    >
      {@render children()}
    </span>
  {/snippet}
</AqeTooltip>

<style>
  .field-tooltip-target {
    display: inline-flex;
    font: inherit;
    min-width: 0;
  }

  .field-tooltip-target-block {
    display: block;
    width: 100%;
  }
</style>
