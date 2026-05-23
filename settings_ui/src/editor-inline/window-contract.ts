import {
  getCursorIntent,
  getCursorMs,
  getPlaybackRequest,
  popEditorFrontendLog,
  popPendingGraphAnalysisRequest,
  prepareForNewNote,
  resetGraphAfterEdit,
  setControlsBusy,
  setHistoryAvailability,
  setPlaybackState,
  setStatus,
  setVisualizer,
  setVisualizerStatusFromPython,
  stopEditorPlayback,
} from "./actions.js";
import { setLearnerVisualizer } from "./graph-actions.js";
import { playAfterEdit } from "./playback-actions.js";
import {
  popPendingRegionDeleteRequest,
  popPendingSplitDefaultSaveRequest,
} from "./bridge.js";
import { setLearnerRecordingState } from "./recording-actions.js";
import { installEditorTestWindowContract } from "./test-contract.js";

export const EDITOR_WINDOW_CONTRACT_NAMES = [
  "__aqeGetCursorIntent",
  "__aqeGetCursorMs",
  "__aqeGetPlaybackRequest",
  "__aqePopPendingGraphAnalysisRequest",
  "__aqePopPendingRegionDeleteRequest",
  "__aqePopPendingSplitDefaultSaveRequest",
  "__aqePopFrontendLog",
  "__aqePlayAfterEdit",
  "__aqePrepareForNewNote",
  "__aqeResetGraphAfterEdit",
  "__aqeSetBusy",
  "__aqeSetHistoryAvailability",
  "__aqeSetLearnerRecordingState",
  "__aqeSetLearnerVisualizer",
  "__aqeSetPlaybackState",
  "__aqeSetStatus",
  "__aqeSetVisualizer",
  "__aqeSetVisualizerStatus",
  "__aqeStopEditorPlayback",
] as const;

export function installEditorWindowContract(): void {
  window.__aqeSetBusy = setControlsBusy;
  window.__aqeSetHistoryAvailability = setHistoryAvailability;
  window.__aqeSetLearnerRecordingState = setLearnerRecordingState;
  window.__aqeSetLearnerVisualizer = setLearnerVisualizer;
  window.__aqeSetStatus = setStatus;
  window.__aqeSetVisualizer = setVisualizer;
  window.__aqeSetVisualizerStatus = setVisualizerStatusFromPython;
  window.__aqeResetGraphAfterEdit = resetGraphAfterEdit;
  window.__aqeSetPlaybackState = setPlaybackState;
  window.__aqeGetPlaybackRequest = getPlaybackRequest;
  window.__aqePlayAfterEdit = playAfterEdit;
  window.__aqeStopEditorPlayback = stopEditorPlayback;
  window.__aqeGetCursorMs = getCursorMs;
  window.__aqeGetCursorIntent = getCursorIntent;
  window.__aqePrepareForNewNote = prepareForNewNote;
  window.__aqePopFrontendLog = popEditorFrontendLog;
  window.__aqePopPendingGraphAnalysisRequest = popPendingGraphAnalysisRequest;
  window.__aqePopPendingRegionDeleteRequest = popPendingRegionDeleteRequest;
  window.__aqePopPendingSplitDefaultSaveRequest = popPendingSplitDefaultSaveRequest;
  installEditorTestWindowContract();
}
