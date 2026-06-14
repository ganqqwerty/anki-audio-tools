import {
  AudioTriggerActionType,
  AudioTriggerRuleOperation,
  GraphRecordingCondition,
  GraphSmoothness,
  GraphVoiceLock,
  GraphVoiceRange,
  TriggerEvent,
  type AudioProcessingPreset,
  type AudioTriggerRule,
  type Config,
  type TriggerNoteTypeOption,
  type TriggerSettingsMetadata,
} from "$lib/types.js";

export const TRIGGER_OPERATIONS = [
  AudioTriggerRuleOperation.Graph,
  AudioTriggerRuleOperation.Convert,
  AudioTriggerRuleOperation.ReduceSize,
  AudioTriggerRuleOperation.Denoise,
  AudioTriggerRuleOperation.RemovePauses,
  AudioTriggerRuleOperation.Slower,
  AudioTriggerRuleOperation.Faster,
  AudioTriggerRuleOperation.VolumeDown,
  AudioTriggerRuleOperation.VolumeUp,
] as const;

export interface TriggerValidationMessage {
  ruleId: string;
  message: string;
}

export function newTriggerRule(
  config: Config,
  metadata: TriggerSettingsMetadata,
  idFactory: (prefix: string) => string,
): AudioTriggerRule {
  const noteType = metadata.note_types[0] ?? { id: null, name: "", fields: [] };
  return normalizeTriggerRule(
    {
      id: idFactory("trigger"),
      name: uniqueTriggerName(config, "New trigger"),
      enabled: true,
      event: TriggerEvent.Add,
      note_type: { id: noteType.id, name: noteType.name },
      source_field: noteType.fields[0] ?? "",
      action_type: AudioTriggerActionType.Operation,
      operation: AudioTriggerRuleOperation.Convert,
      preset_id: null,
      target_field: null,
      parameters: { target_format: config.output_format },
    },
    config,
  );
}

export function normalizeTriggerRule(rule: AudioTriggerRule, config: Config): AudioTriggerRule {
  const next: AudioTriggerRule = {
    ...rule,
    note_type: { ...rule.note_type },
    parameters: { ...rule.parameters },
  };
  if (next.action_type === AudioTriggerActionType.Preset) {
    next.operation = null;
    next.parameters = {};
    return next;
  }

  next.preset_id = null;
  if (next.operation !== AudioTriggerRuleOperation.Graph) next.target_field = null;
  if (next.operation === AudioTriggerRuleOperation.Convert) {
    next.parameters.target_format = next.parameters.target_format ?? config.output_format;
  }
  if (next.operation === AudioTriggerRuleOperation.Graph) {
    next.parameters = {
      ...next.parameters,
      graph_voice_range: next.parameters.graph_voice_range ?? config.graph_voice_range ?? GraphVoiceRange.General,
      graph_recording_condition:
        next.parameters.graph_recording_condition ??
        config.graph_recording_condition ??
        GraphRecordingCondition.Auto,
      graph_smoothness: next.parameters.graph_smoothness ?? config.graph_smoothness ?? GraphSmoothness.VerySmooth,
      graph_connect_short_dropouts_ms:
        next.parameters.graph_connect_short_dropouts_ms ??
        config.graph_connect_short_dropouts_ms ??
        240,
      graph_voice_lock: next.parameters.graph_voice_lock ?? config.graph_voice_lock ?? GraphVoiceLock.Balanced,
    };
  }
  return next;
}

export function fieldsForRule(
  rule: AudioTriggerRule,
  metadata: TriggerSettingsMetadata,
): string[] {
  return noteTypeForRule(rule, metadata)?.fields ?? [];
}

export function noteTypeForRule(
  rule: AudioTriggerRule,
  metadata: TriggerSettingsMetadata,
): TriggerNoteTypeOption | undefined {
  return metadata.note_types.find((item) =>
    rule.note_type.id !== null && item.id !== null
      ? item.id === rule.note_type.id
      : item.name === rule.note_type.name,
  );
}

export function presetRequiresGraph(preset: AudioProcessingPreset | undefined): boolean {
  return Boolean(preset?.graph.enabled);
}

export function actionSummary(rule: AudioTriggerRule, presets: AudioProcessingPreset[]): string {
  if (rule.action_type === AudioTriggerActionType.Preset) {
    return presets.find((preset) => preset.id === rule.preset_id)?.name ?? "Missing preset";
  }
  return rule.operation ?? "operation";
}

export function validateTriggerRules(
  rules: AudioTriggerRule[],
  metadata: TriggerSettingsMetadata,
  presets: AudioProcessingPreset[],
): TriggerValidationMessage[] {
  const messages: TriggerValidationMessage[] = [];
  for (const rule of rules) {
    const label = rule.name || "Trigger";
    const noteType = noteTypeForRule(rule, metadata);
    if (!rule.name.trim()) messages.push({ ruleId: rule.id, message: "Trigger names cannot be empty." });
    if (!noteType) messages.push({ ruleId: rule.id, message: `${label} has an unavailable note type.` });
    if (!rule.source_field) messages.push({ ruleId: rule.id, message: `${label} needs a source field.` });
    if (noteType && rule.source_field && !noteType.fields.includes(rule.source_field)) {
      messages.push({ ruleId: rule.id, message: `${label} source field is unavailable.` });
    }
    if (rule.action_type === AudioTriggerActionType.Preset) {
      const preset = presets.find((item) => item.id === rule.preset_id);
      if (!preset) messages.push({ ruleId: rule.id, message: `${label} needs a preset.` });
      if (presetRequiresGraph(preset) && !rule.target_field) {
        messages.push({ ruleId: rule.id, message: `${label} needs a graph target field.` });
      }
    }
    if (
      rule.action_type === AudioTriggerActionType.Operation &&
      rule.operation === AudioTriggerRuleOperation.Graph &&
      !rule.target_field
    ) {
      messages.push({ ruleId: rule.id, message: `${label} needs a graph target field.` });
    }
  }
  return messages;
}

function uniqueTriggerName(config: Config, base: string): string {
  const names = new Set(config.audio_trigger_rules.map((rule) => rule.name.trim().toLowerCase()));
  if (!names.has(base.toLowerCase())) return base;
  for (let index = 2; index < 100; index += 1) {
    const candidate = `${base} ${index}`;
    if (!names.has(candidate.toLowerCase())) return candidate;
  }
  return `${base} ${config.audio_trigger_rules.length + 1}`;
}
