import type { FrontendLogPayload } from "../lib/generated/contracts.js";
import type {
  CursorIntent,
  EditorCommandPayload,
  GraphAnalysisRequest,
  RegionDeleteRequest,
} from "./types.js";
import type { SourceMetadataRequest } from "./source-metadata-types.js";
import type { SplitDefaultSaveRequest } from "./split-default-save-types.js";

const frontendLogs: FrontendLogPayload[] = [];
const pendingGraphAnalysisRequests: GraphAnalysisRequest[] = [];
const pendingRegionDeleteRequests: RegionDeleteRequest[] = [];
const pendingSourceMetadataRequests: SourceMetadataRequest[] = [];
const pendingSplitDefaultSaveRequests: SplitDefaultSaveRequest[] = [];

export function sendBridgeCommand(command: string): void {
  if (globalThis.pycmd !== undefined) {
    globalThis.pycmd(command);
  }
}

export function focusAndSendCommand(ord: number, command: string): void {
  sendBridgeCommand(`focus:${ord}`);
  sendBridgeCommand(command);
}

export function sendCommandPayload(payload: EditorCommandPayload): void {
  window.__aqePendingCommandPayload = payload;
  sendBridgeCommand("aqe:command-payload");
}

export function focusAndSendCommandPayload(ord: number, payload: EditorCommandPayload): void {
  sendBridgeCommand(`focus:${ord}`);
  sendCommandPayload(payload);
}

export function sendExternalLinkRequest(url: string): void {
  sendCommandPayload({ command: "aqe:open-url", url });
}

export function sendGraphAnalysisRequest(request: GraphAnalysisRequest): void {
  pendingGraphAnalysisRequests.push(request);
  sendBridgeCommand("aqe:analyze-field");
}

export function sendEditorFrontendLog(payload: FrontendLogPayload): void {
  frontendLogs.push(payload);
  sendBridgeCommand("aqe:frontend-log");
}

export function sendSplitDefaultSaveRequest(request: SplitDefaultSaveRequest): void {
  pendingSplitDefaultSaveRequests.push(request);
  sendBridgeCommand("aqe:save-split-defaults");
}

export function sendSourceMetadataRequest(request: SourceMetadataRequest): void {
  pendingSourceMetadataRequests.push(request);
  sendBridgeCommand("aqe:source-metadata");
}

export function popEditorFrontendLog(): FrontendLogPayload | null {
  return frontendLogs.shift() ?? null;
}

export function clearPendingNoteScopedBridgeRequests(): void {
  pendingGraphAnalysisRequests.length = 0;
  pendingRegionDeleteRequests.length = 0;
  pendingSourceMetadataRequests.length = 0;
}

export function popPendingGraphAnalysisRequest(): GraphAnalysisRequest | null {
  return pendingGraphAnalysisRequests.shift() ?? null;
}

export function setPendingRegionDeleteRequest(request: RegionDeleteRequest): void {
  pendingRegionDeleteRequests.push(request);
}

export function popPendingRegionDeleteRequest(): RegionDeleteRequest | null {
  return pendingRegionDeleteRequests.shift() ?? null;
}

export function popPendingSplitDefaultSaveRequest(): SplitDefaultSaveRequest | null {
  return pendingSplitDefaultSaveRequests.shift() ?? null;
}

export function popPendingSourceMetadataRequest(): SourceMetadataRequest | null {
  return pendingSourceMetadataRequests.shift() ?? null;
}

export function popPendingCommandPayload(): EditorCommandPayload | null {
  const payload = window.__aqePendingCommandPayload ?? null;
  window.__aqePendingCommandPayload = null;
  return payload;
}

export function setCursorIntent(intent: CursorIntent): void {
  window.__aqeLastCursorIntent = intent;
}
