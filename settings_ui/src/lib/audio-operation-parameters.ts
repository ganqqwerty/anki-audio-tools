import { t } from "./i18n.js";

export type PauseAggressiveness = "gentle" | "normal" | "aggressive";
export type DpdfnetAggressiveness = "gentle" | "normal" | "aggressive";
export const PAUSE_DETECTION_ALGORITHM_VALUES = ["silencedetect", "silero_vad"] as const;
export type PauseDetectionAlgorithmValue = (typeof PAUSE_DETECTION_ALGORITHM_VALUES)[number];
export interface PauseAdvancedParams {
  threshold: number;
  minSilenceSeconds: number;
  minSpeechSeconds: number;
  preprocessDenoise: boolean;
}

const MIN_VOLUME_STEP_DB = 1;
const MAX_VOLUME_STEP_DB = 40;
const MIN_SPEED_STEP = 1.01;
const MAX_SPEED_STEP = 5;
const MIN_REPEAT_PAUSE_SECONDS = 0;
const MAX_REPEAT_PAUSE_SECONDS = 10;
const MIN_SILENCEDETECT_THRESHOLD_DB = -100;
const MAX_SILENCEDETECT_THRESHOLD_DB = 0;
const MIN_SILERO_THRESHOLD = 0;
const MAX_SILERO_THRESHOLD = 1;
const MIN_PAUSE_SECONDS = 0.01;
const MAX_PAUSE_SECONDS = 10;
const PAUSE_PRESETS: Record<PauseDetectionAlgorithmValue, Record<PauseAggressiveness, PauseAdvancedParams>> = {
  silencedetect: {
    gentle: { threshold: -42, minSilenceSeconds: 0.45, minSpeechSeconds: 0.12, preprocessDenoise: true },
    normal: { threshold: -45, minSilenceSeconds: 0.3, minSpeechSeconds: 0.1, preprocessDenoise: true },
    aggressive: { threshold: -52, minSilenceSeconds: 0.14, minSpeechSeconds: 0.04, preprocessDenoise: true },
  },
  silero_vad: {
    gentle: { threshold: 0.55, minSilenceSeconds: 0.7, minSpeechSeconds: 0.12, preprocessDenoise: false },
    normal: { threshold: 0.5, minSilenceSeconds: 0.45, minSpeechSeconds: 0.1, preprocessDenoise: false },
    aggressive: { threshold: 0.85, minSilenceSeconds: 0.15, minSpeechSeconds: 0.04, preprocessDenoise: false },
  },
};
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

export function isPauseDetectionAlgorithmValue(value: unknown): value is PauseDetectionAlgorithmValue {
  return typeof value === "string" && (PAUSE_DETECTION_ALGORITHM_VALUES as readonly string[]).includes(value);
}

export function pauseDetectionAlgorithmOrDefault(value: unknown): PauseDetectionAlgorithmValue {
  return isPauseDetectionAlgorithmValue(value) ? value : "silencedetect";
}

export function formatPauseDetectionAlgorithm(value: unknown): string {
  const algorithm = pauseDetectionAlgorithmOrDefault(value);
  return t(`settings.pause_detection_algorithm.${algorithm}`);
}

export function pausePreset(
  algorithm: PauseDetectionAlgorithmValue,
  aggressiveness: PauseAggressiveness,
): PauseAdvancedParams {
  return { ...PAUSE_PRESETS[algorithm][aggressiveness] };
}

export function clampPauseThreshold(algorithm: PauseDetectionAlgorithmValue, value: number): number {
  const fallback = pausePreset(algorithm, "normal").threshold;
  if (!Number.isFinite(value)) return fallback;
  if (algorithm === "silero_vad") {
    return Math.max(MIN_SILERO_THRESHOLD, Math.min(MAX_SILERO_THRESHOLD, Math.round(value * 100) / 100));
  }
  return Math.max(MIN_SILENCEDETECT_THRESHOLD_DB, Math.min(MAX_SILENCEDETECT_THRESHOLD_DB, Math.round(value * 10) / 10));
}

export function clampPauseSeconds(value: number): number {
  if (!Number.isFinite(value)) return 0.1;
  return Math.max(MIN_PAUSE_SECONDS, Math.min(MAX_PAUSE_SECONDS, Math.round(value * 100) / 100));
}

export function pauseThresholdMin(algorithm: PauseDetectionAlgorithmValue): number {
  return algorithm === "silero_vad" ? MIN_SILERO_THRESHOLD : MIN_SILENCEDETECT_THRESHOLD_DB;
}

export function pauseThresholdMax(algorithm: PauseDetectionAlgorithmValue): number {
  return algorithm === "silero_vad" ? MAX_SILERO_THRESHOLD : MAX_SILENCEDETECT_THRESHOLD_DB;
}

export function pauseThresholdStep(algorithm: PauseDetectionAlgorithmValue): number {
  return algorithm === "silero_vad" ? 0.01 : 0.5;
}

export function pauseThresholdLabel(algorithm: PauseDetectionAlgorithmValue): string {
  return algorithm === "silero_vad"
    ? t("settings.pause_threshold_probability")
    : t("settings.pause_threshold_db");
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
