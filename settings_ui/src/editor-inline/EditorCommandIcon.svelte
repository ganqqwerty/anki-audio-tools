<script lang="ts">
  import CommandIcon from "$lib/CommandIcon.svelte";

  import type { CommandIconName } from "../lib/icon-types.js";

  const { className = "", icon }: { className?: string; icon: CommandIconName } = $props();
  const classes = $derived(["aqe-button-icon", className].filter(Boolean).join(" "));
</script>

<CommandIcon className={classes} {icon} />
