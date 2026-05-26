import type { FrontendLogPayload } from "../lib/generated/contracts.js";
import type {
  CursorIntent,
  EditorCommandPayload,
  GraphAnalysisRequest,
  PlaybackRequest,
  RegionDeleteRequest,
} from "./types.js";
import type { SplitDefaultSaveRequest } from "./split-default-save-types.js";

const frontendLogs: FrontendLogPayload[] = [];
const pendingGraphAnalysisRequests: GraphAnalysisRequest[] = [];
const pendingPlaybackRequests: PlaybackRequest[] = [];
const pendingRegionDeleteRequests: RegionDeleteRequest[] = [];
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

export function focusAndSendCommandPayload(ord: number, payload: EditorCommandPayload): void {
  sendBridgeCommand(`focus:${ord}`);
  window.__aqePendingCommandPayload = payload;
  sendBridgeCommand("aqe:command-payload");
}

export function sendExternalLinkRequest(url: string): void {
  window.__aqePendingCommandPayload = { command: "aqe:open-url", url };
  sendBridgeCommand("aqe:command-payload");
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

export function popEditorFrontendLog(): FrontendLogPayload | null {
  return frontendLogs.shift() ?? null;
}

export function setPendingPlaybackRequest(request: PlaybackRequest): void {
  pendingPlaybackRequests.push(request);
  window.__aqePendingPlaybackRequest = request;
  window.__aqeLastPlaybackRequest = request;
}

export function popPendingPlaybackRequest(): PlaybackRequest | null {
  const request = pendingPlaybackRequests.shift() ?? null;
  window.__aqePendingPlaybackRequest = pendingPlaybackRequests[0] ?? null;
  return request;
}

export function clearPendingNoteScopedBridgeRequests(): void {
  pendingGraphAnalysisRequests.length = 0;
  pendingPlaybackRequests.length = 0;
  pendingRegionDeleteRequests.length = 0;
  window.__aqePendingPlaybackRequest = null;
  window.__aqeLastPlaybackRequest = null;
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

export function setCursorIntent(intent: CursorIntent): void {
  window.__aqeLastCursorIntent = intent;
}
