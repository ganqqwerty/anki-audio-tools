import type { EditorCommand, EditorCommandPayload, SplitButtonDefaults } from "./types.js";

const MIN_TRIM_MS = 50;
const MAX_TRIM_MS = 10_000;
const DEFAULTS: SplitButtonDefaults = {
  denoiseAlgorithm: "standard",
  pauseAggressiveness: "normal",
  speedStep: 0.05,
  trimStepMs: 100,
  volumeStepDb: 3,
};

interface FieldSplitButtonState {
  defaultTrimStepMs: number;
  trimEdited: boolean;
  trimStepMs: number;
}

const fieldStates = new Map<number, FieldSplitButtonState>();

export function splitButtonDefaults(): SplitButtonDefaults {
  return {
    ...DEFAULTS,
    ...window.__AQE_EDITOR_CONFIG__?.splitButtonDefaults,
  };
}

export function clampTrimStepMs(value: number): number {
  if (!Number.isFinite(value)) return DEFAULTS.trimStepMs;
  return Math.max(MIN_TRIM_MS, Math.min(MAX_TRIM_MS, Math.round(value)));
}

export function formatTrimMs(value: number): string {
  const ms = clampTrimStepMs(value);
  if (ms < 1000) return `${ms} ms`;
  const seconds = ms / 1000;
  return `${Number.isInteger(seconds) ? seconds.toFixed(0) : seconds.toFixed(1)} s`;
}

export function getSplitButtonState(ord: number): FieldSplitButtonState {
  const defaultTrimStepMs = clampTrimStepMs(splitButtonDefaults().trimStepMs);
  const existing = fieldStates.get(ord);
  if (existing) {
    if (!existing.trimEdited && existing.defaultTrimStepMs !== defaultTrimStepMs) {
      existing.defaultTrimStepMs = defaultTrimStepMs;
      existing.trimStepMs = defaultTrimStepMs;
    }
    return existing;
  }
  const state = {
    defaultTrimStepMs,
    trimEdited: false,
    trimStepMs: defaultTrimStepMs,
  };
  fieldStates.set(ord, state);
  return state;
}

export function setTrimStepForField(ord: number, value: number): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.trimEdited = true;
  state.trimStepMs = clampTrimStepMs(value);
  return state;
}

export function buildTrimCommandPayload(command: EditorCommand, ord: number): EditorCommandPayload {
  return {
    command,
    fieldOrd: ord,
    overrides: {
      trimStepMs: getSplitButtonState(ord).trimStepMs,
    },
  };
}
