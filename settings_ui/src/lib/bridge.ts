import type {
  AsyncDonePayload,
  AsyncProgressPayload,
  Config,
  SaveErrorPayload,
} from "./types.js";

declare function pycmd(cmd: string): void;

export function sendBridgeCommand(command: string): void {
  if (typeof pycmd !== "undefined") {
    pycmd(command);
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

export interface BridgeCallbacks {
  onAsyncProgress?: (payload: AsyncProgressPayload) => void;
  onAsyncDone?: (payload: AsyncDonePayload) => void;
  onSaveError?: (payload: SaveErrorPayload) => void;
}

export function registerCallbacks(callbacks: BridgeCallbacks): void {
  if (callbacks.onAsyncProgress) {
    window.onAsyncProgress = callbacks.onAsyncProgress;
  }
  if (callbacks.onAsyncDone) {
    window.onAsyncDone = callbacks.onAsyncDone;
  }
  if (callbacks.onSaveError) {
    window.onSaveError = callbacks.onSaveError;
  }
}

declare global {
  interface Window {
    __INITIAL_STATE__?: import("./types.js").InitialState;
    onAsyncProgress?: (payload: AsyncProgressPayload) => void;
    onAsyncDone?: (payload: AsyncDonePayload) => void;
    onSaveError?: (payload: SaveErrorPayload) => void;
  }
}
