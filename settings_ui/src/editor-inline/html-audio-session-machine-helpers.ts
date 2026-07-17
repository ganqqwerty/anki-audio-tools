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
      recovery: playbackRecoveryFor(state, reason, mediaErrorCode, mediaResponseStatus)
        ? "available"
        : "none",
    },
    effects: [
      { type: "ClearProgressFrame" },
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
  state: Extract<HtmlAudioSessionState, { kind: "starting" | "playing" | "paused" }>,
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

export function noChange(state: HtmlAudioSessionState): HtmlAudioSessionTransition {
  return { state, effects: [] };
}

export function sourceReconfigurationEffects(state: HtmlAudioSessionState): HtmlAudioSessionEffect[] {
  switch (state.kind) {
    case "loading":
    case "starting":
    case "playing":
    case "paused":
      return [
        { type: "ClearProgressFrame" },
        { type: "ClearMetadataTimer" },
      ];
    case "empty":
    case "ready":
    case "failed":
      return [];
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
  const passiveFailure = request === null && (reason === "audio_error" || reason === "metadata_timeout")
    ? { preserveStableError: true }
    : {};
  if (reason === "audio_error" && mediaResponseIsMissing(mediaResponseStatus)) {
    return [{
      kind: "error",
      ...passiveFailure,
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
      ...passiveFailure,
      ...(recovery ? { recovery } : {}),
      statusCode: "AQE-PLAYBACK-002",
      statusKey: "editor.status.browser_audio_format_unsupported",
      type: "ShowPlaybackStatus",
    }];
  }
  return [{
    ...passiveFailure,
    statusKey: "editor.status.browser_audio_unavailable",
    type: "ShowPlaybackStatus",
  }];
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
