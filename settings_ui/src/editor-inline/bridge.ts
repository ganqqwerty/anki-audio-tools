import type { FrontendLogPayload } from "../lib/generated/contracts.js";
import type { CursorIntent, GraphAnalysisRequest, PlaybackRequest, RegionDeleteRequest } from "./types.js";

const frontendLogs: FrontendLogPayload[] = [];
let pendingGraphAnalysisRequest: GraphAnalysisRequest | null = null;
let pendingRegionDeleteRequest: RegionDeleteRequest | null = null;

export function sendBridgeCommand(command: string): void {
  if (globalThis.pycmd !== undefined) {
    globalThis.pycmd(command);
  }
}

export function focusAndSendCommand(ord: number, command: string): void {
  sendBridgeCommand(`focus:${ord}`);
  sendBridgeCommand(command);
}

export function sendGraphAnalysisRequest(request: GraphAnalysisRequest): void {
  pendingGraphAnalysisRequest = request;
  sendBridgeCommand("aqe:analyze-field");
}

export function sendEditorFrontendLog(payload: FrontendLogPayload): void {
  frontendLogs.push(payload);
  sendBridgeCommand("aqe:frontend-log");
}

export function popEditorFrontendLog(): FrontendLogPayload | null {
  return frontendLogs.shift() ?? null;
}

export function setPendingPlaybackRequest(request: PlaybackRequest): void {
  window.__aqePendingPlaybackRequest = request;
  window.__aqeLastPlaybackRequest = request;
}

export function popPendingPlaybackRequest(): PlaybackRequest | null {
  if (!window.__aqePendingPlaybackRequest) return null;
  const request = window.__aqePendingPlaybackRequest;
  window.__aqePendingPlaybackRequest = null;
  return request;
}

export function popPendingGraphAnalysisRequest(): GraphAnalysisRequest | null {
  if (!pendingGraphAnalysisRequest) return null;
  const request = pendingGraphAnalysisRequest;
  pendingGraphAnalysisRequest = null;
  return request;
}

export function setPendingRegionDeleteRequest(request: RegionDeleteRequest): void {
  pendingRegionDeleteRequest = request;
}

export function popPendingRegionDeleteRequest(): RegionDeleteRequest | null {
  if (!pendingRegionDeleteRequest) return null;
  const request = pendingRegionDeleteRequest;
  pendingRegionDeleteRequest = null;
  return request;
}

export function setCursorIntent(intent: CursorIntent): void {
  window.__aqeLastCursorIntent = intent;
}
