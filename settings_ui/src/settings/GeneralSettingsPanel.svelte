<script lang="ts">
  import { t } from "$lib/i18n.js";
  import ToolbarVisibilitySettings from "./ToolbarVisibilitySettings.svelte";
  import type { Config } from "$lib/types.js";

  let { config = $bindable(), saveError }: {
    config: Config;
    saveError: string;
  } = $props();
</script>

<div class="settings-card settings-stack">
  <h2>{t("settings.tab.general")}</h2>

  <ToolbarVisibilitySettings bind:config />

  {#if saveError}
    <p class="settings-error" data-testid="save-error">{saveError}</p>
  {/if}
</div>
