import {
  currentCursorMs,
  exhaustive,
  failedTransition,
  noChange,
  readyFromActive,
  restartLoopTransition,
  sourceReconfigurationEffects,
} from "./html-audio-session-machine-helpers.js";
import { htmlAudioLoopStartMs } from "./html-audio-session-request.js";
import type { HtmlAudioSessionEvent, HtmlAudioSessionState, HtmlAudioSessionTransition } from "./html-audio-session-types.js";

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
          { type: "PauseAudio" }, { type: "ClearProgressFrame" }, { type: "ClearRepeatTimer" },
          { type: "ClearMetadataTimer" }, { type: "PublishPlaybackState", status: "stopped", cursorMs: event.cursorMs },
        ] };
      }
      if (state.kind === "ready") {
        return { state, effects: [
          { type: "PauseAudio" }, { type: "ClearProgressFrame" }, { type: "ClearRepeatTimer" },
          { type: "PublishPlaybackState", status: "stopped", cursorMs: event.cursorMs },
        ] };
      }
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
      if (isDuplicateActivePostEditAutoplay(state, event.request)) {
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

function isDuplicateActivePostEditAutoplay(
  state: Extract<HtmlAudioSessionState, { kind: "loading" | "ready" | "starting" | "playing" | "paused" | "repeat_waiting" | "post_edit_waiting" }>,
  request: Extract<HtmlAudioSessionEvent, { type: "PostEditAutoplayRequested" }>["request"],
): boolean {
  if (
    state.kind !== "starting" &&
    state.kind !== "playing" &&
    state.kind !== "paused" &&
    state.kind !== "repeat_waiting"
  ) {
    return false;
  }
  return state.request.source === "post_edit"
    && request.source === "post_edit"
    && state.request.cursorMs === request.cursorMs
    && state.request.endMs === request.endMs
    && state.request.loop === request.loop
    && state.request.ord === request.ord
    && state.request.regionMode === request.regionMode
    && state.request.resetCursorMs === request.resetCursorMs;
}
