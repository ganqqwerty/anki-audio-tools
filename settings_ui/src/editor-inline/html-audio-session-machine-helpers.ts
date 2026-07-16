import { htmlAudioLoopStartMs, htmlAudioRequestCoversFullSource } from "./html-audio-session-request.js";
import type {
  HtmlAudioFailureReason,
  HtmlAudioSessionEffect,
  HtmlAudioSessionState,
  HtmlAudioSessionTransition,
} from "./html-audio-session-types.js";

export function failedTransition(
  state: Exclude<HtmlAudioSessionState, { kind: "empty" | "failed" }>,
  cursorMs: number,
  reason: HtmlAudioFailureReason,
  mediaErrorCode: number | null = null,
  mediaResponseStatus: number | null = null,
): HtmlAudioSessionTransition {
  return {
    state: {
      kind: "failed",
      ord: state.ord,
      source: state.source,
      cursorMs,
      reason,
      mediaErrorCode,
      mediaResponseStatus,
    },
    effects: [
      { type: "ClearProgressFrame" },
      { type: "ClearRepeatTimer" },
      { type: "ClearMetadataTimer" },
      { type: "PauseAudio" },
      { type: "PublishPlaybackState", status: "stopped", cursorMs },
      ...playbackFailureStatusEffects(state, reason, mediaErrorCode, mediaResponseStatus),
      {
        type: "LogPlaybackTelemetry",
        event: "playback.html_failed",
        data: {
          mediaErrorCode,
          mediaResponseStatus,
          reason,
          recoveryOffered: playbackRecoveryFor(state, reason, mediaErrorCode, mediaResponseStatus) !== undefined,
          sourceFilename: state.source.sourceFilename,
          sourceKind: state.source.kind,
        },
      },
    ],
  };
}

export function readyFromActive(
  state: Extract<HtmlAudioSessionState, { kind: "starting" | "playing" | "paused" | "repeat_waiting" }>,
  cursorMs: number,
): HtmlAudioSessionState {
  return {
    kind: "ready",
    ord: state.ord,
    source: state.source,
    durationMs: state.durationMs,
    cursorMs,
  };
}

export function restartLoopTransition(
  state: Extract<HtmlAudioSessionState, { kind: "starting" | "playing" | "repeat_waiting" }>,
  restartAudio: boolean,
): HtmlAudioSessionTransition {
  const request = { ...state.request, cursorMs: htmlAudioLoopStartMs(state.request) };
  const shouldReloadAudio = request.source !== "post_edit" && htmlAudioRequestCoversFullSource(request, state.durationMs);
  const resetEffects = shouldReloadAudio
    ? [{ type: "ReloadAudioSource" } as const, { type: "SeekAudio", cursorMs: request.cursorMs } as const]
    : [{ type: "SeekAudio", cursorMs: request.cursorMs } as const];
  const nextState: HtmlAudioSessionState = !restartAudio && state.kind === "playing"
    ? { ...state, request }
    : { kind: "starting", ord: state.ord, source: state.source, request, durationMs: state.durationMs };
  return {
    state: nextState,
    effects: [
      { type: "ClearRepeatTimer" },
      { type: "ClearProgressFrame" },
      ...resetEffects,
      ...(restartAudio ? [{ type: "PlayAudio" } as const] : []),
      ...(!restartAudio ? [{ type: "StartProgressFrame", cursorMs: request.cursorMs, endMs: request.endMs } as const] : []),
      ...(!restartAudio ? [{ type: "PublishPlaybackState", status: "playing", cursorMs: request.cursorMs } as const] : []),
    ],
  };
}

export function noChange(state: HtmlAudioSessionState): HtmlAudioSessionTransition {
  return { state, effects: [] };
}

export function sourceReconfigurationEffects(state: HtmlAudioSessionState): HtmlAudioSessionEffect[] {
  switch (state.kind) {
    case "loading":
    case "starting":
    case "playing":
    case "paused":
    case "repeat_waiting":
    case "post_edit_waiting":
      return [
        { type: "ClearProgressFrame" },
        { type: "ClearRepeatTimer" },
        { type: "ClearMetadataTimer" },
        { type: "PauseAudio" },
      ];
    case "empty":
    case "ready":
    case "failed":
      return [];
    default:
      return exhaustive(state);
  }
}

export function currentCursorMs(state: Exclude<HtmlAudioSessionState, { kind: "empty" | "failed" }>): number {
  switch (state.kind) {
    case "loading":
    case "ready":
    case "post_edit_waiting":
      return state.cursorMs;
    case "starting":
    case "playing":
      return state.request.cursorMs;
    case "paused":
      return state.pausedAtMs;
    case "repeat_waiting":
      return state.request.cursorMs;
    default:
      return exhaustive(state);
  }
}

function playbackFailureStatusEffects(
  state: Exclude<HtmlAudioSessionState, { kind: "empty" | "failed" }>,
  reason: HtmlAudioFailureReason,
  mediaErrorCode: number | null,
  mediaResponseStatus: number | null,
): HtmlAudioSessionEffect[] {
  const request = "request" in state ? state.request : state.kind === "loading" ? state.pendingStart : null;
  const recovery = playbackRecoveryFor(state, reason, mediaErrorCode, mediaResponseStatus);
  if (reason === "audio_error" && mediaResponseIsMissing(mediaResponseStatus)) {
    return [{
      kind: "error",
      statusCode: "AQE-MEDIA-002",
      statusKey: "editor.status.referenced_audio_missing",
      type: "ShowPlaybackStatus",
    }];
  }
  if (request?.source === "post_edit") {
    return [{
      ...(recovery ? { recovery, statusCode: "AQE-PLAYBACK-002" } : {}),
      statusKey: recovery
        ? "editor.status.browser_audio_format_unsupported_after_edit"
        : "editor.status.browser_audio_unavailable",
      type: "ShowPostEditPlaybackWarning",
    }];
  }
  if (state.source.kind === "source" && reason === "audio_error" && (mediaErrorCode === 3 || mediaErrorCode === 4)) {
    return [{
      kind: "error",
      ...(recovery ? { recovery } : {}),
      statusCode: "AQE-PLAYBACK-002",
      statusKey: "editor.status.browser_audio_format_unsupported",
      type: "ShowPlaybackStatus",
    }];
  }
  return [{ statusKey: "editor.status.browser_audio_unavailable", type: "ShowPlaybackStatus" }];
}

function playbackRecoveryFor(
  state: Exclude<HtmlAudioSessionState, { kind: "empty" | "failed" }>,
  reason: HtmlAudioFailureReason,
  mediaErrorCode: number | null,
  mediaResponseStatus: number | null,
) {
  if (state.source.kind !== "source" || reason !== "audio_error") return undefined;
  if (mediaResponseIsMissing(mediaResponseStatus)) return undefined;
  if (mediaErrorCode !== 3 && mediaErrorCode !== 4) return undefined;
  if (/\.mp3(?:[\s.]*)$/i.test(state.source.sourceFilename)) return undefined;
  return {
    fieldOrd: state.ord,
    kind: "convert_to_mp3" as const,
    sourceFilename: state.source.sourceFilename,
  };
}

function mediaResponseIsMissing(status: number | null): boolean {
  return status === 404 || status === 410;
}

export function exhaustive(value: never): never {
  throw new Error(`Unhandled html audio session case: ${JSON.stringify(value)}`);
}
