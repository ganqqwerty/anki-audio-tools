<script lang="ts">
  import { t } from "$lib/i18n.js";
  import UnitNumberInput from "$lib/UnitNumberInput.svelte";
  import type { Config } from "$lib/types.js";

  let { config = $bindable() }: { config: Config } = $props();
</script>

<label class="settings-field">
  <span>{t("settings.editor_history_size")}</span>
  <UnitNumberInput
    inputClass="settings-input"
    testId="editor-history-size"
    min="1"
    max="100"
    step="1"
    bind:value={config.editor_history_size}
  />
</label>
