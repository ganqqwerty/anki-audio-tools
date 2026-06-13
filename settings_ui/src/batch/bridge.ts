import { sendBridgeEnvelope } from "$lib/bridge.js";
import type {
  AudioExportDestinationPayload,
  AudioExportDestinationRequest,
  AudioExportFinishPayload,
  AudioExportProgressPayload,
  AudioExportStartRequest,
  BatchErrorPayload,
  BatchFinishPayload,
  BatchLogPayload,
  BatchProgressPayload,
  BatchStartRequest,
} from "$lib/types.js";

export interface BatchCallbacks {
  onProgress?: (payload: BatchProgressPayload) => void;
  onLog?: (payload: BatchLogPayload) => void;
  onFinish?: (payload: BatchFinishPayload) => void;
  onError?: (payload: BatchErrorPayload) => void;
}

export interface AudioExportCallbacks {
  onDestination?: (payload: AudioExportDestinationPayload) => void;
  onProgress?: (payload: AudioExportProgressPayload) => void;
  onLog?: (payload: BatchLogPayload) => void;
  onFinish?: (payload: AudioExportFinishPayload) => void;
  onError?: (payload: BatchErrorPayload) => void;
}

export function batchStart(request: BatchStartRequest): void {
  sendBridgeEnvelope("batch.start", request);
}

export function batchCancel(): void {
  sendBridgeEnvelope("batch.cancel");
}

export function batchClose(): void {
  sendBridgeEnvelope("batch.close");
}

export function batchCopyLog(): void {
  sendBridgeEnvelope("batch.copy_log");
}

export function registerBatchCallbacks(callbacks: BatchCallbacks): void {
  if (callbacks.onProgress) window.onBatchProgress = callbacks.onProgress;
  if (callbacks.onLog) window.onBatchLog = callbacks.onLog;
  if (callbacks.onFinish) window.onBatchFinish = callbacks.onFinish;
  if (callbacks.onError) window.onBatchError = callbacks.onError;
}

export function audioExportChooseDestination(request: AudioExportDestinationRequest): void {
  sendBridgeEnvelope("audio-export.choose-destination", request);
}

export function audioExportStart(request: AudioExportStartRequest): void {
  sendBridgeEnvelope("audio-export.start", request);
}

export function audioExportCancel(): void {
  sendBridgeEnvelope("audio-export.cancel");
}

export function audioExportClose(): void {
  sendBridgeEnvelope("audio-export.close");
}

export function audioExportCopyLog(): void {
  sendBridgeEnvelope("audio-export.copy_log");
}

export function registerAudioExportCallbacks(callbacks: AudioExportCallbacks): void {
  if (callbacks.onDestination) window.onAudioExportDestination = callbacks.onDestination;
  if (callbacks.onProgress) window.onAudioExportProgress = callbacks.onProgress;
  if (callbacks.onLog) window.onAudioExportLog = callbacks.onLog;
  if (callbacks.onFinish) window.onAudioExportFinish = callbacks.onFinish;
  if (callbacks.onError) window.onAudioExportError = callbacks.onError;
}

declare global {
  interface Window {
    __AQE_BATCH_INITIAL_STATE__?: import("$lib/types.js").BatchInitialState | import("$lib/types.js").AudioExportInitialState;
    onBatchProgress?: (payload: BatchProgressPayload) => void;
    onBatchLog?: (payload: BatchLogPayload) => void;
    onBatchFinish?: (payload: BatchFinishPayload) => void;
    onBatchError?: (payload: BatchErrorPayload) => void;
    onAudioExportDestination?: (payload: AudioExportDestinationPayload) => void;
    onAudioExportProgress?: (payload: AudioExportProgressPayload) => void;
    onAudioExportLog?: (payload: BatchLogPayload) => void;
    onAudioExportFinish?: (payload: AudioExportFinishPayload) => void;
    onAudioExportError?: (payload: BatchErrorPayload) => void;
  }
}
