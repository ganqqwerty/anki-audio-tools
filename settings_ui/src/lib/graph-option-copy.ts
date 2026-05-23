import { t } from "./i18n.js";

export const GRAPH_VOICE_RANGES = ["bass", "low", "general", "high", "child"] as const;
export const GRAPH_RECORDING_CONDITIONS = ["auto", "very_noisy", "noisy", "normal", "clean", "studio"] as const;
export const GRAPH_SMOOTHNESSES = ["raw", "balanced", "smooth", "very_smooth"] as const;
export const GRAPH_VOICE_LOCKS = ["loose", "balanced", "stable"] as const;

export function formatGraphVoiceRange(value: string): string {
  return t(`settings.graph_voice_range.${value}`);
}

export function formatGraphRecordingCondition(value: string): string {
  return t(`settings.graph_recording_condition.${value}`);
}

export function formatGraphSmoothness(value: string): string {
  return t(`settings.graph_smoothness.${value}`);
}

export function formatGraphVoiceLock(value: string): string {
  return t(`settings.graph_voice_lock.${value}`);
}

export function graphVoiceRangeNote(): string {
  return t("graph.voice_range.note");
}

export function graphRecordingConditionNote(): string {
  return t("graph.recording_condition.note");
}

export function graphVoiceLockNote(): string {
  return t("graph.voice_lock.note");
}

export function graphConnectDropoutsNote(): string {
  return t("graph.connect_dropouts.note");
}

export function graphVoiceRangeTooltip(value: string): string {
  return t(`graph.voice_range.${value}.tooltip`);
}

export function graphRecordingConditionTooltip(value: string): string {
  return t(`graph.recording_condition.${value}.tooltip`);
}

export function graphVoiceLockTooltip(value: string): string {
  return t(`graph.voice_lock.${value}.tooltip`);
}
