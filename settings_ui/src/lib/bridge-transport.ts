const BRIDGE_RETRY_DELAY_MS = 25;
const BRIDGE_MAX_ATTEMPTS = 40;

function bridgeSender(): ((cmd: string) => void) | null {
  return typeof globalThis.pycmd === "function" ? globalThis.pycmd : null;
}

export interface BridgeEnvelope<TPayload = unknown> {
  command: string;
  payload?: TPayload;
}

export function sendBridgeCommand(command: string, attempt = 0): void {
  const sender = bridgeSender();
  if (sender) {
    sender(command);
    return;
  }
  if (attempt >= BRIDGE_MAX_ATTEMPTS) {
    return;
  }
  window.setTimeout(() => sendBridgeCommand(command, attempt + 1), BRIDGE_RETRY_DELAY_MS);
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

declare global {
  var pycmd: ((cmd: string) => void) | undefined;
}
