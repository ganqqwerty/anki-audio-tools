import type { FieldSplitButtonState, SplitButtonDefaults } from "./types.js";
import { t } from "../lib/i18n.js";
import { DEFAULT_OUTPUT_FORMAT } from "../lib/audio-operation-parameters.js";
import { defaultGraphSplitValues } from "./graph-split-values.js";

type CompleteSplitButtonDefaults = Required<SplitButtonDefaults>;
type PitchHumMode = FieldSplitButtonState["pitchHumMode"];
type ShareTarget = FieldSplitButtonState["shareTarget"];

const DEFAULTS: CompleteSplitButtonDefaults = {
  denoiseAlgorithm: "standard",
  dpdfnetAttnLimitDb: 12,
  ...defaultGraphSplitValues(),
  outputFormat: DEFAULT_OUTPUT_FORMAT,
  sizeReductionMode: "normal",
  sizeReductionBitrateKbps: 64,
  sizeReductionSampleRateHz: 32000,
  sizeReductionChannels: 1,
  pauseAggressiveness: "normal",
  pauseDetectionAlgorithm: "silencedetect",
  pauseSilencedetectThresholdDb: -45,
  pauseSilencedetectMinSilenceSeconds: 0.3,
  pauseSilencedetectMinSpeechSeconds: 0.1,
  pauseSilencedetectPreprocessDenoise: true,
  pauseSileroThreshold: 0.5,
  pauseSileroMinSilenceSeconds: 0.45,
  pauseSileroMinSpeechSeconds: 0.1,
  pauseSileroPreprocessDenoise: false,
  pitchHumMode: "direct",
  repeatPauseSeconds: 0,
  shareTarget: "litterbox",
  speedStep: 1.5,
  voiceRecordingCountdownSeconds: 0,
  volumeStepDb: 15,
};

export function fieldStates(): Record<number, FieldSplitButtonState> {
  window.__aqeSplitButtonStates ??= {};
  return window.__aqeSplitButtonStates;
}

export function splitButtonDefaults(): CompleteSplitButtonDefaults {
  return {
    ...DEFAULTS,
    ...window.__AQE_EDITOR_CONFIG__?.splitButtonDefaults,
  };
}

export function clampVoiceRecordingCountdownSeconds(value: unknown): number {
  if (typeof value === "boolean" || typeof value !== "number" || !Number.isFinite(value)) {
    return 0;
  }
  return Math.max(0, Math.min(10, Math.round(value)));
}

export function formatVoiceRecordingCountdownSeconds(seconds: number): string {
  return t("editor.recording.countdown_seconds", { seconds: clampVoiceRecordingCountdownSeconds(seconds) });
}

export function pitchHumModeOrDefault(value: unknown): PitchHumMode {
  return value === "pitch_tier" ? "pitch_tier" : "direct";
}

export function shareTargetOrDefault(value: unknown): ShareTarget {
  return value === "catbox" ? "catbox" : "litterbox";
}

export type { CompleteSplitButtonDefaults, PitchHumMode, ShareTarget };
