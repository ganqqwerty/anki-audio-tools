import type {
  AsyncDonePayload,
  AsyncOperationName,
  AsyncOperationPayloads,
  AsyncProgressPayload,
  Config,
  SaveErrorPayload,
} from "./types.js";

export function sendBridgeCommand(command: string): void {
  if (globalThis.pycmd !== undefined) {
    globalThis.pycmd(command);
  }
}

export interface BridgeEnvelope<TPayload = unknown> {
  command: string;
  payload?: TPayload;
}

export function encodeBridgeCommand<TPayload>(command: string, payload?: TPayload): string {
  const envelope: BridgeEnvelope<TPayload> = { command };
  if (payload !== undefined) {
    envelope.payload = payload;
  }
  return `bridge:${JSON.stringify(envelope)}`;
}

export function sendBridgeEnvelope<TPayload>(command: string, payload?: TPayload): void {
  sendBridgeCommand(encodeBridgeCommand(command, payload));
}

export function settingsSave(config: Config): void {
  sendBridgeEnvelope("settings.save", config);
}

export function settingsCancel(): void {
  sendBridgeEnvelope("settings.cancel");
}

export function settingsResetDefaults(): void {
  sendBridgeEnvelope("settings.reset_defaults");
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
}

declare global {
  var pycmd: ((cmd: string) => void) | undefined;
  var onAsyncProgress: ((payload: AsyncProgressPayload) => void) | undefined;
  var onAsyncDone: ((payload: AsyncDonePayload) => void) | undefined;
  var onSaveError: ((payload: SaveErrorPayload) => void) | undefined;

  interface Window {
    __INITIAL_STATE__?: import("./types.js").InitialState;
    onAsyncProgress?: (payload: AsyncProgressPayload) => void;
    onAsyncDone?: (payload: AsyncDonePayload) => void;
    onSaveError?: (payload: SaveErrorPayload) => void;
  }
}
