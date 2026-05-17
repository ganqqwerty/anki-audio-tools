<script lang="ts">
  import ChartLine from "@lucide/svelte/icons/chart-line";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import CircleHelp from "@lucide/svelte/icons/circle-help";
  import FastForward from "@lucide/svelte/icons/fast-forward";
  import FolderOpen from "@lucide/svelte/icons/folder-open";
  import Pause from "@lucide/svelte/icons/pause";
  import Play from "@lucide/svelte/icons/play";
  import Redo2 from "@lucide/svelte/icons/redo-2";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Repeat2 from "@lucide/svelte/icons/repeat-2";
  import Rewind from "@lucide/svelte/icons/rewind";
  import Scissors from "@lucide/svelte/icons/scissors";
  import Settings from "@lucide/svelte/icons/settings";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import TimerReset from "@lucide/svelte/icons/timer-reset";
  import Undo2 from "@lucide/svelte/icons/undo-2";
  import Volume1 from "@lucide/svelte/icons/volume-1";
  import Volume2 from "@lucide/svelte/icons/volume-2";
  import VolumeX from "@lucide/svelte/icons/volume-x";

  import type { EditorIconName } from "./types.js";

  const { className = "", icon }: { className?: string; icon: EditorIconName } = $props();
  const classes = $derived(["aqe-button-icon", className].filter(Boolean).join(" "));
</script>

<span class={classes} aria-hidden="true">
  {#if icon === "chart-line"}
    <ChartLine size={14} strokeWidth={2} />
  {:else if icon === "chevron-down"}
    <ChevronDown size={14} strokeWidth={2} />
  {:else if icon === "circle-help"}
    <CircleHelp size={14} strokeWidth={2} />
  {:else if icon === "fast-forward"}
    <FastForward size={14} strokeWidth={2} />
  {:else if icon === "folder-open"}
    <FolderOpen size={14} strokeWidth={2} />
  {:else if icon === "pause"}
    <Pause size={14} strokeWidth={2} />
  {:else if icon === "play"}
    <Play size={14} strokeWidth={2} />
  {:else if icon === "redo-2"}
    <Redo2 size={14} strokeWidth={2} />
  {:else if icon === "refresh-cw"}
    <RefreshCw size={14} strokeWidth={2} />
  {:else if icon === "repeat-2"}
    <Repeat2 size={14} strokeWidth={2} />
  {:else if icon === "rewind"}
    <Rewind size={14} strokeWidth={2} />
  {:else if icon === "scissors"}
    <Scissors size={14} strokeWidth={2} />
  {:else if icon === "settings"}
    <Settings size={14} strokeWidth={2} />
  {:else if icon === "sparkles"}
    <Sparkles size={14} strokeWidth={2} />
  {:else if icon === "timer-reset"}
    <TimerReset size={14} strokeWidth={2} />
  {:else if icon === "undo-2"}
    <Undo2 size={14} strokeWidth={2} />
  {:else if icon === "volume-1"}
    <Volume1 size={14} strokeWidth={2} />
  {:else if icon === "volume-2"}
    <Volume2 size={14} strokeWidth={2} />
  {:else if icon === "volume-x"}
    <VolumeX size={14} strokeWidth={2} />
  {/if}
</span>
