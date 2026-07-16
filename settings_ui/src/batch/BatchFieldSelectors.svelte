<script lang="ts">
  import FieldTooltipTarget from "$lib/FieldTooltipTarget.svelte";
  import { t } from "$lib/i18n.js";
  import { BatchParameterKind } from "$lib/types.js";
  import type {
    BatchInitialState,
    BatchOperationOption,
    BatchProcessingPresetOption,
  } from "$lib/types.js";
  import type { BatchFormState } from "./batch-state.js";

  interface Props {
    state: BatchInitialState;
    form: BatchFormState;
    selected: BatchOperationOption | undefined;
    preset: BatchProcessingPresetOption | undefined;
    disabled: boolean;
  }

  let { state, form = $bindable(), selected, preset, disabled }: Props = $props();
  const disabledReason = $derived(disabled ? t("tooltip.disabled.batch_running") : undefined);
</script>

<label>
  <span>{t("batch.operation")}</span>
  <span class="batch-field-help">{t("batch.operation.help")}</span>
  <FieldTooltipTarget block content={t("batch.operation.help")} {disabledReason}>
    <select aria-label={t("batch.operation")} bind:value={form.operation} data-testid="batch-operation" disabled={disabled}>
      {#each state.operations as operation}
        <option value={operation.operation}>{operation.label}</option>
      {/each}
    </select>
  </FieldTooltipTarget>
</label>

{#if selected?.parameter_kind === BatchParameterKind.Preset}
  <label>
    <span>{t("batch.preset")}</span>
    <select bind:value={form.presetId} data-testid="batch-preset" disabled={disabled}>
      {#each state.processing_presets as item}
        <option value={item.id}>{item.name}</option>
      {/each}
    </select>
  </label>
{/if}

<label>
  <span>{t("batch.source_field")}</span>
  <span class="batch-field-help">{t("batch.source_field.help")}</span>
  <FieldTooltipTarget block content={t("batch.source_field.help")} {disabledReason}>
    <select
      aria-label={t("batch.source_field")}
      bind:value={form.sourceField}
      data-testid="batch-source-field"
      disabled={disabled}
    >
      {#each state.field_groups as group}
        {#each group.fields as field}
          <option value={field}>{group.notetype_name} / {field}</option>
        {/each}
      {/each}
    </select>
  </FieldTooltipTarget>
</label>

{#if selected?.requires_target_field}
  <label>
    <span>{t("batch.target_field")}</span>
    <span class="batch-field-help">{t("batch.target_field.help")}</span>
    <FieldTooltipTarget block content={t("batch.target_field.help")} {disabledReason}>
      <select
        aria-label={t("batch.target_field")}
        bind:value={form.targetField}
        data-testid="batch-target-field"
        disabled={disabled}
      >
        {#each state.field_groups as group}
          {#each group.fields as field}
            <option value={field}>{group.notetype_name} / {field}</option>
          {/each}
        {/each}
      </select>
    </FieldTooltipTarget>
  </label>
{/if}

{#if selected?.parameter_kind === BatchParameterKind.Preset && preset?.has_transforms}
  <label>
    <span>{t("batch.audio_target_field")}</span>
    <select bind:value={form.audioTargetField} data-testid="batch-audio-target-field" disabled={disabled}>
      {#each state.field_groups as group}
        {#each group.fields as field}
          <option value={field}>{group.notetype_name} / {field}</option>
        {/each}
      {/each}
    </select>
  </label>
{/if}

{#if selected?.parameter_kind === BatchParameterKind.Preset && preset?.graph_enabled}
  <label>
    <span>{t("batch.graph_target_field")}</span>
    <select bind:value={form.graphTargetField} data-testid="batch-graph-target-field" disabled={disabled}>
      {#each state.field_groups as group}
        {#each group.fields as field}
          <option value={field}>{group.notetype_name} / {field}</option>
        {/each}
      {/each}
    </select>
  </label>
{/if}

<style>
  label {
    display: grid;
    gap: 6px;
  }

  span {
    color: var(--fg-subtle, currentColor);
    font-size: 11px;
    font-weight: 700;
  }

  .batch-field-help {
    font-weight: 500;
    line-height: 1.35;
  }

  select {
    background: var(--canvas-elevated, Field);
    border: 1px solid var(--border, ButtonBorder);
    border-radius: 6px;
    box-sizing: border-box;
    color: var(--fg, FieldText);
    font: inherit;
    font-size: 11px;
    min-height: 30px;
    padding: 4px 8px;
    width: 100%;
  }

  select:disabled {
    opacity: 0.7;
  }
</style>
