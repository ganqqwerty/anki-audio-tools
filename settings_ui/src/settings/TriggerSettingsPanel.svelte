<script lang="ts">
  import FieldTooltipTarget from "$lib/FieldTooltipTarget.svelte";
  import { t } from "$lib/i18n.js";
  import { AudioTriggerActionType, AudioTriggerRuleOperation, TriggerEvent, type AudioTriggerRule, type Config, type TriggerNoteTypeOption, type TriggerSettingsMetadata } from "$lib/types.js";
  import { TRIGGER_OPERATIONS, actionSummary, fieldsForRule, newTriggerRule, normalizeTriggerRule, parametersForTriggerOperation, presetRequiresGraph, validateTriggerRules } from "./trigger-settings-state.js";

  const {
    config = $bindable(),
    metadata,
  }: { config: Config; metadata: TriggerSettingsMetadata } = $props();

  let selectedRuleId = $state(config.audio_trigger_rules[0]?.id ?? "");
  const selectedRule = $derived(config.audio_trigger_rules.find((rule) => rule.id === selectedRuleId));
  const validationMessages = $derived(
    validateTriggerRules(config.audio_trigger_rules, metadata, config.audio_processing_presets),
  );

  $effect(() => {
    if (config.audio_trigger_rules.some((rule) => rule.id === selectedRuleId)) return;
    selectedRuleId = config.audio_trigger_rules[0]?.id ?? "";
  });

  function newId(prefix: string): string {
    return `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
  }

  function addRule(): void {
    const rule = newTriggerRule(config, metadata, newId);
    config.audio_trigger_rules = [...config.audio_trigger_rules, rule];
    selectedRuleId = rule.id;
  }

  function duplicateRule(rule: AudioTriggerRule): void {
    const copy = structuredClone(rule);
    copy.id = newId("trigger");
    copy.name = `${rule.name} ${t("settings.presets.copy_suffix")}`;
    config.audio_trigger_rules = [...config.audio_trigger_rules, copy];
    selectedRuleId = copy.id;
  }

  function deleteRule(rule: AudioTriggerRule): void {
    config.audio_trigger_rules = config.audio_trigger_rules.filter((item) => item.id !== rule.id);
  }

  function updateRule(rule: AudioTriggerRule): void {
    const normalized = normalizeTriggerRule(rule, config);
    config.audio_trigger_rules = config.audio_trigger_rules.map((item) =>
      item.id === normalized.id ? normalized : item,
    );
  }

  function selectNoteType(rule: AudioTriggerRule, noteType: TriggerNoteTypeOption): void {
    const fields = noteType.fields;
    updateRule({
      ...rule,
      note_type: { id: noteType.id, name: noteType.name },
      source_field: fields.includes(rule.source_field) ? rule.source_field : fields[0] ?? "",
      target_field: rule.target_field && fields.includes(rule.target_field) ? rule.target_field : null,
    });
  }

  function selectedPreset(rule: AudioTriggerRule) {
    return config.audio_processing_presets.find((preset) => preset.id === rule.preset_id);
  }

  function needsTargetField(rule: AudioTriggerRule): boolean {
    if (rule.action_type === AudioTriggerActionType.Operation) {
      return rule.operation === AudioTriggerRuleOperation.Graph;
    }
    return presetRequiresGraph(selectedPreset(rule));
  }
</script>

<div class="settings-card settings-stack">
  <h2>{t("settings.tab.triggers")}</h2>

  <section class="settings-section" aria-labelledby="trigger-rules-title">
    <div class="settings-section-header">
      <h3 id="trigger-rules-title">{t("settings.triggers.title")}</h3>
      <p>{t("settings.triggers.summary")}</p>
    </div>

    {#if validationMessages.length > 0}
      <div class="settings-error" data-testid="trigger-validation">
        {#each validationMessages as msg}
          <p>{msg.message}</p>
        {/each}
      </div>
    {/if}

    <div class="preset-layout">
      <aside class="preset-list" aria-label={t("settings.triggers.list_label")}>
        {#each config.audio_trigger_rules as rule}
          <FieldTooltipTarget block content={t("settings.triggers.list_item.tooltip")}>
            <button
              type="button"
              class="preset-list-item"
              class:preset-list-item-active={rule.id === selectedRuleId}
              data-testid={`trigger-list-${rule.id}`}
              onclick={() => (selectedRuleId = rule.id)}
            >
              <span>{rule.name || t("settings.triggers.unnamed")}</span>
              <small>{rule.event} / {actionSummary(rule, config.audio_processing_presets)}</small>
            </button>
          </FieldTooltipTarget>
        {/each}
        <FieldTooltipTarget block content={t("settings.triggers.add.tooltip")}>
          <button
            type="button"
            class="settings-button settings-button-primary"
            data-testid="trigger-add"
            onclick={addRule}
          >
            {t("settings.triggers.add")}
          </button>
        </FieldTooltipTarget>
      </aside>

      <section class="preset-editor" aria-label={t("settings.triggers.editor_label")}>
        {#if selectedRule}
          <div class="settings-grid">
            <FieldTooltipTarget block content={t("settings.triggers.name.tooltip")}><label class="settings-field preset-name-field">
                <span>{t("settings.triggers.name")}</span>
                <input
                  class="settings-input"
                  data-testid="trigger-name"
                  value={selectedRule.name}
                  oninput={(event) => updateRule({ ...selectedRule, name: event.currentTarget.value })}
                />
              </label></FieldTooltipTarget>
            <FieldTooltipTarget block content={t("settings.triggers.enabled.tooltip")}><label class="settings-field">
                <span>{t("settings.triggers.enabled")}</span>
                <input
                  type="checkbox"
                  checked={selectedRule.enabled}
                  data-testid="trigger-enabled"
                  onchange={(event) => updateRule({ ...selectedRule, enabled: event.currentTarget.checked })}
                />
              </label></FieldTooltipTarget>
            <div class="preset-actions">
              <FieldTooltipTarget content={t("settings.triggers.duplicate.tooltip")}>
                <button type="button" class="settings-button" onclick={() => duplicateRule(selectedRule)}>
                  {t("settings.presets.duplicate")}
                </button>
              </FieldTooltipTarget>
              <FieldTooltipTarget content={t("settings.triggers.delete.tooltip")}>
                <button type="button" class="settings-button" onclick={() => deleteRule(selectedRule)}>
                  {t("settings.presets.delete")}
                </button>
              </FieldTooltipTarget>
            </div>
          </div>

          <div class="settings-grid">
            <FieldTooltipTarget block content={t("settings.triggers.event.tooltip")}><label class="settings-field">
                <span>{t("settings.triggers.event")}</span>
                <select
                  class="settings-select"
                  data-testid="trigger-event"
                  value={selectedRule.event}
                  onchange={(event) =>
                    updateRule({ ...selectedRule, event: event.currentTarget.value as TriggerEvent })}
                >
                  <option value={TriggerEvent.Add}>{t("settings.triggers.event.add")}</option>
                  <option value={TriggerEvent.Edit}>{t("settings.triggers.event.edit")}</option>
                </select>
              </label></FieldTooltipTarget>

            <FieldTooltipTarget block content={t("settings.triggers.note_type.tooltip")}><label class="settings-field">
                <span>{t("settings.triggers.note_type")}</span>
                <select
                  class="settings-select"
                  data-testid="trigger-note-type"
                  value={selectedRule.note_type.id ?? selectedRule.note_type.name}
                  onchange={(event) => {
                    const key = event.currentTarget.value;
                    const noteType = metadata.note_types.find((item) => String(item.id ?? item.name) === key);
                    if (noteType) selectNoteType(selectedRule, noteType);
                  }}
                >
                  {#each metadata.note_types as noteType}
                    <option value={noteType.id ?? noteType.name}>{noteType.name}</option>
                  {/each}
                </select>
              </label></FieldTooltipTarget>

            <FieldTooltipTarget block content={t("settings.triggers.source_field.tooltip")}><label class="settings-field">
                <span>{t("settings.triggers.source_field")}</span>
                <select
                  class="settings-select"
                  data-testid="trigger-source-field"
                  value={selectedRule.source_field}
                  onchange={(event) => updateRule({ ...selectedRule, source_field: event.currentTarget.value })}
                >
                  {#each fieldsForRule(selectedRule, metadata) as field}
                    <option value={field}>{field}</option>
                  {/each}
                </select>
              </label></FieldTooltipTarget>
          </div>

          <div class="settings-grid">
            <FieldTooltipTarget block content={t("settings.triggers.action.tooltip")}><label class="settings-field">
                <span>{t("settings.triggers.action")}</span>
                <select
                  class="settings-select"
                  data-testid="trigger-action-type"
                  value={selectedRule.action_type}
                  onchange={(event) =>
                    updateRule({
                      ...selectedRule,
                      action_type: event.currentTarget.value as AudioTriggerActionType,
                      operation:
                        event.currentTarget.value === AudioTriggerActionType.Operation
                          ? AudioTriggerRuleOperation.Convert
                          : null,
                      preset_id:
                        event.currentTarget.value === AudioTriggerActionType.Preset
                          ? config.audio_processing_presets[0]?.id ?? null
                          : null,
                    })}
                >
                  <option value={AudioTriggerActionType.Operation}>{t("settings.triggers.action.operation")}</option>
                  <option value={AudioTriggerActionType.Preset}>{t("settings.triggers.action.preset")}</option>
                </select>
              </label></FieldTooltipTarget>

            {#if selectedRule.action_type === AudioTriggerActionType.Operation}
              <FieldTooltipTarget block content={t("settings.triggers.operation.tooltip")}><label class="settings-field">
                  <span>{t("settings.presets.operation")}</span>
                  <select
                    class="settings-select"
                    data-testid="trigger-operation"
                    value={selectedRule.operation ?? AudioTriggerRuleOperation.Convert}
                    onchange={(event) => {
                      const operation = event.currentTarget.value as AudioTriggerRuleOperation;
                      updateRule({
                        ...selectedRule,
                        operation,
                        parameters: parametersForTriggerOperation(operation, config),
                      });
                    }}
                  >
                    {#each TRIGGER_OPERATIONS as operation}
                      <option value={operation}>{t(`operation.${operation}`)}</option>
                    {/each}
                  </select>
                </label></FieldTooltipTarget>
            {:else}
              <FieldTooltipTarget block content={t("settings.triggers.preset.tooltip")}><label class="settings-field">
                  <span>{t("settings.triggers.preset")}</span>
                  <select
                    class="settings-select"
                    data-testid="trigger-preset"
                    value={selectedRule.preset_id ?? ""}
                    onchange={(event) => updateRule({ ...selectedRule, preset_id: event.currentTarget.value || null })}
                  >
                    {#each config.audio_processing_presets as preset}
                      <option value={preset.id}>{preset.name}</option>
                    {/each}
                  </select>
                </label></FieldTooltipTarget>
            {/if}

            {#if needsTargetField(selectedRule)}
              <FieldTooltipTarget block content={t("settings.triggers.target_field.tooltip")}><label class="settings-field">
                  <span>{t("settings.triggers.target_field")}</span>
                  <select
                    class="settings-select"
                    data-testid="trigger-target-field"
                    value={selectedRule.target_field ?? ""}
                    onchange={(event) =>
                      updateRule({ ...selectedRule, target_field: event.currentTarget.value || null })}
                  >
                    <option value="">{t("settings.triggers.choose_field")}</option>
                    {#each fieldsForRule(selectedRule, metadata) as field}
                      <option value={field}>{field}</option>
                    {/each}
                  </select>
                </label></FieldTooltipTarget>
            {/if}
          </div>
        {:else}
          <div class="preset-empty">
            <p>{t("settings.triggers.empty")}</p>
          </div>
        {/if}
      </section>
    </div>
  </section>
</div>
