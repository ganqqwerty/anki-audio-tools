import { formatPauseAggressiveness } from "./audio-operation-parameters.js";

export type SizeReductionMode = "gentle" | "normal" | "aggressive";
export const SIZE_REDUCTION_MODE_VALUES = ["gentle", "normal", "aggressive"] as const;
export const SIZE_REDUCTION_SAMPLE_RATE_VALUES = [
  8000,
  11025,
  12000,
  16000,
  22050,
  24000,
  32000,
  44100,
  48000,
] as const;

const MIN_SIZE_REDUCTION_BITRATE_KBPS = 16;
const MAX_SIZE_REDUCTION_BITRATE_KBPS = 320;
const MIN_SIZE_REDUCTION_CHANNELS = 1;
const MAX_SIZE_REDUCTION_CHANNELS = 2;

export interface SizeReductionAdvancedParams {
  bitrateKbps: number;
  sampleRateHz: number;
  channels: number;
}

export interface AudioSourceMetadataSummary {
  bitRate?: number | null;
  sampleRate?: number | null;
  channels?: number | null;
}

export function isSizeReductionMode(value: unknown): value is SizeReductionMode {
  return typeof value === "string" && (SIZE_REDUCTION_MODE_VALUES as readonly string[]).includes(value);
}

export function sizeReductionModeOrDefault(value: unknown): SizeReductionMode {
  return isSizeReductionMode(value) ? value : "normal";
}

export function formatSizeReductionMode(value: SizeReductionMode): string {
  return formatPauseAggressiveness(value);
}

export function sizeReductionPreset(value: SizeReductionMode): SizeReductionAdvancedParams {
  if (value === "gentle") return { bitrateKbps: 96, sampleRateHz: 44100, channels: 2 };
  if (value === "aggressive") return { bitrateKbps: 40, sampleRateHz: 22050, channels: 1 };
  return { bitrateKbps: 64, sampleRateHz: 32000, channels: 1 };
}

export function clampSizeReductionBitrateKbps(value: number): number {
  if (!Number.isFinite(value)) return sizeReductionPreset("normal").bitrateKbps;
  return Math.max(
    MIN_SIZE_REDUCTION_BITRATE_KBPS,
    Math.min(MAX_SIZE_REDUCTION_BITRATE_KBPS, Math.round(value)),
  );
}

export function clampSizeReductionSampleRateHz(value: number): number {
  if (!Number.isFinite(value)) return sizeReductionPreset("normal").sampleRateHz;
  return SIZE_REDUCTION_SAMPLE_RATE_VALUES.reduce((best, candidate) => {
    const bestDistance = Math.abs(best - value);
    const candidateDistance = Math.abs(candidate - value);
    if (candidateDistance < bestDistance) return candidate;
    if (candidateDistance === bestDistance && candidate < best) return candidate;
    return best;
  }, sizeReductionPreset("normal").sampleRateHz);
}

export function clampSizeReductionChannels(value: number): number {
  if (!Number.isFinite(value)) return sizeReductionPreset("normal").channels;
  return Math.max(
    MIN_SIZE_REDUCTION_CHANNELS,
    Math.min(MAX_SIZE_REDUCTION_CHANNELS, Math.round(value)),
  );
}
