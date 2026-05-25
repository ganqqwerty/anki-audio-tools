<script lang="ts">
  import AqeTooltip from "../lib/AqeTooltip.svelte";
  import { COMMAND_SLUGS } from "./commands.js";
  import type { ButtonSpec } from "./types.js";

  const {
    commands,
    labelFor,
    onRun,
    slug,
    targetOrd,
    titleFor,
  }: {
    commands: readonly ButtonSpec["command"][];
    labelFor: (command: ButtonSpec["command"]) => string;
    onRun: (command: ButtonSpec["command"]) => void;
    slug: string;
    targetOrd: number;
    titleFor: (command: ButtonSpec["command"]) => string;
  } = $props();

  function testId(command: ButtonSpec["command"]): string {
    const suffix = commands.length === 1 ? "" : `-${COMMAND_SLUGS[command]}`;
    return `aqe-split-${targetOrd}-${slug}-run${suffix}`;
  }
</script>

{#each commands as command}
  <AqeTooltip>
    {#snippet trigger({ props })}
      <button
        {...props}
        type="button"
        class="aqe-button aqe-split-run-button aqe-tooltip-target"
        data-aqe-tooltip-content={titleFor(command)}
        data-testid={testId(command)}
        aria-label={titleFor(command)}
        onclick={() => onRun(command)}
      >
        {labelFor(command)}
      </button>
    {/snippet}
  </AqeTooltip>
{/each}
