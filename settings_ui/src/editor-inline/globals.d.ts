import type { FrontendLogPayload, ProsodyPayload, RecorderSnapshot } from "../lib/generated/contracts.js";
import type { EditorStatusMessage } from "./editor-control-state.js";
import type { GraphSettings } from "./graph-settings.js";
import type {
  CursorIntent,
  CursorPositionForTest,
  EditorCommandPayload,
  EditorRuntimeConfig,
  FieldSplitButtonState,
  GraphAnalysisRequest,
  GraphStateForTest,
  RegionDeleteRequest,
} from "./types.js";
import type { EditorFieldState } from "./field-state.js";
import type {
  SourceMetadataRequest,
  SourceMetadataResponse,
} from "./source-metadata-types.js";
import type { SplitDefaultSaveRequest } from "./split-default-save-types.js";
import type { StatusOwner } from "./control-actions.js";

declare global {
  var pycmd: ((cmd: string) => void) | undefined;

  interface Window {
    __AQE_EDITOR_CONFIG__?: EditorRuntimeConfig;
    __aqeActiveField?: number | null;
    __aqeEditorDispose?: (() => void) | undefined;
    __aqeGetCursorIntent?: (() => CursorIntent) | undefined;
    __aqeGetCursorMs?: (() => number) | undefined;
    __aqeGraphPixelBoundsForTest?: ((ord: number) => { left: number; width: number } | null) | undefined;
    __aqeFieldState?: ((ord: number) => EditorFieldState | null) | undefined;
    __aqeGraphPixelBoundsForTest?: ((ord: number) => { left: number; width: number } | null) | undefined;
    __aqeGraphStateForTest?: ((ord: number) => GraphStateForTest | null) | undefined;
    __aqeHistoryAvailabilityByField?: Record<number, { canRedo: boolean; canUndo: boolean }> | undefined;
    __aqeHistorySnapshotsByField?: Record<number, import("./types.js").HistorySnapshot> | undefined;
    __aqeInstallAudioPlaybackTestDriverForTest?: ((ord: number) => boolean) | undefined;
    __aqeLastCursorIntent?: CursorIntent | null;
    __aqePendingGraphRedrawField?: number | null;
    __aqePendingGraphRedrawPreserveLearnerOverlay?: boolean;
    __aqePendingGraphRedrawSource?: string | null;
    __aqePendingCommandPayload?: EditorCommandPayload | null;
    __aqeSplitButtonStates?: Record<number, FieldSplitButtonState> | undefined;
    __aqePopPendingGraphAnalysisRequest?: (() => GraphAnalysisRequest | null) | undefined;
    __aqePopPendingRegionDeleteRequest?: (() => RegionDeleteRequest | null) | undefined;
    __aqePopPendingSplitDefaultSaveRequest?: (() => SplitDefaultSaveRequest | null) | undefined;
    __aqePopPendingSourceMetadataRequest?: (() => SourceMetadataRequest | null) | undefined;
    __aqePopFrontendLog?: (() => FrontendLogPayload | null) | undefined;
    __aqePrepareForNewNote?: (() => void) | undefined;
    __aqeResetGraphAfterEdit?: ((
      ord: number,
      sourceFilename?: string | null,
      graphSettingsOrPreserveLearnerOverlay?: GraphSettings | boolean | null,
      preserveLearnerOverlay?: boolean,
    ) => boolean) | undefined;
    __aqeScan?: (() => void) | undefined;
    __aqeSetBusy?: ((ord: number, busy: boolean, message?: string, command?: string) => void) | undefined;
    __aqeSetCursorByClientXForTest?: ((ord: number, clientX: number, notifyPython: boolean) => CursorPositionForTest | null) | undefined;
    __aqeSetCursorForTest?: ((ord: number, ms: number, notifyPython: boolean) => boolean) | undefined;
    __aqeSetFieldStateForTest?: ((ord: number, patch: Partial<EditorFieldState>) => EditorFieldState | null) | undefined;
    __aqeSetHistoryAvailability?: ((ord: number, canUndo: boolean, canRedo: boolean) => void) | undefined;
    __aqeSetHistorySnapshot?: ((ord: number, snapshot: import("./types.js").HistorySnapshot) => void) | undefined;
    __aqeSetLearnerRecordingState?: ((payload: RecorderSnapshot) => void) | undefined;
    __aqeSetLearnerVisualizer?: ((ord: number, track: ProsodyPayload) => void) | undefined;
    __aqeSetStatus?: ((message: EditorStatusMessage, kind?: string, owner?: StatusOwner) => void) | undefined;
    __aqeSetTimeViewportForTest?: ((ord: number, startMs: number, endMs: number) => boolean) | undefined;
    __aqeSetVisualizer?: ((
      ord: number,
      track: ProsodyPayload,
      cursorMs: number,
      backendMediaGeneration?: number,
    ) => void) | undefined;
    __aqeSetVisualizerStatus?: ((ord: number, message: EditorStatusMessage, kind?: string) => void) | undefined;
    __aqeReceiveSourceMetadataResponse?: ((payload: SourceMetadataResponse) => void) | undefined;
  }
}

export {};
