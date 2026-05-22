import type {
  EditorCommand,
  EditorCommandPayload,
  FieldSplitButtonState,
  SplitButtonDefaults,
} from "./types.js";
import type { SplitDefaultSaveRequest } from "./split-default-save-types.js";
import { t } from "../lib/i18n.js";
import {
  clampRepeatPauseSeconds,
  clampDpdfnetAttnLimitDb,
  clampSpeedStep,
  clampTrimStepMs,
  clampVolumeStepDb,
} from "../lib/audio-operation-parameters.js";
import {
  clampGraphConnectShortDropoutsMs,
  defaultGraphSplitValues,
  graphRecordingConditionOrDefault,
  graphSmoothnessOrDefault,
  graphVoiceLockOrDefault,
  graphVoiceRangeOrDefault,
} from "./graph-split-values.js";
export {
  clampRepeatPauseSeconds,
  clampDpdfnetAttnLimitDb,
  clampSpeedStep,
  clampTrimStepMs,
  clampVolumeStepDb,
  formatPauseAggressiveness,
  formatDpdfnetAggressiveness,
  formatRepeatPauseSeconds,
  formatSpeedStep,
  formatTrimMs,
  formatVolumeDb,
} from "../lib/audio-operation-parameters.js";

type CompleteSplitButtonDefaults = Required<SplitButtonDefaults>;
type PitchHumMode = FieldSplitButtonState["pitchHumMode"];
const DEFAULTS: CompleteSplitButtonDefaults = {
  denoiseAlgorithm: "standard",
  dpdfnetAttnLimitDb: 12,
  ...defaultGraphSplitValues(),
  pauseAggressiveness: "normal",
  pitchHumMode: "direct",
  repeatPauseSeconds: 0,
  speedStep: 0.05,
  trimStepMs: 100,
  volumeStepDb: 3,
};

function fieldStates(): Record<number, FieldSplitButtonState> {
  window.__aqeSplitButtonStates ??= {};
  return window.__aqeSplitButtonStates;
}

export function splitButtonDefaults(): CompleteSplitButtonDefaults {
  return {
    ...DEFAULTS,
    ...window.__AQE_EDITOR_CONFIG__?.splitButtonDefaults,
  };
}

export function formatDenoiseAlgorithm(value: FieldSplitButtonState["denoiseAlgorithm"]): string {
  if (value === "rnnoise") return t("settings.denoise_algorithm.rnnoise");
  if (value === "dpdfnet") return t("settings.denoise_algorithm.dpdfnet");
  if (value === "voice_only") return t("settings.denoise_algorithm.voice_only");
  return t("settings.denoise_algorithm.standard");
}

export function formatPitchHumMode(value: PitchHumMode): string {
  if (value === "pitch_tier") return t("editor.pitch_hum.mode.pitch_tier");
  return t("editor.pitch_hum.mode.direct");
}

function pitchHumModeOrDefault(value: unknown): PitchHumMode {
  return value === "pitch_tier" ? "pitch_tier" : "direct";
}

