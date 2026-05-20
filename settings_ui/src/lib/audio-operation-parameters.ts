import { t } from "./i18n.js";

export type PauseAggressiveness = "gentle" | "normal" | "aggressive";

const MIN_TRIM_MS = 50;
const MAX_TRIM_MS = 10_000;
const MIN_VOLUME_STEP_DB = 0.5;
const MAX_VOLUME_STEP_DB = 12;
const MIN_SPEED_STEP = 0.01;
const MAX_SPEED_STEP = 0.25;
const MIN_REPEAT_PAUSE_SECONDS = 0;
const MAX_REPEAT_PAUSE_SECONDS = 10;

export function clampTrimStepMs(value: number): number {
  if (!Number.isFinite(value)) return 100;
  return Math.max(MIN_TRIM_MS, Math.min(MAX_TRIM_MS, Math.round(value)));
}

export function clampVolumeStepDb(value: number): number {
  if (!Number.isFinite(value)) return 3;
  return Math.max(MIN_VOLUME_STEP_DB, Math.min(MAX_VOLUME_STEP_DB, Math.round(value * 10) / 10));
}

export function clampSpeedStep(value: number): number {
  if (!Number.isFinite(value)) return 0.05;
  return Math.max(MIN_SPEED_STEP, Math.min(MAX_SPEED_STEP, Math.round(value * 100) / 100));
}

export function clampRepeatPauseSeconds(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.max(
    MIN_REPEAT_PAUSE_SECONDS,
    Math.min(MAX_REPEAT_PAUSE_SECONDS, Math.round(value * 10) / 10),
  );
}

export function formatTrimMs(value: number): string {
  const ms = clampTrimStepMs(value);
  if (ms < 1000) return `${ms} ms`;
  const seconds = ms / 1000;
  return `${Number.isInteger(seconds) ? seconds.toFixed(0) : seconds.toFixed(1)} s`;
}

export function formatVolumeDb(value: number): string {
  const db = clampVolumeStepDb(value);
  return `${Number.isInteger(db) ? db.toFixed(0) : db.toFixed(1)} dB`;
}

export function formatSpeedStep(value: number, operation: string): string {
  const step = clampSpeedStep(value);
  const multiplier = operation === "aqe:slower" || operation === "slower" ? 1 - step : 1 + step;
  return `x${multiplier.toFixed(2)}`;
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
