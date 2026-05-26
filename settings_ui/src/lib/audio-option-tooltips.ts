import { t } from "./i18n.js";

export function choiceTooltip(label: string, description: string): string {
  return description.trim().length > 0 ? `${label}\n${description}` : label;
}

export function denoiseAlgorithmTooltip(value: string): string {
  return t(`settings.denoise_algorithm.${value}.tooltip`);
}

export function dpdfnetAggressivenessTooltip(value: number): string {
  return t(`settings.dpdfnet_attn_limit_db.${dpdfnetAggressivenessKey(value)}.tooltip`);
}

export function pauseAggressivenessTooltip(value: string): string {
  return t(`editor.split.option.pause.${value}.description`);
}

export function pauseDetectionAlgorithmTooltip(value: string): string {
  return t(`settings.pause_detection_algorithm.${value}.tooltip`);
}

export function pitchHumModeTooltip(value: string): string {
  return t(`editor.split.option.pitch_hum.${value}.description`);
}

export function shareTargetTooltip(value: string): string {
  return t(`settings.share_target.${value}.tooltip`);
}

function dpdfnetAggressivenessKey(value: number): "gentle" | "normal" | "aggressive" {
  if (value <= 9) return "gentle";
  if (value >= 18) return "aggressive";
  return "normal";
}
