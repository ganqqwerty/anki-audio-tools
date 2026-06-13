import {
  formatGraphRecordingCondition,
  formatGraphSmoothness,
  formatGraphVoiceLock,
  formatGraphVoiceRange,
  GRAPH_RECORDING_CONDITIONS,
  GRAPH_SMOOTHNESSES,
  GRAPH_VOICE_LOCKS,
  GRAPH_VOICE_RANGES,
} from "../lib/graph-option-copy.js";
import type {
  GraphRecordingCondition,
  GraphSmoothness,
  GraphVoiceLock,
  GraphVoiceRange,
} from "./graph-settings.js";

const DEFAULT_GRAPH_CONNECT_SHORT_DROPOUTS_MS = 240;
const DEFAULT_GRAPH_RECORDING_CONDITION: GraphRecordingCondition = "auto";
const DEFAULT_GRAPH_SMOOTHNESS: GraphSmoothness = "very_smooth";
const DEFAULT_GRAPH_VOICE_LOCK: GraphVoiceLock = "balanced";
const DEFAULT_GRAPH_VOICE_RANGE: GraphVoiceRange = "general";
const MIN_GRAPH_DROPOUT_MS = 0;
const MAX_GRAPH_DROPOUT_MS = 500;
const GRAPH_DROPOUT_STEP_MS = 30;

export function defaultGraphSplitValues(): {
  graphConnectShortDropoutsMs: number;
  graphRecordingCondition: GraphRecordingCondition;
  graphSmoothness: GraphSmoothness;
  graphVoiceLock: GraphVoiceLock;
  graphVoiceRange: GraphVoiceRange;
} {
  return {
    graphConnectShortDropoutsMs: DEFAULT_GRAPH_CONNECT_SHORT_DROPOUTS_MS,
    graphRecordingCondition: DEFAULT_GRAPH_RECORDING_CONDITION,
    graphSmoothness: DEFAULT_GRAPH_SMOOTHNESS,
    graphVoiceLock: DEFAULT_GRAPH_VOICE_LOCK,
    graphVoiceRange: DEFAULT_GRAPH_VOICE_RANGE,
  };
}

export function clampGraphConnectShortDropoutsMs(value: unknown): number {
  const numeric = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(numeric)) return DEFAULT_GRAPH_CONNECT_SHORT_DROPOUTS_MS;
  const rounded = Math.round(numeric / GRAPH_DROPOUT_STEP_MS) * GRAPH_DROPOUT_STEP_MS;
  return Math.max(MIN_GRAPH_DROPOUT_MS, Math.min(MAX_GRAPH_DROPOUT_MS, rounded));
}

export function isGraphVoiceRange(value: unknown): value is GraphVoiceRange {
  return typeof value === "string" && (GRAPH_VOICE_RANGES as readonly string[]).includes(value);
}

export function isGraphRecordingCondition(value: unknown): value is GraphRecordingCondition {
  return typeof value === "string" && (GRAPH_RECORDING_CONDITIONS as readonly string[]).includes(value);
}

export function isGraphSmoothness(value: unknown): value is GraphSmoothness {
  return typeof value === "string" && (GRAPH_SMOOTHNESSES as readonly string[]).includes(value);
}

export function isGraphVoiceLock(value: unknown): value is GraphVoiceLock {
  return typeof value === "string" && (GRAPH_VOICE_LOCKS as readonly string[]).includes(value);
}

export function graphVoiceRangeOrDefault(value: unknown): GraphVoiceRange {
  return isGraphVoiceRange(value) ? value : DEFAULT_GRAPH_VOICE_RANGE;
}

export function graphRecordingConditionOrDefault(value: unknown): GraphRecordingCondition {
  return isGraphRecordingCondition(value) ? value : DEFAULT_GRAPH_RECORDING_CONDITION;
}

export function graphSmoothnessOrDefault(value: unknown): GraphSmoothness {
  return isGraphSmoothness(value) ? value : DEFAULT_GRAPH_SMOOTHNESS;
}

export function graphVoiceLockOrDefault(value: unknown): GraphVoiceLock {
  return isGraphVoiceLock(value) ? value : DEFAULT_GRAPH_VOICE_LOCK;
}

export {
  formatGraphRecordingCondition,
  formatGraphSmoothness,
  formatGraphVoiceLock,
  formatGraphVoiceRange,
  GRAPH_RECORDING_CONDITIONS,
  GRAPH_SMOOTHNESSES,
  GRAPH_VOICE_LOCKS,
  GRAPH_VOICE_RANGES,
};
