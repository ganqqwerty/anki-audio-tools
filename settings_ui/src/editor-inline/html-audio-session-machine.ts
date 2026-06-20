import type { HtmlAudioFailureReason, HtmlAudioSessionEffect, HtmlAudioSessionEvent, HtmlAudioSessionState, HtmlAudioSessionTransition } from "./html-audio-session-types.js";
import { htmlAudioLoopStartMs, htmlAudioRequestCoversFullSource } from "./html-audio-session-request.js";

export type { HtmlAudioFailureReason, HtmlAudioSessionEffect, HtmlAudioSessionEvent, HtmlAudioSessionState, HtmlAudioSessionTransition, HtmlAudioSource, HtmlAudioStartRequest, PostEditAutoplayIntent } from "./html-audio-session-types.js";

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
            { type: "StartProgressFrame", cursorMs: state.pendingStart.cursorMs, endMs: state.pendingStart.endMs },
            { type: "PublishPlaybackState", status: "playing" },
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
        state.kind === "paused" ||
        state.kind === "repeat_waiting"
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
            { type: "ClearRepeatTimer" },
            { type: "ClearProgressFrame" },
            { type: "SeekAudio", cursorMs: event.request.cursorMs },
            { type: "PlayAudio" },
            { type: "StartProgressFrame", cursorMs: event.request.cursorMs, endMs: event.request.endMs },
            { type: "PublishPlaybackState", status: "playing", cursorMs: event.request.cursorMs },
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
          { type: "SeekAudio", cursorMs: event.request.cursorMs },
          { type: "PlayAudio" },
          { type: "StartProgressFrame", cursorMs: event.request.cursorMs, endMs: event.request.endMs },
          { type: "PublishPlaybackState", status: "playing" },
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
          { type: "PublishPlaybackState", status: "playing" },
          ...backendPlaybackEffects(state),
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
          { type: "StartProgressFrame", cursorMs: state.pausedAtMs, endMs: state.request.endMs },
          { type: "PublishPlaybackState", status: "playing", cursorMs: state.pausedAtMs },
        ],
      };
    }
    case "StopRequested":
      if (state.kind !== "starting" && state.kind !== "playing" && state.kind !== "paused" && state.kind !== "repeat_waiting") {
        return noChange(state);
      }
      return {
        state: readyFromActive(state, event.cursorMs),
        effects: [
          { type: "PauseAudio" },
          { type: "ClearProgressFrame" },
          { type: "ClearRepeatTimer" },
          { type: "PublishPlaybackState", status: "stopped", cursorMs: event.cursorMs },
        ],
      };
    case "BoundaryReached": {
      if (state.kind === "ready" && event.request) {
        const boundaryEvent: HtmlAudioSessionEvent = {
          cursorMs: event.cursorMs,
          restartAudio: true,
          type: "BoundaryReached",
        };
        if (event.repeatEnabled !== undefined) boundaryEvent.repeatEnabled = event.repeatEnabled;
        if (event.repeatPauseMs !== undefined) boundaryEvent.repeatPauseMs = event.repeatPauseMs;
        if (event.resetCursorMs !== undefined) boundaryEvent.resetCursorMs = event.resetCursorMs;
        return transitionHtmlAudioSession(
          {
            kind: "starting",
            ord: state.ord,
            source: state.source,
            request: event.request,
            durationMs: state.durationMs,
          },
          boundaryEvent,
        );
      }
      if (state.kind !== "starting" && state.kind !== "playing") return noChange(state);
      if (event.repeatEnabled ?? state.request.loop) {
        if ((event.repeatPauseMs ?? 0) <= 0) {
          return restartLoopTransition(state, event.restartAudio === true);
        }
        return {
          state: {
            kind: "repeat_waiting",
            ord: state.ord,
            source: state.source,
            request: state.request,
            durationMs: state.durationMs,
            resumeAtMs: htmlAudioLoopStartMs(state.request),
          },
          effects: [
            { type: "PauseAudio" },
            { type: "ClearProgressFrame" },
            { type: "StartRepeatTimer", pauseMs: event.repeatPauseMs ?? 0 },
            { type: "PublishRepeatWaitingState", cursorMs: htmlAudioLoopStartMs(state.request) },
          ],
        };
      }
      const resetCursorMs = event.resetCursorMs ?? htmlAudioLoopStartMs(state.request);
      return {
        state: readyFromActive(state, resetCursorMs),
        effects: [
          { type: "PauseAudio" },
          { type: "ClearProgressFrame" },
          { type: "ClearRepeatTimer" },
          { cursorMs: resetCursorMs, type: "CompletePlayback" },
        ],
      };
    }
    case "RepeatDelayElapsed":
      if (state.kind !== "repeat_waiting") return noChange(state);
      if (event.repeatEnabled === false) {
        const resetCursorMs = htmlAudioLoopStartMs(state.request);
        return {
          state: readyFromActive(state, resetCursorMs),
          effects: [
            { type: "ClearRepeatTimer" },
            { cursorMs: resetCursorMs, type: "CompletePlayback" },
          ],
        };
      }
      return restartLoopTransition(state, true);

    case "AudioError":
      if (state.kind === "empty" || state.kind === "failed") return noChange(state);
      return failedTransition(state, event.cursorMs, event.reason);
    case "RuntimeDisposed":
      if (state.kind === "empty") return noChange(state);
      return {
        state: initialHtmlAudioSessionState(state.ord),
        effects: [
          { type: "PauseAudio" },
          { type: "ClearAudioSource" },
          { type: "ClearProgressFrame" },
          { type: "ClearMetadataTimer" },
          { type: "ClearRepeatTimer" },
          { type: "PublishPlaybackState", status: "stopped" },
        ],
      };
    case "PostEditAutoplayRequested":
      if (
        state.kind !== "loading" &&
        state.kind !== "ready" &&
        state.kind !== "starting" &&
        state.kind !== "playing" &&
        state.kind !== "paused" &&
        state.kind !== "repeat_waiting" &&
        state.kind !== "post_edit_waiting"
      ) {
        return noChange(state);
      }
      if (event.intent.sourceFilename !== state.source.sourceFilename) {
        return noChange(state);
      }
      return {
        state: {
          kind: "post_edit_waiting",
          ord: state.ord,
          source: state.source,
          postEdit: event.intent,
          request: event.request,
          cursorMs: currentCursorMs(state),
          graphDurationMs: null,
          readyDispatched: false,
        },
        effects: [],
      };
    case "GraphRenderedForSource":
    case "PostEditReadyConfirmed":
      if (state.kind !== "post_edit_waiting") {
        return noChange(state);
      }
      if (event.sourceFilename !== state.postEdit.sourceFilename) {
        return noChange(state);
      }
      if (state.readyDispatched) {
        return {
          state: {
            ...state,
            graphDurationMs: event.durationMs,
          },
          effects: [],
        };
      }
      return {
        state: {
          kind: "ready",
          ord: state.ord,
          source: state.source,
          durationMs: event.durationMs,
          cursorMs: state.request.cursorMs,
        },
        effects: [
          { type: "ClearMetadataTimer" },
          {
            type: "DispatchPostEditReady",
            ord: state.postEdit.fieldOrd,
            generation: state.postEdit.generation,
            sourceFilename: state.postEdit.sourceFilename,
          },
        ],
      };
    case "SourceCleared":
      return {
        state: initialHtmlAudioSessionState(state.ord),
        effects: [
          { type: "PauseAudio" },
          { type: "ClearAudioSource" },
          { type: "ClearProgressFrame" },
          { type: "ClearMetadataTimer" },
          { type: "ClearRepeatTimer" },
          { type: "PublishPlaybackState", status: "stopped" },
        ],
      };
    case "MetadataTimeout":
      if (state.kind !== "loading") return noChange(state);
      return failedTransition(state, state.cursorMs, "metadata_timeout");
    default:
      return exhaustive(event);
  }
}

