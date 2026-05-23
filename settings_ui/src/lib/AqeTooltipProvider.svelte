<script lang="ts">
  import { Tooltip } from "bits-ui";
  import type { Snippet } from "svelte";

  const { children }: { children?: Snippet } = $props();
</script>

<Tooltip.Provider delayDuration={0} disableHoverableContent={true} skipDelayDuration={0}>
  {@render children?.()}
</Tooltip.Provider>
