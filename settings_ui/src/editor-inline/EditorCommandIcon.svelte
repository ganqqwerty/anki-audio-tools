<script lang="ts">
  import CommandIcon from "$lib/CommandIcon.svelte";

  import type { EditorIconName } from "./types.js";

  const { className = "", icon }: { className?: string; icon: EditorIconName } = $props();
  const classes = $derived(["aqe-button-icon", className].filter(Boolean).join(" "));
</script>

<CommandIcon className={classes} {icon} />
