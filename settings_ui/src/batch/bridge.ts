import { sendBridgeEnvelope } from "$lib/bridge.js";
import type {
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

declare global {
  interface Window {
    __AQE_BATCH_INITIAL_STATE__?: import("$lib/types.js").BatchInitialState;
    onBatchProgress?: (payload: BatchProgressPayload) => void;
    onBatchLog?: (payload: BatchLogPayload) => void;
    onBatchFinish?: (payload: BatchFinishPayload) => void;
    onBatchError?: (payload: BatchErrorPayload) => void;
  }
}
