<script lang="ts">
  import AudioLines from "@lucide/svelte/icons/audio-lines";
  import ChartLine from "@lucide/svelte/icons/chart-line";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import CircleHelp from "@lucide/svelte/icons/circle-help";
  import FastForward from "@lucide/svelte/icons/fast-forward";
  import FileAudio from "@lucide/svelte/icons/file-audio";
  import FolderOpen from "@lucide/svelte/icons/folder-open";
  import Mic from "@lucide/svelte/icons/mic";
  import Pause from "@lucide/svelte/icons/pause";
  import Play from "@lucide/svelte/icons/play";
  import Redo2 from "@lucide/svelte/icons/redo-2";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Repeat2 from "@lucide/svelte/icons/repeat-2";
  import Rewind from "@lucide/svelte/icons/rewind";
  import Scissors from "@lucide/svelte/icons/scissors";
  import Settings from "@lucide/svelte/icons/settings";
  import Snail from "@lucide/svelte/icons/snail";
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
  {:else if icon === "file-audio"}
    <FileAudio {size} {strokeWidth} />
  {:else if icon === "folder-open"}
    <FolderOpen {size} {strokeWidth} />
  {:else if icon === "mic"}
    <Mic {size} {strokeWidth} />
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
  {:else if icon === "hare-running"}
    <!-- Framework7 hare, MIT. Modified with outline motion lines. -->
    <svg xmlns="http://www.w3.org/2000/svg" width={Math.round(size * 1.35)} height={size} viewBox="0 0 76 56" fill="none" stroke="currentColor" aria-hidden="true">
      <g color="currentColor">
        <path fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" d="M1.5 25.75H16.5M4 32.45H17.5M8 39.15H17.5"/>
        <path transform="translate(20 0)" fill="currentColor" stroke="none" d="M16.478 51.234c3.382 0 6.457-.76 9.008-3.057c.977.706 2.062 1.103 3.69 1.103c1.537 0 2.731-.506 4.866-.506c1.97 0 2.948.506 4.521.506c3.726 0 5.029-1.917 5.029-4.033c0-3.419-2.605-5.463-7.814-5.915a53 53 0 0 1 4.775-2.044c2.17 1.447 5.3 2.315 7.615 2.297C53.033 39.55 56 38.03 56 33.02c0-6.15-4.667-10.78-10.165-10.834l-3.944-5.336c-3.002-4.034-6.222-6.295-10.346-6.295c-3.201 0-7.56 1.773-7.56 4.287c0 2.098 2.387 3.6 4.702 5.065c2.714 1.7 6.385 3.816 9.786 5.788c-.47.416-.796.597-1.266.597c-.543 0-1.285-.271-2.243-.832c-7.326-4.124-11.685-7.47-17.328-7.47c-6.71 0-11.558 3.454-13.856 10.074C1.538 28.533 0 30 0 32.26c0 2.803 2.261 4.25 4.594 4.377c1.737 2.804 6.53 5.282 12.698 4.775l1.718 1.43c-.452.234-.886.307-1.41.307c-1.194-.018-2.334-.398-3.709-.398c-2.514 0-4.286 1.465-4.286 3.654c0 3.093 2.749 4.829 6.873 4.829m17.473-5.047c-2.261 0-3.69.362-4.703.362c-.814 0-1.736-.126-2.64-.868l-8.086-6.82c-5.788.254-10.039-1.265-12.48-4.81c-1.846.216-3.184-.489-3.184-2.008c0-1.375 1.194-2.334 3.202-2.225c1.844-6.114 5.914-8.954 11.54-8.954c5.914 0 11.992 4.758 16.405 7.254a6.94 6.94 0 0 0 3.419.958c1.99 0 3.545-1.248 4.956-3.78L30.351 17.88c-1.266-.814-3.093-2.17-3.093-2.659c0-1.067 2.497-1.863 4.323-1.863c2.858 0 5.3 1.682 7.434 4.377l5.554 6.639c5.118-.236 8.97 3.671 8.97 8.664c0 3.201-1.482 4.178-5.28 4.178c-2.37 0-4.993-.959-7.254-2.388c-3.31.832-6.783 2.406-9.586 4.486c-.38.036-.688.072-.977.109l-1.302-3.184c-2.732-6.566-7.109-8.809-11.54-8.809c-.724 0-1.556.018-2.298.181c-.904.2-1.23.67-1.23 1.266c0 .688.507 1.14 1.23 1.122c.778-.036 1.285-.127 2.17-.127c4.107 0 7.127 2.189 9.624 8.158l1.754 4.033c1.375-.289 2.677-.506 4.721-.506c3.69 0 7.344.977 7.344 3.473c0 .959-.832 1.61-2.352 1.61c-1.754 0-3.02-.453-4.612-.453m13.041-14.361c.796.018 1.447-.688 1.484-1.466a1.405 1.405 0 0 0-1.393-1.447c-.778-.018-1.447.652-1.465 1.411c-.037.796.596 1.484 1.374 1.502M12.21 46.423c0-.724.489-1.285 1.538-1.285c1.03 0 2.152.29 3.4.29c1.664 0 2.84-.145 3.925-.887l2.37 1.954c-1.664 1.501-4.124 2.279-7.054 2.279c-2.533 0-4.179-.904-4.179-2.351"/>
      </g>
    </svg>
  {:else if icon === "snail"}
    <Snail {size} {strokeWidth} />
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
