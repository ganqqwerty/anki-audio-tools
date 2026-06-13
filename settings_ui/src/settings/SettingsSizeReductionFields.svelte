<script lang="ts">
  import { choiceTooltip, sizeReductionModeTooltip } from "$lib/audio-option-tooltips.js";
  import { t } from "$lib/i18n.js";
  import SizeReductionAdvancedParamsFields from "$lib/SizeReductionAdvancedParamsFields.svelte";
  import {
    formatSizeReductionMode,
    SIZE_REDUCTION_MODE_VALUES,
    sizeReductionPreset,
  } from "$lib/size-reduction-parameters.js";
  import type { Config } from "$lib/types.js";
  import SettingsChoiceGroup from "./SettingsChoiceGroup.svelte";

  let { config = $bindable() }: { config: Config } = $props();

  function applySizeReductionPreset(value: Config["size_reduction_mode"]): void {
    const preset = sizeReductionPreset(value);
    config.size_reduction_mode = value;
    config.size_reduction_bitrate_kbps = preset.bitrateKbps;
    config.size_reduction_sample_rate_hz = preset.sampleRateHz;
    config.size_reduction_channels = preset.channels;
  }
</script>

<label class="settings-field">
  <span>{t("settings.size_reduction_mode")}</span>
  <SettingsChoiceGroup
    ariaLabel={t("settings.size_reduction_mode")}
    options={SIZE_REDUCTION_MODE_VALUES.map((value) => ({
      label: formatSizeReductionMode(value),
      tooltip: choiceTooltip(formatSizeReductionMode(value), sizeReductionModeTooltip(value)),
      value,
    }))}
    testId="size-reduction-mode"
    value={config.size_reduction_mode}
    onSelect={(value) => applySizeReductionPreset(value as Config["size_reduction_mode"])}
  />
</label>
<SizeReductionAdvancedParamsFields
  bind:bitrateKbps={config.size_reduction_bitrate_kbps}
  bind:sampleRateHz={config.size_reduction_sample_rate_hz}
  bind:channels={config.size_reduction_channels}
  testPrefix="settings-size-reduction"
/>
