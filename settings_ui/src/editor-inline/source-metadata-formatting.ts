import { t } from "../lib/i18n.js";
import type { AudioSourceMetadataSummary } from "../lib/size-reduction-parameters.js";

export function formatSourceMetadata(metadata: AudioSourceMetadataSummary | undefined): string | null {
  if (!metadata) return null;
  return t("settings.size_reduction_source_metadata", {
    bitRate: formatBitRate(metadata.bitRate),
    sampleRate: formatSampleRate(metadata.sampleRate),
    channels: formatChannels(metadata.channels),
    size: formatFileSize(metadata.fileSizeBytes),
  });
}

function formatBitRate(value: number | null | undefined): string {
  if (!isPositiveNumber(value)) return t("settings.size_reduction_source_metadata.unknown");
  return `${Math.max(1, Math.round(value / 1000))} kbps`;
}

function formatSampleRate(value: number | null | undefined): string {
  if (!isPositiveNumber(value)) return t("settings.size_reduction_source_metadata.unknown");
  return `${Math.round(value)} Hz`;
}

function formatChannels(value: number | null | undefined): string {
  if (!isPositiveNumber(value)) return t("settings.size_reduction_source_metadata.unknown");
  return String(Math.round(value));
}

function formatFileSize(value: number | null | undefined): string {
  if (!isPositiveNumber(value)) return t("settings.size_reduction_source_metadata.unknown");
  const units = ["bytes", "KB", "MB", "GB", "TB"] as const;
  let scaled = value;
  let unitIndex = 0;
  while (scaled >= 1024 && unitIndex < units.length - 1) {
    scaled /= 1024;
    unitIndex += 1;
  }
  const compactValue = unitIndex === 0
    ? `${Math.round(scaled)} ${units[unitIndex]}`
    : `${stripTrailingZero(scaled.toFixed(1))} ${units[unitIndex]}`;
  const exactBytes = new Intl.NumberFormat("en-US").format(Math.round(value));
  return `${compactValue} (${exactBytes} bytes)`;
}

function stripTrailingZero(value: string): string {
  return value.endsWith(".0") ? value.slice(0, -2) : value;
}

function isPositiveNumber(value: number | null | undefined): value is number {
  return typeof value === "number" && Number.isFinite(value) && value > 0;
}
