import type { FieldSplitButtonState } from "./types.js";
import type {
  GraphRecordingCondition,
  GraphSettings,
  GraphSmoothness,
  GraphVoiceLock,
  GraphVoiceRange,
} from "./graph-settings.js";
import {
  clampGraphConnectShortDropoutsMs,
  graphRecordingConditionOrDefault,
  graphSmoothnessOrDefault,
  graphVoiceLockOrDefault,
  graphVoiceRangeOrDefault,
} from "./graph-split-values.js";
import { getSplitButtonState } from "./split-button-state.js";

export const GRAPH_SPLIT_STATE_CHANGED_EVENT = "aqe-ui:graph-split-state-changed";

export interface GraphSplitStateChangedDetail {
  ord: number;
  state: FieldSplitButtonState;
}

export function setGraphVoiceRangeForField(ord: number, value: GraphVoiceRange): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.graphEdited = true;
  state.graphVoiceRange = graphVoiceRangeOrDefault(value);
  notifyGraphSplitStateChanged(ord, state);
  return state;
}

export function setGraphRecordingConditionForField(
  ord: number,
  value: GraphRecordingCondition,
): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.graphEdited = true;
  state.graphRecordingCondition = graphRecordingConditionOrDefault(value);
  notifyGraphSplitStateChanged(ord, state);
  return state;
}

export function setGraphSmoothnessForField(ord: number, value: GraphSmoothness): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.graphEdited = true;
  state.graphSmoothness = graphSmoothnessOrDefault(value);
  notifyGraphSplitStateChanged(ord, state);
  return state;
}

export function setGraphConnectShortDropoutsForField(ord: number, value: number): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.graphEdited = true;
  state.graphConnectShortDropoutsMs = clampGraphConnectShortDropoutsMs(value);
  notifyGraphSplitStateChanged(ord, state);
  return state;
}

export function setGraphVoiceLockForField(ord: number, value: GraphVoiceLock): FieldSplitButtonState {
  const state = getSplitButtonState(ord);
  state.graphEdited = true;
  state.graphVoiceLock = graphVoiceLockOrDefault(value);
  notifyGraphSplitStateChanged(ord, state);
  return state;
}

export function graphSettingsForField(ord: number): GraphSettings {
  const state = getSplitButtonState(ord);
  return {
    connectShortDropoutsMs: state.graphConnectShortDropoutsMs,
    recordingCondition: state.graphRecordingCondition,
    smoothness: state.graphSmoothness,
    voiceLock: state.graphVoiceLock,
    voiceRange: state.graphVoiceRange,
  };
}

function notifyGraphSplitStateChanged(ord: number, state: FieldSplitButtonState): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent<GraphSplitStateChangedDetail>(
    GRAPH_SPLIT_STATE_CHANGED_EVENT,
    { detail: { ord, state } },
  ));
}
