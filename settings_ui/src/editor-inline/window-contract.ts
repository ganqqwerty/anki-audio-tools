import {
  getCursorIntent,
  getCursorMs,
  popEditorFrontendLog,
  popPendingGraphAnalysisRequest,
  prepareForNewNote,
  resetGraphAfterEdit,
  setControlsBusy,
  setHistoryAvailability,
  setHistorySnapshot,
  setStatus,
  setVisualizer,
  setVisualizerStatusFromPython,
} from "./actions.js";
import {
  receiveRecorderSnapshot,
  setLearnerVisualizer,
} from "./recording-actions.js";
import {
  popPendingRegionDeleteRequest,
  popPendingSplitDefaultSaveRequest,
  popPendingSourceMetadataRequest,
} from "./bridge.js";
import { receiveSourceMetadataResponse } from "./source-metadata-requests.js";
import { installEditorTestWindowContract } from "./test-contract.js";

export const EDITOR_WINDOW_CONTRACT_NAMES = [
  "__aqeGetCursorIntent",
  "__aqeGetCursorMs",
  "__aqePopPendingGraphAnalysisRequest",
  "__aqePopPendingRegionDeleteRequest",
  "__aqePopPendingSplitDefaultSaveRequest",
  "__aqePopPendingSourceMetadataRequest",
  "__aqePopFrontendLog",
  "__aqePrepareForNewNote",
  "__aqeResetGraphAfterEdit",
  "__aqeSetBusy",
  "__aqeSetHistoryAvailability",
  "__aqeSetHistorySnapshot",
  "__aqeSetLearnerRecordingState",
  "__aqeSetLearnerVisualizer",
  "__aqeSetStatus",
  "__aqeSetVisualizer",
  "__aqeSetVisualizerStatus",
  "__aqeReceiveSourceMetadataResponse",
] as const;

export function installEditorWindowContract(): void {
  window.__aqeSetBusy = setControlsBusy;
  window.__aqeSetHistoryAvailability = setHistoryAvailability;
  window.__aqeSetHistorySnapshot = setHistorySnapshot;
  window.__aqeSetLearnerRecordingState = receiveRecorderSnapshot;
  window.__aqeSetLearnerVisualizer = setLearnerVisualizer;
  window.__aqeSetStatus = setStatus;
  window.__aqeSetVisualizer = setVisualizer;
  window.__aqeSetVisualizerStatus = setVisualizerStatusFromPython;
  window.__aqeResetGraphAfterEdit = resetGraphAfterEdit;
  window.__aqeGetCursorMs = getCursorMs;
  window.__aqeGetCursorIntent = getCursorIntent;
  window.__aqePrepareForNewNote = prepareForNewNote;
  window.__aqePopFrontendLog = popEditorFrontendLog;
  window.__aqePopPendingGraphAnalysisRequest = popPendingGraphAnalysisRequest;
  window.__aqePopPendingRegionDeleteRequest = popPendingRegionDeleteRequest;
  window.__aqePopPendingSplitDefaultSaveRequest = popPendingSplitDefaultSaveRequest;
  window.__aqePopPendingSourceMetadataRequest = popPendingSourceMetadataRequest;
  window.__aqeReceiveSourceMetadataResponse = receiveSourceMetadataResponse;
  installEditorTestWindowContract();
}
