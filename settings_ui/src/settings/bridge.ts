import type {
  AsyncDonePayload,
  AsyncOperationName,
  AsyncOperationPayloads,
  AsyncProgressPayload,
  Config,
  RuntimeStatus,
  SaveErrorPayload,
} from "../lib/types.js";
import { sendBridgeEnvelope } from "../lib/bridge-transport.js";

export function settingsSave(config: Config): void {
  sendBridgeEnvelope("settings.save", config);
}

export function settingsCancel(): void {
  sendBridgeEnvelope("settings.cancel");
}

export function settingsResetDefaults(): void {
  sendBridgeEnvelope("settings.reset_defaults");
}

export function settingsCheckMedia(): void {
  sendBridgeEnvelope("settings.check_media");
}

export function settingsOpenRuntimeInstaller(): void {
  sendBridgeEnvelope("settings.open_runtime_installer");
}

export function sendAsyncCmd<TOp extends AsyncOperationName>(
  id: string,
  op: TOp,
  payload: AsyncOperationPayloads[TOp],
): void {
  sendBridgeEnvelope("settings.async", { id, op, payload });
}

export function copySupportReport(text: string): void {
  sendBridgeEnvelope("support.copy_report", { text });
}

export interface BridgeCallbacks {
  onAsyncProgress?: (payload: AsyncProgressPayload) => void;
  onAsyncDone?: (payload: AsyncDonePayload) => void;
  onSaveError?: (payload: SaveErrorPayload) => void;
  onRuntimeInstallerClosed?: (payload: RuntimeStatus) => void;
}

export function registerCallbacks(callbacks: BridgeCallbacks): void {
  if (callbacks.onAsyncProgress) {
    globalThis.onAsyncProgress = callbacks.onAsyncProgress;
  }
  if (callbacks.onAsyncDone) {
    globalThis.onAsyncDone = callbacks.onAsyncDone;
  }
  if (callbacks.onSaveError) {
    globalThis.onSaveError = callbacks.onSaveError;
  }
  if (callbacks.onRuntimeInstallerClosed) {
    globalThis.onRuntimeInstallerClosed = callbacks.onRuntimeInstallerClosed;
  }
}

declare global {
  var onAsyncProgress: ((payload: AsyncProgressPayload) => void) | undefined;
  var onAsyncDone: ((payload: AsyncDonePayload) => void) | undefined;
  var onSaveError: ((payload: SaveErrorPayload) => void) | undefined;
  var onRuntimeInstallerClosed: ((payload: RuntimeStatus) => void) | undefined;

  interface Window {
    __INITIAL_STATE__?: import("../lib/types.js").InitialState;
    onAsyncProgress?: (payload: AsyncProgressPayload) => void;
    onAsyncDone?: (payload: AsyncDonePayload) => void;
    onSaveError?: (payload: SaveErrorPayload) => void;
    onRuntimeInstallerClosed?: (payload: RuntimeStatus) => void;
  }
}