function failedTransition(
  state: Exclude<HtmlAudioSessionState, { kind: "empty" | "failed" }>,
  cursorMs: number,
  reason: HtmlAudioFailureReason,
): HtmlAudioSessionTransition {
  return {
    state: {
      kind: "failed",
      ord: state.ord,
      source: state.source,
      cursorMs,
      reason,
    },
    effects: [
      { type: "ClearProgressFrame" },
      { type: "PauseAudio" },
      { type: "PublishPlaybackState", status: "stopped", cursorMs },
      ...playbackFailureStatusEffects(state),
      {
        type: "LogPlaybackTelemetry",
        event: "playback.html_failed",
        data: { reason },
      },
    ],
  };
}

function readyFromActive(
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

function restartLoopTransition(
  state: Extract<HtmlAudioSessionState, { kind: "starting" | "playing" | "repeat_waiting" }>,
  restartAudio: boolean,
): HtmlAudioSessionTransition {
  const request = { ...state.request, cursorMs: htmlAudioLoopStartMs(state.request) };
  const resetEffects = htmlAudioRequestCoversFullSource(request, state.durationMs)
    ? [{ type: "ReloadAudioSource" } as const]
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
      { type: "StartProgressFrame", cursorMs: request.cursorMs, endMs: request.endMs },
      { type: "PublishPlaybackState", status: "playing", cursorMs: request.cursorMs },
    ],
  };
}

function backendPlaybackEffects(
  state: Extract<HtmlAudioSessionState, { kind: "starting" }>,
): HtmlAudioSessionEffect[] {
  return state.request.source === "learner_recording"
    ? []
    : [{ request: state.request, type: "QueueBackendPlayback" }];
}

function playbackFailureStatusEffects(
  state: Exclude<HtmlAudioSessionState, { kind: "empty" | "failed" }>,
): HtmlAudioSessionEffect[] {
  if ("request" in state && state.request.source === "post_edit") {
    return [{ statusKey: "editor.status.browser_audio_unavailable", type: "ShowPostEditPlaybackWarning" }];
  }
  return [{ statusKey: "editor.status.browser_audio_unavailable", type: "ShowPlaybackStatus" }];
}

function noChange(state: HtmlAudioSessionState): HtmlAudioSessionTransition {
  return { state, effects: [] };
}

function sourceReconfigurationEffects(state: HtmlAudioSessionState): HtmlAudioSessionEffect[] {
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

function currentCursorMs(state: Exclude<HtmlAudioSessionState, { kind: "empty" | "failed" }>): number {
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

function exhaustive(value: never): never {
  throw new Error(`Unhandled html audio session case: ${JSON.stringify(value)}`);
}
