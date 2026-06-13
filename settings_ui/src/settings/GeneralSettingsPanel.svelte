<script lang="ts">
  import { t } from "$lib/i18n.js";
  import ToolbarVisibilitySettings from "./ToolbarVisibilitySettings.svelte";
  import type { Config } from "$lib/types.js";

  let { config = $bindable() }: {
    config: Config;
  } = $props();
</script>

<div class="settings-card settings-stack">
  <h2>{t("settings.tab.general")}</h2>

  <ToolbarVisibilitySettings bind:config />
</div>
