import {
  getCursorIntent,
  getCursorMs,
  getPlaybackRequest,
  popEditorFrontendLog,
  popPendingGraphAnalysisRequest,
  prepareForNewNote,
  resetGraphAfterEdit,
  setControlsBusy,
  setPlaybackState,
  setStatus,
  setVisualizer,
  setVisualizerStatusFromPython,
  stopEditorPlayback,
} from "./actions.js";
import { popPendingRegionDeleteRequest } from "./bridge.js";
import { installEditorTestWindowContract } from "./test-contract.js";

export const EDITOR_WINDOW_CONTRACT_NAMES = [
  "__aqeGetCursorIntent",
  "__aqeGetCursorMs",
  "__aqeGetPlaybackRequest",
  "__aqePopPendingGraphAnalysisRequest",
  "__aqePopPendingRegionDeleteRequest",
  "__aqePopFrontendLog",
  "__aqePrepareForNewNote",
  "__aqeResetGraphAfterEdit",
  "__aqeSetBusy",
  "__aqeSetPlaybackState",
  "__aqeSetStatus",
  "__aqeSetVisualizer",
  "__aqeSetVisualizerStatus",
  "__aqeStopEditorPlayback",
] as const;

export function installEditorWindowContract(): void {
  window.__aqeSetBusy = setControlsBusy;
  window.__aqeSetStatus = setStatus;
  window.__aqeSetVisualizer = setVisualizer;
  window.__aqeSetVisualizerStatus = setVisualizerStatusFromPython;
  window.__aqeResetGraphAfterEdit = resetGraphAfterEdit;
  window.__aqeSetPlaybackState = setPlaybackState;
  window.__aqeGetPlaybackRequest = getPlaybackRequest;
  window.__aqeStopEditorPlayback = stopEditorPlayback;
  window.__aqeGetCursorMs = getCursorMs;
  window.__aqeGetCursorIntent = getCursorIntent;
  window.__aqePrepareForNewNote = prepareForNewNote;
  window.__aqePopFrontendLog = popEditorFrontendLog;
  window.__aqePopPendingGraphAnalysisRequest = popPendingGraphAnalysisRequest;
  window.__aqePopPendingRegionDeleteRequest = popPendingRegionDeleteRequest;
  installEditorTestWindowContract();
}
