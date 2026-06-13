<script lang="ts">
  import { t } from "$lib/i18n.js";
  import {
    Operation,
    type AudioProcessingPreset,
    type AudioProcessingPresetGraph,
    type AudioProcessingPresetStep,
    type Config,
  } from "$lib/types.js";
  import PresetGraphEditor from "./PresetGraphEditor.svelte";
  import PresetStepEditor from "./PresetStepEditor.svelte";
  import {
    TRANSFORM_OPERATIONS,
    graphParametersFromConfig,
    newStep,
    operationLabel,
    validatePresets,
  } from "./preset-settings-helpers.js";

  const { config = $bindable() }: { config: Config } = $props();

  let selectedPresetId = $state(config.audio_processing_presets[0]?.id ?? "");
  let addStepOperation = $state<Operation>(Operation.Denoise);
  const selectedPreset = $derived(
    config.audio_processing_presets.find((preset) => preset.id === selectedPresetId),
  );
  const validationMessages = $derived(validatePresets(config.audio_processing_presets));

  $effect(() => {
    if (config.audio_processing_presets.some((preset) => preset.id === selectedPresetId)) return;
    selectedPresetId = config.audio_processing_presets[0]?.id ?? "";
  });

  function newId(prefix: string): string {
    return `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
  }

  function uniqueName(base: string): string {
    const names = new Set(
      config.audio_processing_presets.map((preset) => preset.name.trim().toLowerCase()),
    );
    if (!names.has(base.toLowerCase())) return base;
    for (let index = 2; index < 100; index += 1) {
      const candidate = `${base} ${index}`;
      if (!names.has(candidate.toLowerCase())) return candidate;
    }
    return `${base} ${config.audio_processing_presets.length + 1}`;
  }

  function createPreset(): AudioProcessingPreset {
    return {
      id: newId("preset"),
      name: uniqueName(t("settings.presets.new_name")),
      steps: [newStep(Operation.Denoise, config, newId)],
      graph: {
        enabled: false,
        parameters: graphParametersFromConfig(config),
      },
    };
  }

  function addPreset(): void {
    const preset = createPreset();
    config.audio_processing_presets = [...config.audio_processing_presets, preset];
    selectedPresetId = preset.id;
  }

  function duplicatePreset(preset: AudioProcessingPreset): void {
    const copy = structuredClone(preset);
    copy.id = newId("preset");
    copy.name = uniqueName(`${preset.name} ${t("settings.presets.copy_suffix")}`);
    copy.steps = copy.steps.map((step) => ({ ...step, id: newId("step") }));
    config.audio_processing_presets = [...config.audio_processing_presets, copy];
    selectedPresetId = copy.id;
  }

  function deletePreset(preset: AudioProcessingPreset): void {
    config.audio_processing_presets = config.audio_processing_presets.filter(
      (item) => item.id !== preset.id,
    );
  }

  function addStep(preset: AudioProcessingPreset): void {
    preset.steps = [...preset.steps, newStep(addStepOperation, config, newId)];
  }

  function removeStep(preset: AudioProcessingPreset, step: AudioProcessingPresetStep): void {
    preset.steps = preset.steps.filter((item) => item.id !== step.id);
  }

  function updateStep(
    preset: AudioProcessingPreset,
    index: number,
    step: AudioProcessingPresetStep,
  ): void {
    preset.steps = preset.steps.map((item, itemIndex) => (itemIndex === index ? step : item));
  }

  function moveStep(preset: AudioProcessingPreset, index: number, direction: -1 | 1): void {
    const nextIndex = index + direction;
    if (nextIndex < 0 || nextIndex >= preset.steps.length) return;
    const steps = [...preset.steps];
    const [step] = steps.splice(index, 1);
    if (!step) return;
    steps.splice(nextIndex, 0, step);
    preset.steps = steps;
  }

  function updateGraph(preset: AudioProcessingPreset, graph: AudioProcessingPresetGraph): void {
    preset.graph = graph;
  }
</script>

<div class="settings-card settings-stack">
  <h2>{t("settings.tab.presets")}</h2>

  <section class="settings-section" aria-labelledby="processing-presets-title">
    <div class="settings-section-header">
      <h3 id="processing-presets-title">{t("settings.presets.title")}</h3>
      <p>{t("settings.presets.summary")}</p>
    </div>

    {#if validationMessages.length > 0}
      <div class="settings-error" data-testid="preset-validation">
        {#each validationMessages as msg}
          <p>{msg.message}</p>
        {/each}
      </div>
    {/if}

    <div class="preset-layout">
      <aside class="preset-list" aria-label={t("settings.presets.list_label")}>
        {#each config.audio_processing_presets as preset}
          <button
            type="button"
            class="preset-list-item"
            class:preset-list-item-active={preset.id === selectedPresetId}
            data-testid={`preset-list-${preset.id}`}
            onclick={() => (selectedPresetId = preset.id)}
          >
            <span>{preset.name || t("settings.presets.unnamed")}</span>
            <small>
              {preset.steps.length} / {preset.graph.enabled ? t("operation.graph") : t("settings.presets.no_graph")}
            </small>
          </button>
        {/each}
        <button
          type="button"
          class="settings-button settings-button-primary"
          data-testid="preset-add"
          onclick={addPreset}
        >
          {t("settings.presets.add")}
        </button>
      </aside>

      <section class="preset-editor" aria-label={t("settings.presets.editor_label")}>
        {#if selectedPreset}
          <div class="settings-grid">
            <label class="settings-field preset-name-field">
              <span>{t("settings.presets.name")}</span>
              <input class="settings-input" bind:value={selectedPreset.name} data-testid="preset-name" />
            </label>
            <div class="preset-actions">
              <button type="button" class="settings-button" onclick={() => duplicatePreset(selectedPreset)}>
                {t("settings.presets.duplicate")}
              </button>
              <button type="button" class="settings-button" onclick={() => deletePreset(selectedPreset)}>
                {t("settings.presets.delete")}
              </button>
            </div>
          </div>

          <div class="preset-subsection">
            <div class="preset-subsection-header">
              <h4>{t("settings.presets.steps")}</h4>
              <span class="settings-muted">{t("settings.presets.steps_summary")}</span>
            </div>
            <div class="preset-add-step">
              <select
                class="settings-select"
                bind:value={addStepOperation}
                data-testid="preset-add-step-operation"
              >
                {#each TRANSFORM_OPERATIONS as operation}
                  <option value={operation}>{operationLabel(operation)}</option>
                {/each}
              </select>
              <button
                type="button"
                class="settings-button"
                data-testid="preset-add-step"
                onclick={() => addStep(selectedPreset)}
              >
                {t("settings.presets.add_step")}
              </button>
            </div>

            <div class="preset-steps">
              {#each selectedPreset.steps as step, index (step.id)}
                <PresetStepEditor
                  canMoveDown={index < selectedPreset.steps.length - 1}
                  canMoveUp={index > 0}
                  {config}
                  {index}
                  {step}
                  onChange={(nextStep) => updateStep(selectedPreset, index, nextStep)}
                  onMoveDown={() => moveStep(selectedPreset, index, 1)}
                  onMoveUp={() => moveStep(selectedPreset, index, -1)}
                  onRemove={() => removeStep(selectedPreset, step)}
                />
              {/each}
            </div>
          </div>

          <PresetGraphEditor
            graph={selectedPreset.graph}
            onChange={(graph) => updateGraph(selectedPreset, graph)}
          />
        {:else}
          <div class="preset-empty">
            <p>{t("settings.presets.empty")}</p>
            <button type="button" class="settings-button settings-button-primary" onclick={addPreset}>
              {t("settings.presets.add")}
            </button>
          </div>
        {/if}
      </section>
    </div>
  </section>
</div>
