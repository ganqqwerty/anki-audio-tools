import type { FieldSplitButtonState, SplitButtonDefaults } from "./types.js";
import type { SplitDefaultSaveRequest } from "./split-default-save-types.js";
import {
  clampGraphConnectShortDropoutsMs,
  graphRecordingConditionOrDefault,
  graphSmoothnessOrDefault,
  graphVoiceLockOrDefault,
  graphVoiceRangeOrDefault,
} from "./graph-split-values.js";

type CompleteSplitButtonDefaults = Required<SplitButtonDefaults>;

export function applyPromotedGraphDefaultsToState(
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
