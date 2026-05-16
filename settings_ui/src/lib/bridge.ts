import type {
  AsyncDonePayload,
  AsyncProgressPayload,
  Config,
  SaveErrorPayload,
} from "./types.js";

export function sendBridgeCommand(command: string): void {
  if (globalThis.pycmd !== undefined) {
    globalThis.pycmd(command);
  }
}

export function settingsSave(config: Config): void {
  sendBridgeCommand(`settings_save:${JSON.stringify(config)}`);
}

export function settingsCancel(): void {
  sendBridgeCommand("settings_cancel");
}

export function settingsResetDefaults(): void {
  sendBridgeCommand("settings_reset_defaults");
}

export function sendAsyncCmd(id: string, op: string, payload: unknown): void {
  sendBridgeCommand(`async_cmd:${JSON.stringify({ id, op, payload })}`);
}

export function copySupportReport(text: string): void {
  sendBridgeCommand(`copy_support_report:${JSON.stringify({ text })}`);
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
