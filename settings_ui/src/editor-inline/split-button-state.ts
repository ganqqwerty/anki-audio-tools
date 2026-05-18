import type {
  EditorCommand,
  EditorCommandPayload,
  FieldSplitButtonState,
  SplitButtonDefaults,
} from "./types.js";

const MIN_TRIM_MS = 50;
const MAX_TRIM_MS = 10_000;
const MIN_VOLUME_STEP_DB = 0.5;
const MAX_VOLUME_STEP_DB = 12;
const MIN_SPEED_STEP = 0.01;
const MAX_SPEED_STEP = 0.25;
const DEFAULTS: SplitButtonDefaults = {
  denoiseAlgorithm: "standard",
  pauseAggressiveness: "normal",
  speedStep: 0.05,
  trimStepMs: 100,
  volumeStepDb: 3,
};

function fieldStates(): Record<number, FieldSplitButtonState> {
  window.__aqeSplitButtonStates ??= {};
  return window.__aqeSplitButtonStates;
}

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

export function clampVolumeStepDb(value: number): number {
  if (!Number.isFinite(value)) return DEFAULTS.volumeStepDb;
  return Math.max(MIN_VOLUME_STEP_DB, Math.min(MAX_VOLUME_STEP_DB, Math.round(value * 10) / 10));
}

export function clampSpeedStep(value: number): number {
  if (!Number.isFinite(value)) return DEFAULTS.speedStep;
  return Math.max(MIN_SPEED_STEP, Math.min(MAX_SPEED_STEP, Math.round(value * 100) / 100));
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

export function formatSpeedStep(value: number, command: EditorCommand): string {
  const step = clampSpeedStep(value);
  const multiplier = command === "aqe:slower" ? 1 - step : 1 + step;
  return `x${multiplier.toFixed(2)}`;
}

export function formatPauseAggressiveness(value: FieldSplitButtonState["pauseAggressiveness"]): string {
  return value === "aggressive" ? "Aggressive" : value === "gentle" ? "Gentle" : "Normal";
}

export function formatDenoiseAlgorithm(value: FieldSplitButtonState["denoiseAlgorithm"]): string {
  return value === "rnnoise" ? "RNNoise" : "Standard";
}

export function getSplitButtonState(ord: number): FieldSplitButtonState {
  const defaults = splitButtonDefaults();
  const defaultTrimStepMs = clampTrimStepMs(defaults.trimStepMs);
  const defaultVolumeStepDb = clampVolumeStepDb(defaults.volumeStepDb);
  const defaultSpeedStep = clampSpeedStep(defaults.speedStep);
  const defaultPauseAggressiveness = defaults.pauseAggressiveness;
  const defaultDenoiseAlgorithm = defaults.denoiseAlgorithm;
  const states = fieldStates();
  const existing = states[ord];
  if (existing) {
    if (!existing.trimEdited && existing.defaultTrimStepMs !== defaultTrimStepMs) {
      existing.defaultTrimStepMs = defaultTrimStepMs;
      existing.trimStepMs = defaultTrimStepMs;
    }
    if (!existing.volumeEdited && existing.defaultVolumeStepDb !== defaultVolumeStepDb) {
      existing.defaultVolumeStepDb = defaultVolumeStepDb;
      existing.volumeStepDb = defaultVolumeStepDb;
    }
    if (!existing.speedEdited && existing.defaultSpeedStep !== defaultSpeedStep) {
      existing.defaultSpeedStep = defaultSpeedStep;
      existing.speedStep = defaultSpeedStep;
    }
    if (!existing.pauseEdited && existing.defaultPauseAggressiveness !== defaultPauseAggressiveness) {
      existing.defaultPauseAggressiveness = defaultPauseAggressiveness;
      existing.pauseAggressiveness = defaultPauseAggressiveness;
    }
    if (!existing.denoiseEdited && existing.defaultDenoiseAlgorithm !== defaultDenoiseAlgorithm) {
      existing.defaultDenoiseAlgorithm = defaultDenoiseAlgorithm;
      existing.denoiseAlgorithm = defaultDenoiseAlgorithm;
    }
    return existing;
  }
  const state = {
    defaultDenoiseAlgorithm,
    defaultPauseAggressiveness,
    defaultTrimStepMs,
    defaultVolumeStepDb,
    defaultSpeedStep,
    denoiseAlgorithm: defaultDenoiseAlgorithm,
    denoiseEdited: false,
    pauseAggressiveness: defaultPauseAggressiveness,
    pauseEdited: false,
    speedEdited: false,
    speedStep: defaultSpeedStep,
    trimEdited: false,
    trimStepMs: defaultTrimStepMs,
    volumeEdited: false,
    volumeStepDb: defaultVolumeStepDb,
  };
  states[ord] = state;
  return state;
}

export function setTrimStepForField(ord: number, value: number): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.trimEdited = true;
  state.trimStepMs = clampTrimStepMs(value);
  return state;
}

export function setVolumeStepForField(ord: number, value: number): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.volumeEdited = true;
  state.volumeStepDb = clampVolumeStepDb(value);
  return state;
}

export function setSpeedStepForField(ord: number, value: number): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.speedEdited = true;
  state.speedStep = clampSpeedStep(value);
  return state;
}

export function setPauseAggressivenessForField(
  ord: number,
  value: FieldSplitButtonState["pauseAggressiveness"],
): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.pauseEdited = true;
  state.pauseAggressiveness = value;
  return state;
}

export function setDenoiseAlgorithmForField(
  ord: number,
  value: FieldSplitButtonState["denoiseAlgorithm"],
): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.denoiseEdited = true;
  state.denoiseAlgorithm = value;
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

export function buildSplitCommandPayload(command: EditorCommand, ord: number): EditorCommandPayload {
  const state = getSplitButtonState(ord);
  if (command === "aqe:volume-up" || command === "aqe:volume-down") {
    return { command, fieldOrd: ord, overrides: { volumeStepDb: state.volumeStepDb } };
  }
  if (command === "aqe:faster" || command === "aqe:slower") {
    return { command, fieldOrd: ord, overrides: { speedStep: state.speedStep } };
  }
  if (command === "aqe:remove-pauses") {
    return { command, fieldOrd: ord, overrides: { pauseAggressiveness: state.pauseAggressiveness } };
  }
  if (command === "aqe:denoise-standard" || command === "aqe:rnnoise") {
    const selectedCommand = state.denoiseAlgorithm === "rnnoise" ? "aqe:rnnoise" : "aqe:denoise-standard";
    return { command: selectedCommand, fieldOrd: ord, overrides: { denoiseAlgorithm: state.denoiseAlgorithm } };
  }
  return buildTrimCommandPayload(command, ord);
}
