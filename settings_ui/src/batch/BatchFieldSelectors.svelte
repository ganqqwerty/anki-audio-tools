<script lang="ts">
  import { t } from "$lib/i18n.js";
  import type { BatchInitialState, BatchOperationOption } from "$lib/types.js";
  import type { BatchFormState } from "./batch-state.js";

  interface Props {
    state: BatchInitialState;
    form: BatchFormState;
    selected: BatchOperationOption | undefined;
    disabled: boolean;
  }

  let { state, form = $bindable(), selected, disabled }: Props = $props();
</script>

<label>
  <span>{t("batch.operation")}</span>
  <select bind:value={form.operation} data-testid="batch-operation" disabled={disabled}>
    {#each state.operations as operation}
      <option value={operation.operation}>{operation.label}</option>
    {/each}
  </select>
</label>

<label>
  <span>{t("batch.source_field")}</span>
  <select bind:value={form.sourceField} disabled={disabled}>
    {#each state.field_groups as group}
      {#each group.fields as field}
        <option value={field}>{group.notetype_name} / {field}</option>
      {/each}
    {/each}
  </select>
</label>

{#if selected?.requires_target_field}
  <label>
    <span>{t("batch.target_field")}</span>
    <select bind:value={form.targetField} disabled={disabled}>
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
