<script lang="ts">
  import CommandIcon from "$lib/CommandIcon.svelte";
  import {
    formatOutputFormat,
    OUTPUT_FORMAT_VALUES,
  } from "$lib/audio-operation-parameters.js";
  import { t } from "$lib/i18n.js";
  import type { Config } from "$lib/types.js";

  const { config = $bindable() }: { config: Config } = $props();
</script>

<label>
  <span class="label-with-icon">
    <CommandIcon className="settings-label-icon" icon="file-audio" />
    <span>{t("settings.output_format")}</span>
  </span>
  <select data-testid="output-format" bind:value={config.output_format}>
    {#each OUTPUT_FORMAT_VALUES as format}
      <option value={format}>{formatOutputFormat(format)}</option>
    {/each}
  </select>
</label>
