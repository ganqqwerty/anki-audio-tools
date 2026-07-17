import type {
  HtmlAudioSessionEvent,
  HtmlAudioSessionState,
  HtmlAudioStartRequest,
} from "./html-audio-session-types.js";
import type {
  TransportAttemptIdentity,
  TransportFailureIdentity,
  TransportSourceIdentity,
} from "./transport/index.js";

export function transportIdentityLogContext(
  identity: TransportSourceIdentity | TransportAttemptIdentity | TransportFailureIdentity | undefined,
): Record<string, unknown> {
  if (!identity) return {};
  return {
    ...(identity && "attemptId" in identity ? { attemptId: identity.attemptId } : {}),
    ...(identity && "failureId" in identity ? { failureId: identity.failureId } : {}),
    fieldInstanceId: identity.fieldInstanceId,
    runtimeId: identity.runtimeId,
    sourceInstanceId: identity.sourceInstanceId,
  };
}

export function htmlAudioSessionStateSummary(state: HtmlAudioSessionState): Record<string, unknown> {
  const base = {
    cursorMs: "cursorMs" in state ? state.cursorMs : null,
    durationMs: "durationMs" in state ? state.durationMs : null,
    kind: state.kind,
    sourceFilename: "source" in state ? state.source?.sourceFilename : null,
  };
  if (state.kind === "loading") {
    return {
      ...base,
      pendingStart: state.pendingStart ? htmlAudioRequestSummary(state.pendingStart) : null,
    };
  }
  if ("request" in state) return { ...base, request: htmlAudioRequestSummary(state.request) };
  if (state.kind === "failed") {
    return {
      ...base,
      mediaErrorCode: state.mediaErrorCode,
      mediaResponseStatus: state.mediaResponseStatus,
      reason: state.reason,
    };
  }
  return base;
}

export function htmlAudioSessionEventSummary(event: HtmlAudioSessionEvent): Record<string, unknown> {
  switch (event.type) {
    case "SourceConfigured":
      return {
        cursorMs: event.cursorMs,
        sourceFilename: event.source.sourceFilename,
        sourceKind: event.source.kind,
        type: event.type,
      };
    case "StartRequested":
      return { request: htmlAudioRequestSummary(event.request), type: event.type };
    case "BoundaryReached":
      return {
        cursorMs: event.cursorMs,
        resetCursorMs: event.resetCursorMs,
        type: event.type,
      };
    case "MetadataLoaded":
      return { durationMs: event.durationMs, type: event.type };
    case "PlayResolved":
      return { sourceFilename: event.sourceFilename, type: event.type };
    case "PlayRejected":
      return { reason: event.reason, sourceFilename: event.sourceFilename, type: event.type };
    case "SeekFailed":
      return { cursorMs: event.cursorMs, reason: event.reason, type: event.type };
    case "AudioError":
      return {
        cursorMs: event.cursorMs,
        mediaErrorCode: event.mediaErrorCode,
        mediaResponseStatus: event.mediaResponseStatus,
        reason: event.reason,
        type: event.type,
      };
    case "PauseRequested":
    case "StopRequested":
      return { cursorMs: event.cursorMs, type: event.type };
    default:
      return { type: (event as { type: string }).type };
  }
}

function htmlAudioRequestSummary(request: HtmlAudioStartRequest): Record<string, unknown> {
  return {
    cursorMs: request.cursorMs,
    endMs: request.endMs,
    loop: request.loop,
    ord: request.ord,
    regionMode: request.regionMode,
    resetCursorMs: request.resetCursorMs,
    source: request.source,
  };
}
