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
      ...(!restartAudio ? [{ type: "StartProgressFrame", cursorMs: request.cursorMs, endMs: request.endMs } as const] : []),
      { type: "PublishPlaybackState", status: "playing", cursorMs: request.cursorMs },
    ],
  };
}

export function backendPlaybackEffects(
  state: Extract<HtmlAudioSessionState, { kind: "starting" }>,
): HtmlAudioSessionEffect[] {
  return state.request.source === "learner_recording"
    ? []
    : [{ request: state.request, type: "QueueBackendPlayback" }];
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
): HtmlAudioSessionEffect[] {
  if ("request" in state && state.request.source === "post_edit") {
    return [{ statusKey: "editor.status.browser_audio_unavailable", type: "ShowPostEditPlaybackWarning" }];
  }
  return [{ statusKey: "editor.status.browser_audio_unavailable", type: "ShowPlaybackStatus" }];
}

export function exhaustive(value: never): never {
  throw new Error(`Unhandled html audio session case: ${JSON.stringify(value)}`);
}
