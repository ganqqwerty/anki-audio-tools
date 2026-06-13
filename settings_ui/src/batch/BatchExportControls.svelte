<script lang="ts">
  import { t } from "$lib/i18n.js";
  import UnitNumberInput from "$lib/UnitNumberInput.svelte";
  import { AudioExportMode } from "$lib/types.js";
  import type { AudioExportInitialState } from "$lib/types.js";
  import type { AudioExportFormState } from "./export-state.js";
  import { setAudioExportFieldSelected } from "./export-state.js";

  interface Props {
    state: AudioExportInitialState;
    form: AudioExportFormState;
    disabled: boolean;
    onChooseDestination: () => void;
  }

  let { state, form = $bindable(), disabled, onChooseDestination }: Props = $props();

  const modeOptions = [
    { value: AudioExportMode.Zip, label: t("audio_export.mode.zip") },
    { value: AudioExportMode.CombinedMp3, label: t("audio_export.mode.combined_mp3") },
  ];
</script>

<div class="export-grid" data-testid="audio-export-controls">
  <label class="export-control">
    <span>{t("batch.operation")}</span>
    <div class="export-choice-group" role="radiogroup" aria-label={t("batch.operation")}>
      {#each modeOptions as option}
        <label class="export-choice">
          <input
            type="radio"
            bind:group={form.mode}
            value={option.value}
            disabled={disabled}
          />
          <span>{option.label}</span>
        </label>
      {/each}
    </div>
  </label>

  <label class="export-control export-destination">
    <span>{t("audio_export.destination")}</span>
    <div class="destination-row">
      <input
        readonly
        data-testid="audio-export-destination"
        value={form.destinationPath}
        aria-label={t("audio_export.destination")}
      />
      <button type="button" disabled={disabled} onclick={onChooseDestination}>
        {t("audio_export.choose_destination")}
      </button>
    </div>
  </label>

  {#if form.mode === AudioExportMode.CombinedMp3}
    <label class="export-control">
      <span>{t("audio_export.silence_between_clips")}</span>
      <UnitNumberInput
        block
        bind:value={form.silenceBetweenClipsSeconds}
        disabled={disabled}
        max="10"
        min="0"
        step="0.25"
        testId="audio-export-silence"
        unit="s"
      />
    </label>
  {/if}

  <fieldset class="export-fields">
    <legend>{t("audio_export.fields")}</legend>
    <div class="field-groups">
      {#each state.field_groups as group}
        <div class="field-group">
          <span class="field-group-name">{group.notetype_name}</span>
          <div class="field-options">
            {#each group.fields as field}
              <label class="field-option">
                <input
                  type="checkbox"
                  checked={form.selectedFields[group.notetype_name]?.has(field) ?? false}
                  disabled={disabled}
                  onchange={(event) =>
                    setAudioExportFieldSelected(
                      form,
                      group.notetype_name,
                      field,
                      event.currentTarget.checked,
                    )}
                />
                <span>{field}</span>
              </label>
            {/each}
          </div>
        </div>
      {/each}
    </div>
  </fieldset>
</div>

<style>
  .export-grid {
    display: grid;
    gap: 14px;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  }

  .export-control {
    display: grid;
    gap: 6px;
  }

  span,
  legend {
    color: var(--fg-subtle, currentColor);
    font-size: 11px;
    font-weight: 700;
  }

  .export-choice-group,
  .field-options {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .export-choice,
  .field-option {
    align-items: center;
    display: inline-flex;
    gap: 5px;
    min-height: 24px;
  }

  .export-choice span,
  .field-option span {
    color: inherit;
    font-weight: 400;
  }

  .destination-row {
    display: grid;
    gap: 6px;
    grid-template-columns: minmax(0, 1fr) auto;
  }

  input[readonly] {
    background: var(--canvas-elevated, Field);
    border: 1px solid var(--border, ButtonBorder);
    border-radius: 6px;
    box-sizing: border-box;
    color: var(--fg, FieldText);
    font: inherit;
    font-size: 11px;
    min-height: 30px;
    min-width: 0;
    padding: 4px 8px;
    width: 100%;
  }

  button {
    appearance: none;
    background: transparent;
    border: 1px solid ButtonBorder;
    border-radius: 7px;
    color: inherit;
    cursor: pointer;
    font: inherit;
    font-size: 11px;
    min-height: 30px;
    padding: 4px 8px;
  }

  button:disabled,
  input:disabled {
    cursor: default;
    opacity: 0.7;
  }

  .export-fields {
    border: 0;
    display: grid;
    gap: 8px;
    grid-column: 1 / -1;
    margin: 0;
    padding: 0;
  }

  .field-groups {
    display: grid;
    gap: 8px;
  }

  .field-group {
    align-items: baseline;
    display: grid;
    gap: 8px;
    grid-template-columns: minmax(92px, auto) 1fr;
  }

  .field-group-name {
    overflow-wrap: anywhere;
  }
</style>
