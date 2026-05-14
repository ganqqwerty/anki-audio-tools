/**
 * Async job tracking — maps job IDs to pending Promises.
 *
 * Usage:
 *   const result = await startAsyncOp("test_api", { provider, api_key, model });
 *   // Python calls window.onAsyncProgress / window.onAsyncDone
 *   // Promise resolves with result or rejects with error
 */

import { sendAsyncCmd } from "./bridge.js";
import type { AsyncDonePayload, AsyncProgressPayload } from "./types.js";

interface PendingJob {
  resolve: (result: unknown) => void;
  reject: (error: Error) => void;
  // Explicit `| undefined` required by exactOptionalPropertyTypes
  onProgress: ((pct: number, message: string) => void) | undefined;
}

// Map from job ID → pending handlers
const _pending = new Map<string, PendingJob>();

let _idCounter = 0;

function _nextId(): string {
  _idCounter += 1;
  return `job_${_idCounter}_${Date.now()}`;
}

/**
 * Start an async operation and return a Promise that resolves with the result.
 *
 * @param op - Operation name (e.g. "test_api", "fetch_voices")
 * @param payload - Operation-specific payload
 * @param onProgress - Optional progress callback (pct: 0-100, message: string)
 */
export function startAsyncOp(
  op: string,
  payload: unknown,
  onProgress?: (pct: number, message: string) => void,
): Promise<unknown> {
  const id = _nextId();

  const promise = new Promise<unknown>((resolve, reject) => {
    _pending.set(id, { resolve, reject, onProgress });
  });

  sendAsyncCmd(id, op, payload);
  return promise;
}

/**
 * Handle a progress update from Python.
 * Called by bridge.ts when window.onAsyncProgress fires.
 */
export function handleAsyncProgress(payload: AsyncProgressPayload): void {
  const job = _pending.get(payload.id);
  if (job?.onProgress) {
    job.onProgress(payload.progress, payload.message);
  }
}

/**
 * Handle completion from Python.
 * Called by bridge.ts when window.onAsyncDone fires.
 */
export function handleAsyncDone(payload: AsyncDonePayload): void {
  const job = _pending.get(payload.id);
  if (!job) return;
  _pending.delete(payload.id);

  if (payload.ok) {
    job.resolve(payload.result);
  } else {
    job.reject(new Error(payload.error ?? "Unknown async error"));
  }
}

/** Exposed for testing only — clears all pending jobs. */
export function _clearPendingForTest(): void {
  _pending.clear();
  _idCounter = 0;
}
