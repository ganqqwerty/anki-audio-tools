<script lang="ts">
  import AqeTooltipProvider from "../../src/lib/AqeTooltipProvider.svelte";
  import { EditorButtonMode } from "../../src/lib/types.js";
  import ButtonSettingsCard from "../../src/settings/ButtonSettingsCard.svelte";
  import SettingsChoiceGroup from "../../src/settings/SettingsChoiceGroup.svelte";

  const {
    onSelect = () => {},
    variant,
  }: {
    onSelect?: (value: string | number) => void;
    variant: "button-card" | "choice-group";
  } = $props();
</script>

<AqeTooltipProvider>
  {#if variant === "button-card"}
    <ButtonSettingsCard
      icon="play"
      mode={EditorButtonMode.Icon}
      modeLocked={true}
      onSetMode={() => {}}
      onToggle={() => {}}
      testId="button-settings-test"
      title="Test"
      visible={true}
    />
  {:else}
    <SettingsChoiceGroup
      ariaLabel="Choice"
      disabled={true}
      disabledReason="Disabled because another option is active."
      {onSelect}
      options={[{ label: "Option A", tooltip: "Option A\nDoes the thing.", value: "a" }]}
      testId="choice"
      value="a"
    />
  {/if}
</AqeTooltipProvider>
