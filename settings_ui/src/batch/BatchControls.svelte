<script lang="ts">
  import { t } from "$lib/i18n.js";
  import { BatchParameterKind, BatchPauseAggressiveness } from "$lib/types.js";
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

<div class="batch-grid">
  <label>
    <span>{t("batch.operation")}</span>
    <select bind:value={form.operation} disabled={disabled}>
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

  {#if selected?.parameter_kind === BatchParameterKind.Speed}
    <label>
      <span>{t("settings.speed_step")}</span>
      <input bind:value={form.speedStep} disabled={disabled} max="0.25" min="0.01" step="0.01" type="number" />
    </label>
  {:else if selected?.parameter_kind === BatchParameterKind.Volume}
    <label>
      <span>{t("settings.volume_step_db")}</span>
      <input bind:value={form.volumeStepDb} disabled={disabled} max="12" min="0.5" step="0.5" type="number" />
    </label>
  {:else if selected?.parameter_kind === BatchParameterKind.Pause}
    <label>
      <span>{t("settings.pause_aggressiveness")}</span>
      <select bind:value={form.pauseAggressiveness} disabled={disabled}>
        <option value={BatchPauseAggressiveness.Gentle}>{t("settings.pause_aggressiveness.gentle")}</option>
        <option value={BatchPauseAggressiveness.Normal}>{t("settings.pause_aggressiveness.normal")}</option>
        <option value={BatchPauseAggressiveness.Aggressive}>{t("settings.pause_aggressiveness.aggressive")}</option>
      </select>
    </label>
  {/if}
</div>

<style>
  .batch-grid {
    display: grid;
    gap: 14px;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  }

  label {
    display: grid;
    gap: 6px;
  }

  span {
    color: var(--fg-subtle, currentColor);
    font-size: 0.85rem;
    font-weight: 600;
  }

  select,
  input {
    background: var(--canvas-elevated, Field);
    border: 1px solid var(--border, ButtonBorder);
    border-radius: 6px;
    box-sizing: border-box;
    color: var(--fg, FieldText);
    font: inherit;
    min-height: 34px;
    padding: 6px 8px;
    width: 100%;
  }

  select:disabled,
  input:disabled {
    opacity: 0.7;
  }
</style>
