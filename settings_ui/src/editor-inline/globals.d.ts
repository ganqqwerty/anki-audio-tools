import type { FrontendLogPayload, ProsodyPayload } from "../lib/generated/contracts.js";
import type {
  CursorIntent,
  CursorPositionForTest,
  EditorRuntimeConfig,
  GraphStateForTest,
  PlaybackRequest,
  PlaybackState,
} from "./types.js";

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
    __aqeInstallAudioPlaybackTestDriverForTest?: ((ord: number) => boolean) | undefined;
    __aqeLastCursorIntent?: CursorIntent | null;
    __aqeLastPlaybackRequest?: PlaybackRequest | null;
    __aqePendingGraphRedrawField?: number | null;
    __aqePendingPlaybackRequest?: PlaybackRequest | null;
    __aqePopFrontendLog?: (() => FrontendLogPayload | null) | undefined;
    __aqePrepareForNewNote?: (() => void) | undefined;
    __aqeResetGraphAfterEdit?: ((ord: number) => boolean) | undefined;
    __aqeScan?: (() => void) | undefined;
    __aqeSetBusy?: ((ord: number, busy: boolean, message?: string, command?: string) => void) | undefined;
    __aqeSetCursorByClientXForTest?: ((ord: number, clientX: number, notifyPython: boolean) => CursorPositionForTest | null) | undefined;
    __aqeSetCursorForTest?: ((ord: number, ms: number, notifyPython: boolean) => boolean) | undefined;
    __aqeSetPlaybackState?: ((ord: number, state: PlaybackState, cursorMs: number) => void) | undefined;
    __aqeSetStatus?: ((message: string, kind?: string) => void) | undefined;
    __aqeSetVisualizer?: ((ord: number, track: ProsodyPayload, cursorMs: number) => void) | undefined;
    __aqeSetVisualizerStatus?: ((ord: number, message: string, kind?: string) => void) | undefined;
    __aqeStopEditorPlayback?: ((ord: number) => boolean) | undefined;
  }
}

export {};
