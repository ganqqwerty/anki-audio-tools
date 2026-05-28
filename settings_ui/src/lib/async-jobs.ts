/**
 * Async job tracking — maps job IDs to pending Promises.
 *
 * Usage:
 *   const result = await startAsyncOp("test_api", { provider, api_key, model });
 *   // Python calls window.onAsyncProgress / window.onAsyncDone
 *   // Promise resolves with result or rejects with error
 */

import { sendAsyncCmd } from "./bridge.js";
import {
  AQE_FRONTEND_INVALID_ASYNC_RESULT,
  AQE_FRONTEND_UNKNOWN_ASYNC_ERROR,
  frontendUserError,
  isUserFacingError,
} from "./user-facing-error.js";
import type {
  AsyncDonePayload,
  AsyncOperationName,
  AsyncOperationPayloads,
  AsyncOperationResults,
  AsyncProgressPayload,
  ExternalToolHealth,
  HealthReport,
  RuntimeStatus,
  ShowLogFileResult,
  SupportReportResult,
} from "./types.js";

interface PendingJob {
  op: AsyncOperationName;
  resolve: (result: unknown) => void;
  reject: (error: unknown) => void;
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
export function startAsyncOp<TOp extends AsyncOperationName>(
  op: TOp,
  payload: AsyncOperationPayloads[TOp],
  onProgress?: (pct: number, message: string) => void,
): Promise<AsyncOperationResults[TOp]> {
  const id = _nextId();

  const promise = new Promise<AsyncOperationResults[TOp]>((resolve, reject) => {
    _pending.set(id, {
      op,
      resolve: (result: unknown) => resolve(result as AsyncOperationResults[TOp]),
      reject,
      onProgress,
    });
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
    const narrowed = _narrowResult(job.op, payload.result);
    if (narrowed.ok) {
      job.resolve(narrowed.result);
    } else {
      job.reject(frontendUserError(AQE_FRONTEND_INVALID_ASYNC_RESULT, narrowed.error));
    }
  } else {
    const message = payload.error ?? "Unknown async error";
    job.reject(
      isUserFacingError(payload.user_error)
        ? payload.user_error
        : frontendUserError(AQE_FRONTEND_UNKNOWN_ASYNC_ERROR, message),
    );
  }
}

/** Exposed for testing only — clears all pending jobs. */
export function _clearPendingForTest(): void {
  _pending.clear();
  _idCounter = 0;
}

function _narrowResult(
  op: AsyncOperationName,
  result: AsyncDonePayload["result"],
):
  | { ok: true; result: AsyncOperationResults[AsyncOperationName] }
  | { ok: false; error: string } {
  if (op === "health_check" && _isHealthReport(result)) {
    return { ok: true, result };
  }
  if (op === "support_report" && _isSupportReportResult(result)) {
    return { ok: true, result };
  }
  if (op === "show_log_file" && _isShowLogFileResult(result)) {
    return { ok: true, result };
  }
  if ((op === "runtime_status" || op === "runtime_install") && _isRuntimeStatus(result)) {
    return { ok: true, result };
  }
  return {
    ok: false,
    error: `Invalid async result payload for ${op}`,
  };
}

function _isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function _isExternalToolHealth(value: unknown): value is ExternalToolHealth {
  if (!_isRecord(value)) return false;
  return (
    typeof value.available === "boolean" &&
    typeof value.path === "string" &&
    typeof value.version === "string" &&
    typeof value.error === "string"
  );
}

function _isHealthReport(value: unknown): value is HealthReport {
  if (!_isRecord(value)) return false;
  return (
    typeof value.collection_available === "boolean" &&
    typeof value.deck_count === "number" &&
    typeof value.note_type_count === "number" &&
    typeof value.card_count === "number" &&
    (value.deep_filter === undefined || _isExternalToolHealth(value.deep_filter)) &&
    (value.rnnoise === undefined || _isExternalToolHealth(value.rnnoise)) &&
    (value.dpdfnet === undefined || _isExternalToolHealth(value.dpdfnet)) &&
    (value.spleeter === undefined || _isExternalToolHealth(value.spleeter)) &&
    (value.silero_vad === undefined || _isExternalToolHealth(value.silero_vad)) &&
    (value.runtime === undefined || _isRuntimeStatus(value.runtime))
  );
}

function _isSupportReportResult(value: unknown): value is SupportReportResult {
  return _isRecord(value) && typeof value.reportText === "string";
}

function _isShowLogFileResult(value: unknown): value is ShowLogFileResult {
  return _isRecord(value) && typeof value.logFilePath === "string";
}

function _isRuntimeStatus(value: unknown): value is RuntimeStatus {
  if (!_isRecord(value)) return false;
  return (
    typeof value.phase === "string" &&
    typeof value.runtime_manifest_id === "string" &&
    typeof value.platform === "string" &&
    typeof value.runtime_root === "string" &&
    typeof value.progress === "number" &&
    typeof value.message === "string" &&
    typeof value.error === "string"
  );
}
