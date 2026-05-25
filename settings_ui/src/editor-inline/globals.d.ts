import type { FrontendLogPayload, ProsodyPayload } from "../lib/generated/contracts.js";
import type {
  CursorIntent,
  CursorPositionForTest,
  EditorCommandPayload,
  EditorRuntimeConfig,
  FieldSplitButtonState,
  GraphAnalysisRequest,
  GraphStateForTest,
  PlaybackRequest,
  PlaybackState,
  PostEditPlaybackIntent,
  RegionDeleteRequest,
} from "./types.js";
import type { LearnerRecordingStatePayload } from "./recording-state.js";
import type { SplitDefaultSaveRequest } from "./split-default-save-types.js";

declare global {
  var pycmd: ((cmd: string) => void) | undefined;

  interface Window {
    __AQE_EDITOR_CONFIG__?: EditorRuntimeConfig;
    __aqeActiveField?: number | null;
    __aqeEditorDispose?: (() => void) | undefined;
    __aqeGetCursorIntent?: (() => CursorIntent) | undefined;
    __aqeGetCursorMs?: (() => number) | undefined;
    __aqeGetPlaybackRequest?: (() => PlaybackRequest) | undefined;
    __aqeGraphStateForTest?: ((ord: number) => GraphStateForTest | null) | undefined;
    __aqeHistoryAvailabilityByField?: Record<number, { canRedo: boolean; canUndo: boolean }> | undefined;
    __aqeInstallAudioPlaybackTestDriverForTest?: ((ord: number) => boolean) | undefined;
    __aqeLastCursorIntent?: CursorIntent | null;
    __aqeLastPlaybackRequest?: PlaybackRequest | null;
    __aqePendingGraphRedrawField?: number | null;
    __aqePendingGraphRedrawSource?: string | null;
    __aqePendingCommandPayload?: EditorCommandPayload | null;
    __aqePendingPlaybackRequest?: PlaybackRequest | null;
    __aqePostEditPlaybackIntents?: Record<number, PostEditPlaybackIntent> | undefined;
    __aqeSplitButtonStates?: Record<number, FieldSplitButtonState> | undefined;
    __aqePlayAfterEdit?: ((ord: number) => boolean) | undefined;
    __aqePopPendingGraphAnalysisRequest?: (() => GraphAnalysisRequest | null) | undefined;
    __aqePopPendingRegionDeleteRequest?: (() => RegionDeleteRequest | null) | undefined;
    __aqePopPendingSplitDefaultSaveRequest?: (() => SplitDefaultSaveRequest | null) | undefined;
    __aqePopFrontendLog?: (() => FrontendLogPayload | null) | undefined;
    __aqePrepareForNewNote?: (() => void) | undefined;
    __aqeResetGraphAfterEdit?: ((ord: number, sourceFilename?: string | null) => boolean) | undefined;
    __aqeScan?: (() => void) | undefined;
    __aqeSetBusy?: ((ord: number, busy: boolean, message?: string, command?: string) => void) | undefined;
    __aqeSetCursorByClientXForTest?: ((ord: number, clientX: number, notifyPython: boolean) => CursorPositionForTest | null) | undefined;
    __aqeSetCursorForTest?: ((ord: number, ms: number, notifyPython: boolean) => boolean) | undefined;
    __aqeSetHistoryAvailability?: ((ord: number, canUndo: boolean, canRedo: boolean) => void) | undefined;
    __aqeSetLearnerRecordingState?: ((payload: LearnerRecordingStatePayload) => void) | undefined;
    __aqeSetLearnerVisualizer?: ((ord: number, track: ProsodyPayload) => void) | undefined;
    __aqeSetPlaybackState?: ((ord: number, state: PlaybackState, cursorMs: number) => void) | undefined;
    __aqeSetStatus?: ((message: string, kind?: string) => void) | undefined;
    __aqeSetVisualizer?: ((ord: number, track: ProsodyPayload, cursorMs: number) => void) | undefined;
    __aqeSetVisualizerStatus?: ((ord: number, message: string, kind?: string) => void) | undefined;
    __aqeStopEditorPlayback?: ((ord: number) => boolean) | undefined;
  }
}

export {};
