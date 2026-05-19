<script lang="ts">
  import AudioLines from "@lucide/svelte/icons/audio-lines";
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
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Undo2 from "@lucide/svelte/icons/undo-2";
  import Volume1 from "@lucide/svelte/icons/volume-1";
  import Volume2 from "@lucide/svelte/icons/volume-2";
  import VolumeX from "@lucide/svelte/icons/volume-x";
  import Waves from "@lucide/svelte/icons/waves";

  import type { CommandIconName } from "./icon-types.js";

  const {
    className = "",
    icon,
    size = 14,
    strokeWidth = 2,
  }: {
    className?: string;
    icon: CommandIconName;
    size?: number;
    strokeWidth?: number;
  } = $props();
</script>

<span class={className} aria-hidden="true">
  {#if icon === "audio-lines"}
    <AudioLines {size} {strokeWidth} />
  {:else if icon === "chart-line"}
    <ChartLine {size} {strokeWidth} />
  {:else if icon === "chevron-down"}
    <ChevronDown {size} {strokeWidth} />
  {:else if icon === "circle-help"}
    <CircleHelp {size} {strokeWidth} />
  {:else if icon === "fast-forward"}
    <FastForward {size} {strokeWidth} />
  {:else if icon === "folder-open"}
    <FolderOpen {size} {strokeWidth} />
  {:else if icon === "pause"}
    <Pause {size} {strokeWidth} />
  {:else if icon === "play"}
    <Play {size} {strokeWidth} />
  {:else if icon === "redo-2"}
    <Redo2 {size} {strokeWidth} />
  {:else if icon === "refresh-cw"}
    <RefreshCw {size} {strokeWidth} />
  {:else if icon === "repeat-2"}
    <Repeat2 {size} {strokeWidth} />
  {:else if icon === "rewind"}
    <Rewind {size} {strokeWidth} />
  {:else if icon === "scissors"}
    <Scissors {size} {strokeWidth} />
  {:else if icon === "settings"}
    <Settings {size} {strokeWidth} />
  {:else if icon === "sparkles"}
    <Sparkles {size} {strokeWidth} />
  {:else if icon === "timer-reset"}
    <TimerReset {size} {strokeWidth} />
  {:else if icon === "trash-2"}
    <Trash2 {size} {strokeWidth} />
  {:else if icon === "undo-2"}
    <Undo2 {size} {strokeWidth} />
  {:else if icon === "volume-1"}
    <Volume1 {size} {strokeWidth} />
  {:else if icon === "volume-2"}
    <Volume2 {size} {strokeWidth} />
  {:else if icon === "volume-x"}
    <VolumeX {size} {strokeWidth} />
  {:else if icon === "waves"}
    <Waves {size} {strokeWidth} />
  {/if}
</span>
