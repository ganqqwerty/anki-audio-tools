<script lang="ts">
  import CommandIcon from "$lib/CommandIcon.svelte";
  import {
    formatOutputFormat,
    OUTPUT_FORMAT_VALUES,
  } from "$lib/audio-operation-parameters.js";
  import { t } from "$lib/i18n.js";
  import { OutputFormat, type Config } from "$lib/types.js";
  import SettingsChoiceGroup from "./SettingsChoiceGroup.svelte";

  const { config = $bindable() }: { config: Config } = $props();
</script>

<label class="settings-field">
  <span class="settings-label-with-icon">
    <CommandIcon className="settings-label-icon" icon="file-audio" />
    <span class="settings-label-text">{t("settings.output_format")}</span>
  </span>
  <SettingsChoiceGroup
    ariaLabel={t("settings.output_format")}
    options={OUTPUT_FORMAT_VALUES.map((format) => ({
      label: formatOutputFormat(format),
      value: format,
    }))}
    testId="output-format"
    value={config.output_format}
    onSelect={(value) => (config.output_format = value as OutputFormat)}
  />
</label>
