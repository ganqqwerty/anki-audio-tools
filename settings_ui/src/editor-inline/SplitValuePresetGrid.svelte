<script lang="ts">
  import AqeTooltip from "../lib/AqeTooltip.svelte";
  import { splitOptionTooltip } from "./split-menu-content.js";
  import type { ButtonSpec } from "./types.js";

  const {
    command,
    dpdfnetAttnLimitDb,
    onSelect,
    optionLabel,
    options,
    selectedLabel,
    slug,
    targetOrd,
  }: {
    command: ButtonSpec["command"];
    dpdfnetAttnLimitDb: number;
    onSelect: (value: string) => void;
    optionLabel: (value: string) => string;
    options: string[];
    selectedLabel: string;
    slug: string;
    targetOrd: number;
  } = $props();
</script>

<div class="aqe-split-presets">
  {#each options as option}
    <AqeTooltip>
      {#snippet trigger({ props })}
        <button
          {...props}
          type="button"
          class="aqe-button aqe-split-preset aqe-tooltip-target"
          data-aqe-tooltip-content={splitOptionTooltip(option, dpdfnetAttnLimitDb, command)}
          data-testid={`aqe-split-${targetOrd}-${slug}-preset-${option}`}
          aria-pressed={selectedLabel === optionLabel(option) ? "true" : "false"}
          onclick={() => onSelect(option)}
        >
          <span class="aqe-split-preset-label">{optionLabel(option)}</span>
        </button>
      {/snippet}
    </AqeTooltip>
  {/each}
</div>
