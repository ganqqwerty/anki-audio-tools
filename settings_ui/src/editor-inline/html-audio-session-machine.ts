import {
  exhaustive,
  failedTransition,
  noChange,
  readyFromActive,
  sourceReconfigurationEffects,
} from "./html-audio-session-machine-helpers.js";
import { htmlAudioLoopStartMs } from "./html-audio-session-request.js";
import type { HtmlAudioSessionEvent, HtmlAudioSessionState, HtmlAudioSessionTransition } from "./html-audio-session-types.js";

export type { HtmlAudioFailureReason, HtmlAudioSessionEffect, HtmlAudioSessionEvent, HtmlAudioSessionState, HtmlAudioSessionTransition, HtmlAudioSource, HtmlAudioStartRequest } from "./html-audio-session-types.js";

const METADATA_TIMEOUT_MS = 5000;

export function initialHtmlAudioSessionState(ord: number): HtmlAudioSessionState {
  return { kind: "empty", ord, cursorMs: 0 };
}

export function transitionHtmlAudioSession(
  state: HtmlAudioSessionState,
  event: HtmlAudioSessionEvent,
): HtmlAudioSessionTransition {
  switch (event.type) {
    case "SourceConfigured":
      if (!event.replace && sameConfiguredSource(state, event.source)) return noChange(state);
      return {
        state: {
          kind: "loading",
          ord: state.ord,
          source: event.source,
          cursorMs: event.cursorMs,
          pendingStart: null,
        },
        effects: [
          ...sourceReconfigurationEffects(state),
          { type: "ConfigureAudioSource", sourceFilename: event.source.sourceFilename },
          { type: "StartMetadataTimer", timeoutMs: METADATA_TIMEOUT_MS },
          { type: "PublishPlaybackState", status: "stopped" },
        ],
      };
    case "MetadataLoaded":
      if (state.kind !== "loading") {
        return noChange(state);
      }
      if (state.pendingStart !== null) {
        return {
          state: {
            kind: "starting",
            ord: state.ord,
            source: state.source,
            request: state.pendingStart,
            durationMs: event.durationMs,
          },
          effects: [
            { type: "ClearMetadataTimer" },
            { type: "SeekAudio", cursorMs: state.pendingStart.cursorMs },
            { type: "PlayAudio" },
          ],
        };
      }
      return {
        state: {
          kind: "ready",
          ord: state.ord,
          source: state.source,
          durationMs: event.durationMs,
          cursorMs: state.cursorMs,
        },
        effects: [
          { type: "ClearMetadataTimer" },
          { type: "PublishPlaybackState", status: "stopped" },
        ],
      };
    case "StartRequested":
      if (state.kind === "loading") {
        return {
          state: {
            ...state,
            pendingStart: event.request,
          },
          effects: [
            { type: "PublishPlaybackState", status: "stopped" },
            {
              type: "LogPlaybackTelemetry",
              event: "html_audio_start_deferred_until_metadata",
              data: { ord: state.ord, sourceKind: state.source.kind },
            },
          ],
        };
      }
      if (
        state.kind === "starting" ||
        state.kind === "playing" ||
        state.kind === "paused"
      ) {
        return {
          state: {
            kind: "starting",
            ord: state.ord,
            source: state.source,
            request: event.request,
            durationMs: state.durationMs,
          },
          effects: [
            { type: "ClearProgressFrame" },
            { type: "SeekAudio", cursorMs: event.request.cursorMs },
            { type: "PlayAudio" },
          ],
        };
      }
      if (state.kind !== "ready") {
        return noChange(state);
      }
      return {
        state: {
          kind: "starting",
          ord: state.ord,
          source: state.source,
          request: event.request,
          durationMs: state.durationMs,
        },
        effects: [
          ...(state.mediaExhausted ? [{ type: "ReloadAudioSource" } as const] : []),
          { type: "SeekAudio", cursorMs: event.request.cursorMs },
          { type: "PlayAudio" },
        ],
      };
    case "PlayResolved":
      if (state.kind !== "starting" || state.source.sourceFilename !== event.sourceFilename) {
        return noChange(state);
      }
      return {
        state: {
          kind: "playing",
          ord: state.ord,
          source: state.source,
          request: state.request,
          durationMs: state.durationMs,
          startedAtMs: event.nowMs,
        },
        effects: [
          { type: "StartProgressFrame", cursorMs: state.request.cursorMs, endMs: state.request.endMs },
          { type: "PublishPlaybackState", status: "playing" },
        ],
      };
    case "PlayRejected":
      if (state.kind !== "starting" || state.source.sourceFilename !== event.sourceFilename) {
        return noChange(state);
      }
      return failedTransition(state, state.request.cursorMs, event.reason);
    case "SeekFailed":
      if (state.kind === "empty" || state.kind === "failed") {
        return noChange(state);
      }
      return failedTransition(state, event.cursorMs, event.reason);
    case "PauseRequested":
      if (state.kind === "loading") {
        return { state: initialHtmlAudioSessionState(state.ord), effects: [
          { type: "PauseAudio" }, { type: "ClearProgressFrame" }, { type: "ClearMetadataTimer" },
        ] };
      }
      if (state.kind === "ready") {
        return { state, effects: [{ type: "PauseAudio" }, { type: "ClearProgressFrame" }] };
      }
      if (state.kind !== "starting" && state.kind !== "playing") return noChange(state);
      return {
        state: {
          kind: "paused",
          ord: state.ord,
          source: state.source,
          request: state.request,
          durationMs: state.durationMs,
          pausedAtMs: event.cursorMs,
        },
        effects: [
          { type: "PauseAudio" },
          { type: "ClearProgressFrame" },
          { type: "PublishPlaybackState", status: "paused", cursorMs: event.cursorMs },
        ],
      };
    case "ResumeRequested": {
      if (state.kind !== "paused") return noChange(state);
      const resumeRequest = { ...state.request, cursorMs: state.pausedAtMs };
      return {
        state: {
          kind: "starting",
          ord: state.ord,
          source: state.source,
          request: resumeRequest,
          durationMs: state.durationMs,
        },
        effects: [
          { type: "SeekAudio", cursorMs: state.pausedAtMs },
          { type: "PlayAudio" },
        ],
      };
    }
    case "StopRequested":
      if (state.kind === "loading") {
        return { state: initialHtmlAudioSessionState(state.ord), effects: [
          { type: "PauseAudio" }, { type: "ClearProgressFrame" },
          { type: "ClearMetadataTimer" }, { type: "PublishPlaybackState", status: "stopped", cursorMs: event.cursorMs },
        ] };
      }
      if (state.kind === "ready") {
        return { state, effects: [
          { type: "PauseAudio" }, { type: "ClearProgressFrame" },
          { type: "PublishPlaybackState", status: "stopped", cursorMs: event.cursorMs },
        ] };
      }
      if (state.kind !== "starting" && state.kind !== "playing" && state.kind !== "paused") {
        return noChange(state);
      }
      return {
        state: readyFromActive(state, event.cursorMs),
        effects: [
          { type: "PauseAudio" },
          { type: "ClearProgressFrame" },
          { type: "PublishPlaybackState", status: "stopped", cursorMs: event.cursorMs },
        ],
      };
    case "BoundaryReached": {
      if (state.kind !== "starting" && state.kind !== "playing") return noChange(state);
      const resetCursorMs = event.resetCursorMs ?? htmlAudioLoopStartMs(state.request);
      const mediaExhausted = event.cursorMs >= state.durationMs;
      return {
        state: {
          ...readyFromActive(state, resetCursorMs),
          ...(mediaExhausted ? { mediaExhausted: true as const } : {}),
        },
        effects: [
          { type: "PauseAudio" },
          { type: "ClearProgressFrame" },
          { request: state.request, type: "ReportPassCompleted" },
          { cursorMs: resetCursorMs, type: "CompletePlayback" },
        ],
      };
    }
    case "AudioError":
      if (state.kind === "empty" || state.kind === "failed") return noChange(state);
      return failedTransition(
        state,
        event.cursorMs,
        event.reason,
        event.mediaErrorCode,
        event.mediaResponseStatus,
      );
    case "RuntimeDisposed":
      if (state.kind === "empty") return noChange(state);
      return {
        state: initialHtmlAudioSessionState(state.ord),
        effects: [
          { type: "ClearAudioSource" },
          { type: "ClearProgressFrame" },
          { type: "ClearMetadataTimer" },
          { type: "PublishPlaybackState", status: "stopped" },
        ],
      };
    case "SourceCleared":
      return {
        state: initialHtmlAudioSessionState(state.ord),
        effects: [
          { type: "ClearAudioSource" },
          { type: "ClearProgressFrame" },
          { type: "ClearMetadataTimer" },
          { type: "PublishPlaybackState", status: "stopped" },
        ],
      };
    case "MetadataTimeout":
      if (state.kind !== "loading") return noChange(state);
      return failedTransition(state, state.cursorMs, "metadata_timeout");
    case "RecoveryClaimed":
      if (state.kind !== "failed" || state.recovery !== "available") return noChange(state);
      return { state: { ...state, recovery: "claimed" }, effects: [] };
    default:
      return exhaustive(event);
  }
}

function sameConfiguredSource(
  state: HtmlAudioSessionState,
  source: Extract<HtmlAudioSessionEvent, { type: "SourceConfigured" }>["source"],
): boolean {
  if (state.kind === "empty" || state.kind === "failed") return false;
  if (state.source.kind !== source.kind) return false;
  if (state.source.sourceFilename !== source.sourceFilename) return false;
  return state.source.kind !== "learner_recording"
    || (source.kind === "learner_recording" && state.source.attemptId === source.attemptId);
}
