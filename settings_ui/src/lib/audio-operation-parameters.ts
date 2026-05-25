import { t } from "./i18n.js";

export type PauseAggressiveness = "gentle" | "normal" | "aggressive";
export type DpdfnetAggressiveness = "gentle" | "normal" | "aggressive";

const MIN_VOLUME_STEP_DB = 1;
const MAX_VOLUME_STEP_DB = 40;
const MIN_SPEED_STEP = 1.01;
const MAX_SPEED_STEP = 5;
const MIN_REPEAT_PAUSE_SECONDS = 0;
const MAX_REPEAT_PAUSE_SECONDS = 10;
export const DPDFNET_ATTENUATION_LIMIT_DB_VALUES = [6, 12, 18] as const;
export const DEFAULT_OUTPUT_FORMAT = "mp3";
export const OUTPUT_FORMAT_VALUES = ["mp3", "m4a", "wav", "flac"] as const;
export type OutputFormatValue = (typeof OUTPUT_FORMAT_VALUES)[number];

export function clampVolumeStepDb(value: number): number {
  if (!Number.isFinite(value)) return 15;
  return Math.max(MIN_VOLUME_STEP_DB, Math.min(MAX_VOLUME_STEP_DB, Math.round(value * 10) / 10));
}

export function clampSpeedStep(value: number): number {
  if (!Number.isFinite(value)) return 1.5;
  return Math.max(MIN_SPEED_STEP, Math.min(MAX_SPEED_STEP, Math.round(value * 100) / 100));
}

export function clampRepeatPauseSeconds(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.max(
    MIN_REPEAT_PAUSE_SECONDS,
    Math.min(MAX_REPEAT_PAUSE_SECONDS, Math.round(value * 10) / 10),
  );
}

export function clampDpdfnetAttnLimitDb(value: number): number {
  if (!Number.isFinite(value)) return 12;
  return DPDFNET_ATTENUATION_LIMIT_DB_VALUES.reduce((best, candidate) => {
    const bestDistance = Math.abs(best - value);
    const candidateDistance = Math.abs(candidate - value);
    if (candidateDistance < bestDistance) return candidate;
    if (candidateDistance === bestDistance && candidate > best) return candidate;
    return best;
  }, 12);
}

export function formatVolumeDb(value: number): string {
  const db = clampVolumeStepDb(value);
  return `${Number.isInteger(db) ? db.toFixed(0) : db.toFixed(1)} dB`;
}

export function formatSpeedStep(value: number, operation: string): string {
  void operation;
  return `x${formatMultiplier(clampSpeedStep(value))}`;
}

export function formatRepeatPauseSeconds(value: number): string {
  const seconds = clampRepeatPauseSeconds(value);
  return `${Number.isInteger(seconds) ? seconds.toFixed(0) : seconds.toFixed(1)} s`;
}

export function formatPauseAggressiveness(value: PauseAggressiveness): string {
  if (value === "aggressive") return t("settings.pause_aggressiveness.aggressive");
  if (value === "gentle") return t("settings.pause_aggressiveness.gentle");
  return t("settings.pause_aggressiveness.normal");
}

export function dpdfnetAggressiveness(value: number): DpdfnetAggressiveness {
  const db = clampDpdfnetAttnLimitDb(value);
  if (db === 6) return "gentle";
  if (db === 18) return "aggressive";
  return "normal";
}

export function formatDpdfnetAggressiveness(value: number): string {
  return formatPauseAggressiveness(dpdfnetAggressiveness(value));
}

export function isOutputFormatValue(value: unknown): value is OutputFormatValue {
  return typeof value === "string" && (OUTPUT_FORMAT_VALUES as readonly string[]).includes(value);
}

export function outputFormatOrDefault(value: unknown): OutputFormatValue {
  return isOutputFormatValue(value) ? value : DEFAULT_OUTPUT_FORMAT;
}

export function formatOutputFormat(value: unknown): string {
  const outputFormat = outputFormatOrDefault(value);
  return t(`settings.output_format.${outputFormat}`);
}

function formatMultiplier(value: number): string {
  return Number.isInteger(value) ? value.toFixed(0) : value.toFixed(2).replace(/0+$/, "").replace(/\.$/, "");
}