export function getSplitButtonState(ord: number): FieldSplitButtonState {
  const defaults = splitButtonDefaults();
  const defaultGraphConnectShortDropoutsMs = clampGraphConnectShortDropoutsMs(defaults.graphConnectShortDropoutsMs);
  const defaultGraphRecordingCondition = graphRecordingConditionOrDefault(defaults.graphRecordingCondition);
  const defaultGraphSmoothness = graphSmoothnessOrDefault(defaults.graphSmoothness);
  const defaultGraphVoiceLock = graphVoiceLockOrDefault(defaults.graphVoiceLock);
  const defaultGraphVoiceRange = graphVoiceRangeOrDefault(defaults.graphVoiceRange);
  const defaultTrimStepMs = clampTrimStepMs(defaults.trimStepMs);
  const defaultVolumeStepDb = clampVolumeStepDb(defaults.volumeStepDb);
  const defaultSpeedStep = clampSpeedStep(defaults.speedStep);
  const defaultRepeatPauseSeconds = clampRepeatPauseSeconds(defaults.repeatPauseSeconds);
  const defaultPauseAggressiveness = defaults.pauseAggressiveness;
  const defaultPitchHumMode = pitchHumModeOrDefault(defaults.pitchHumMode);
  const defaultDenoiseAlgorithm = defaults.denoiseAlgorithm;
  const defaultDpdfnetAttnLimitDb = clampDpdfnetAttnLimitDb(defaults.dpdfnetAttnLimitDb);
  const states = fieldStates();
  const existing = states[ord];
  if (existing) {
    if (!Number.isFinite(existing.repeatPauseSeconds)) {
      existing.repeatPauseSeconds = defaultRepeatPauseSeconds;
      existing.defaultRepeatPauseSeconds = defaultRepeatPauseSeconds;
      existing.repeatPauseEdited = false;
    }
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
    if (!existing.repeatPauseEdited && existing.defaultRepeatPauseSeconds !== defaultRepeatPauseSeconds) {
      existing.defaultRepeatPauseSeconds = defaultRepeatPauseSeconds;
      existing.repeatPauseSeconds = defaultRepeatPauseSeconds;
    }
    if (!existing.pauseEdited && existing.defaultPauseAggressiveness !== defaultPauseAggressiveness) {
      existing.defaultPauseAggressiveness = defaultPauseAggressiveness;
      existing.pauseAggressiveness = defaultPauseAggressiveness;
    }
    if (!existing.pitchHumEdited && existing.defaultPitchHumMode !== defaultPitchHumMode) {
      existing.defaultPitchHumMode = defaultPitchHumMode;
      existing.pitchHumMode = defaultPitchHumMode;
    }
    if (!existing.denoiseEdited && existing.defaultDenoiseAlgorithm !== defaultDenoiseAlgorithm) {
      existing.defaultDenoiseAlgorithm = defaultDenoiseAlgorithm;
      existing.denoiseAlgorithm = defaultDenoiseAlgorithm;
    }
    if (!existing.dpdfnetEdited && existing.defaultDpdfnetAttnLimitDb !== defaultDpdfnetAttnLimitDb) {
      existing.defaultDpdfnetAttnLimitDb = defaultDpdfnetAttnLimitDb;
      existing.dpdfnetAttnLimitDb = defaultDpdfnetAttnLimitDb;
    }
    if (!existing.graphEdited) {
      if (existing.defaultGraphVoiceRange !== defaultGraphVoiceRange) {
        existing.defaultGraphVoiceRange = defaultGraphVoiceRange;
        existing.graphVoiceRange = defaultGraphVoiceRange;
      }
      if (existing.defaultGraphRecordingCondition !== defaultGraphRecordingCondition) {
        existing.defaultGraphRecordingCondition = defaultGraphRecordingCondition;
        existing.graphRecordingCondition = defaultGraphRecordingCondition;
      }
      if (existing.defaultGraphSmoothness !== defaultGraphSmoothness) {
        existing.defaultGraphSmoothness = defaultGraphSmoothness;
        existing.graphSmoothness = defaultGraphSmoothness;
      }
      if (existing.defaultGraphConnectShortDropoutsMs !== defaultGraphConnectShortDropoutsMs) {
        existing.defaultGraphConnectShortDropoutsMs = defaultGraphConnectShortDropoutsMs;
        existing.graphConnectShortDropoutsMs = defaultGraphConnectShortDropoutsMs;
      }
      if (existing.defaultGraphVoiceLock !== defaultGraphVoiceLock) {
        existing.defaultGraphVoiceLock = defaultGraphVoiceLock;
        existing.graphVoiceLock = defaultGraphVoiceLock;
      }
    }
    return existing;
  }
  const state = {
    defaultDenoiseAlgorithm,
    defaultDpdfnetAttnLimitDb,
    defaultGraphConnectShortDropoutsMs,
    defaultGraphRecordingCondition,
    defaultGraphSmoothness,
    defaultGraphVoiceLock,
    defaultGraphVoiceRange,
    defaultPauseAggressiveness,
    defaultPitchHumMode,
    defaultRepeatPauseSeconds,
    defaultTrimStepMs,
    defaultVolumeStepDb,
    defaultSpeedStep,
    denoiseAlgorithm: defaultDenoiseAlgorithm,
    denoiseEdited: false,
    dpdfnetAttnLimitDb: defaultDpdfnetAttnLimitDb,
    dpdfnetEdited: false,
    graphConnectShortDropoutsMs: defaultGraphConnectShortDropoutsMs,
    graphEdited: false,
    graphRecordingCondition: defaultGraphRecordingCondition,
    graphSmoothness: defaultGraphSmoothness,
    graphVoiceLock: defaultGraphVoiceLock,
    graphVoiceRange: defaultGraphVoiceRange,
    pauseAggressiveness: defaultPauseAggressiveness,
    pauseEdited: false,
    pitchHumEdited: false,
    pitchHumMode: defaultPitchHumMode,
    repeatPauseEdited: false,
    repeatPauseSeconds: defaultRepeatPauseSeconds,
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

function replaceSplitButtonDefaults(values: Partial<CompleteSplitButtonDefaults>): CompleteSplitButtonDefaults {
  const nextDefaults = {
    ...splitButtonDefaults(),
    ...values,
  };
  window.__AQE_EDITOR_CONFIG__ = {
    ...(window.__AQE_EDITOR_CONFIG__ ?? { audioFieldIndices: [] }),
    splitButtonDefaults: nextDefaults,
  };
  return nextDefaults;
}

export function promoteSplitDefaultsForField(
  ord: number,
  values: SplitDefaultSaveRequest["defaults"],
): FieldSplitButtonState {
  const splitDefaults = { ...values };
  delete splitDefaults.repeatPlaybackByDefault;
  const nextDefaults = replaceSplitButtonDefaults(splitDefaults);
  for (const [rawOrd, state] of Object.entries(fieldStates())) {
    const forceCurrentField = Number(rawOrd) === ord;
    applyPromotedDefaultsToState(state, nextDefaults, values, forceCurrentField);
  }
  return getSplitButtonState(ord);
}

function applyPromotedDefaultsToState(
  state: FieldSplitButtonState,
  defaults: CompleteSplitButtonDefaults,
  values: SplitDefaultSaveRequest["defaults"],
  forceCurrentField: boolean,
): void {
  if (values.trimStepMs !== undefined) {
    state.defaultTrimStepMs = clampTrimStepMs(defaults.trimStepMs);
    if (forceCurrentField || !state.trimEdited) state.trimStepMs = state.defaultTrimStepMs;
    if (forceCurrentField) state.trimEdited = false;
  }
  if (values.volumeStepDb !== undefined) {
    state.defaultVolumeStepDb = clampVolumeStepDb(defaults.volumeStepDb);
    if (forceCurrentField || !state.volumeEdited) state.volumeStepDb = state.defaultVolumeStepDb;
    if (forceCurrentField) state.volumeEdited = false;
  }
  if (values.speedStep !== undefined) {
    state.defaultSpeedStep = clampSpeedStep(defaults.speedStep);
    if (forceCurrentField || !state.speedEdited) state.speedStep = state.defaultSpeedStep;
    if (forceCurrentField) state.speedEdited = false;
  }
  if (values.repeatPauseSeconds !== undefined) {
    state.defaultRepeatPauseSeconds = clampRepeatPauseSeconds(defaults.repeatPauseSeconds);
    if (forceCurrentField || !state.repeatPauseEdited) state.repeatPauseSeconds = state.defaultRepeatPauseSeconds;
    if (forceCurrentField) state.repeatPauseEdited = false;
  }
  if (values.pauseAggressiveness !== undefined) {
    state.defaultPauseAggressiveness = defaults.pauseAggressiveness;
    if (forceCurrentField || !state.pauseEdited) state.pauseAggressiveness = state.defaultPauseAggressiveness;
    if (forceCurrentField) state.pauseEdited = false;
  }
  if (values.denoiseAlgorithm !== undefined) {
    state.defaultDenoiseAlgorithm = defaults.denoiseAlgorithm;
    if (forceCurrentField || !state.denoiseEdited) state.denoiseAlgorithm = state.defaultDenoiseAlgorithm;
    if (forceCurrentField) state.denoiseEdited = false;
  }
  if (values.dpdfnetAttnLimitDb !== undefined) {
    state.defaultDpdfnetAttnLimitDb = clampDpdfnetAttnLimitDb(defaults.dpdfnetAttnLimitDb);
    if (forceCurrentField || !state.dpdfnetEdited) state.dpdfnetAttnLimitDb = state.defaultDpdfnetAttnLimitDb;
    if (forceCurrentField) state.dpdfnetEdited = false;
  }
  if (values.pitchHumMode !== undefined) {
    state.defaultPitchHumMode = pitchHumModeOrDefault(defaults.pitchHumMode);
    if (forceCurrentField || !state.pitchHumEdited) state.pitchHumMode = state.defaultPitchHumMode;
    if (forceCurrentField) state.pitchHumEdited = false;
  }
  applyPromotedGraphDefaultsToState(state, defaults, values, forceCurrentField);
}

function applyPromotedGraphDefaultsToState(
  state: FieldSplitButtonState,
  defaults: CompleteSplitButtonDefaults,
  values: SplitDefaultSaveRequest["defaults"],
  forceCurrentField: boolean,
): void {
  const graphChanged =
    values.graphVoiceRange !== undefined ||
    values.graphRecordingCondition !== undefined ||
    values.graphSmoothness !== undefined ||
    values.graphConnectShortDropoutsMs !== undefined ||
    values.graphVoiceLock !== undefined;
  if (!graphChanged) return;
  state.defaultGraphVoiceRange = graphVoiceRangeOrDefault(defaults.graphVoiceRange);
  state.defaultGraphRecordingCondition = graphRecordingConditionOrDefault(defaults.graphRecordingCondition);
  state.defaultGraphSmoothness = graphSmoothnessOrDefault(defaults.graphSmoothness);
  state.defaultGraphConnectShortDropoutsMs = clampGraphConnectShortDropoutsMs(defaults.graphConnectShortDropoutsMs);
  state.defaultGraphVoiceLock = graphVoiceLockOrDefault(defaults.graphVoiceLock);
  if (forceCurrentField || !state.graphEdited) {
    state.graphVoiceRange = state.defaultGraphVoiceRange;
    state.graphRecordingCondition = state.defaultGraphRecordingCondition;
    state.graphSmoothness = state.defaultGraphSmoothness;
    state.graphConnectShortDropoutsMs = state.defaultGraphConnectShortDropoutsMs;
    state.graphVoiceLock = state.defaultGraphVoiceLock;
  }
  if (forceCurrentField) state.graphEdited = false;
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

export function setRepeatPauseSecondsForField(ord: number, value: number): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.repeatPauseEdited = true;
  state.repeatPauseSeconds = clampRepeatPauseSeconds(value);
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

export function setDpdfnetAttnLimitDbForField(ord: number, value: number): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.dpdfnetEdited = true;
  state.dpdfnetAttnLimitDb = clampDpdfnetAttnLimitDb(value);
  return state;
}

export function setPitchHumModeForField(ord: number, value: PitchHumMode): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.pitchHumEdited = true;
  state.pitchHumMode = pitchHumModeOrDefault(value);
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

function graphSettingsPayload(state: FieldSplitButtonState): NonNullable<EditorCommandPayload["graphSettings"]> {
  return {
    connectShortDropoutsMs: state.graphConnectShortDropoutsMs,
    recordingCondition: state.graphRecordingCondition,
    smoothness: state.graphSmoothness,
    voiceLock: state.graphVoiceLock,
    voiceRange: state.graphVoiceRange,
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
  if (
    command === "aqe:denoise-standard" ||
    command === "aqe:rnnoise" ||
    command === "aqe:dpdfnet" ||
    command === "aqe:voice-only"
  ) {
    const selectedCommand =
      state.denoiseAlgorithm === "rnnoise"
        ? "aqe:rnnoise"
        : state.denoiseAlgorithm === "dpdfnet"
          ? "aqe:dpdfnet"
        : state.denoiseAlgorithm === "voice_only"
          ? "aqe:voice-only"
          : "aqe:denoise-standard";
    const overrides: EditorCommandPayload["overrides"] = { denoiseAlgorithm: state.denoiseAlgorithm };
    if (state.denoiseAlgorithm === "dpdfnet") {
      overrides.dpdfnetAttnLimitDb = state.dpdfnetAttnLimitDb;
    }
    return { command: selectedCommand, fieldOrd: ord, overrides };
  }
  if (command === "aqe:analyze" || command === "aqe:pitch-hum") {
    const payload: EditorCommandPayload = {
      command,
      fieldOrd: ord,
      graphSettings: graphSettingsPayload(state),
    };
    if (command === "aqe:pitch-hum") {
      payload.overrides = { pitchHumMode: state.pitchHumMode };
    }
    return payload;
  }
  return buildTrimCommandPayload(command, ord);
}

export function buildSplitDefaultSaveRequest(command: EditorCommand, ord: number): SplitDefaultSaveRequest {
  const state = getSplitButtonState(ord);
  const request: SplitDefaultSaveRequest = {
    defaults: {},
    fieldOrd: ord,
  };
  if (command === "aqe:volume-up" || command === "aqe:volume-down") {
    request.defaults.volumeStepDb = state.volumeStepDb;
  } else if (command === "aqe:faster" || command === "aqe:slower") {
    request.defaults.speedStep = state.speedStep;
  } else if (command === "aqe:remove-pauses") {
    request.defaults.pauseAggressiveness = state.pauseAggressiveness;
  } else if (
    command === "aqe:denoise-standard" ||
    command === "aqe:rnnoise" ||
    command === "aqe:dpdfnet" ||
    command === "aqe:voice-only"
  ) {
    request.defaults.denoiseAlgorithm = state.denoiseAlgorithm;
    request.defaults.dpdfnetAttnLimitDb = state.dpdfnetAttnLimitDb;
  } else if (command === "aqe:analyze") {
    request.defaults.graphVoiceRange = state.graphVoiceRange;
    request.defaults.graphRecordingCondition = state.graphRecordingCondition;
    request.defaults.graphSmoothness = state.graphSmoothness;
    request.defaults.graphConnectShortDropoutsMs = state.graphConnectShortDropoutsMs;
    request.defaults.graphVoiceLock = state.graphVoiceLock;
  } else if (command === "aqe:pitch-hum") {
    request.defaults.pitchHumMode = state.pitchHumMode;
  } else {
    request.defaults.trimStepMs = state.trimStepMs;
  }
  return request;
}
