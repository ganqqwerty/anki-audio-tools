export type SourcePlaybackFailureReason =
  | "metadata_timeout"
  | "audio_play_rejected"
  | "audio_error"
  | "audio_seek_failed";

export interface SourcePlaybackRequest {
  ord: number;
  cursorMs: number;
  endMs: number;
  loop: boolean;
  regionMode: "full" | "selection";
  repeatPauseMs: number;
  source: "user" | "post_edit" | "chorusing";
}

export interface PendingSourceStart {
  request: SourcePlaybackRequest;
  source: SourcePlaybackRequest["source"];
}

export type SourcePlaybackState =
  | { kind: "unconfigured"; reason: "audio_element_missing" | "audio_src_missing"; cursorMs: number }
  | { kind: "loading_metadata"; cursorMs: number; pendingStart: PendingSourceStart | null; sourceFilename: string }
  | { kind: "ready"; cursorMs: number; durationMs: number; sourceFilename: string }
  | { kind: "starting"; request: SourcePlaybackRequest; durationMs: number; sourceFilename: string }
  | { kind: "playing"; request: SourcePlaybackRequest; durationMs: number; sourceFilename: string }
  | { kind: "paused"; request: SourcePlaybackRequest; pausedAtMs: number; durationMs: number; sourceFilename: string }
  | { kind: "repeat_waiting"; request: SourcePlaybackRequest; durationMs: number; resumeAtMs: number; sourceFilename: string }
  | { kind: "failed"; cursorMs: number; reason: SourcePlaybackFailureReason; sourceFilename: string | null };

export type SourcePlaybackEvent =
  | { type: "AudioElementMissing" }
  | { type: "SourceCleared" }
  | { type: "SourceConfigured"; sourceFilename: string; cursorMs: number }
  | { type: "MetadataLoaded"; durationMs: number }
  | { type: "MetadataTimeout" }
  | { type: "UserPlayRequested"; request: SourcePlaybackRequest }
  | { type: "PostEditAutoplayRequested"; request: SourcePlaybackRequest }
  | { type: "PauseRequested"; cursorMs: number }
  | { type: "ResumeRequested" }
  | { type: "StopRequested"; cursorMs: number }
  | { type: "SeekSucceeded"; cursorMs: number }
  | { type: "SeekFailed"; reason: "audio_seek_failed"; cursorMs: number }
  | { type: "PlayResolved" }
  | { type: "PlayRejected"; reason: "audio_play_rejected"; cursorMs: number }
  | { type: "AudioError"; reason: "audio_error"; cursorMs: number }
  | { type: "BoundaryReached"; cursorMs: number }
  | { type: "RepeatDelayElapsed" }
  | { type: "RuntimeDisposed" };

export type SourcePlaybackEffect =
  | { type: "ConfigureAudioSource"; sourceFilename: string }
  | { type: "ProbeAudioMetadata" }
  | { type: "StartMetadataTimer"; timeoutMs: 5000 }
  | { type: "ClearMetadataTimer" }
  | { type: "SeekAudio"; cursorMs: number }
  | { type: "PlayAudio" }
  | { type: "PauseAudio" }
  | { type: "StopAudio" }
  | { type: "StartRepeatTimer"; pauseMs: number }
  | { type: "ClearRepeatTimer" }
  | { type: "PublishPlaybackState" }
  | { type: "ShowPlaybackStatus"; statusKey: string; kind?: "info" | "warning" | "error" }
  | { type: "LogPlaybackTelemetry"; event: string; data: Record<string, unknown> };

export interface SourcePlaybackTransition {
  state: SourcePlaybackState;
  effects: SourcePlaybackEffect[];
}

export function initialSourcePlaybackState(cursorMs = 0): SourcePlaybackState {
  return { cursorMs, kind: "unconfigured", reason: "audio_src_missing" };
}

export function transitionSourcePlayback(
  state: SourcePlaybackState,
  event: SourcePlaybackEvent,
): SourcePlaybackTransition {
  switch (event.type) {
    case "AudioElementMissing":
      return {
        state: { cursorMs: cursorMsFor(state), kind: "unconfigured", reason: "audio_element_missing" },
        effects: [
          { type: "PublishPlaybackState" },
          telemetry("playback.audio_element_missing"),
        ],
      };
    case "SourceCleared":
      return {
        state: { cursorMs: cursorMsFor(state), kind: "unconfigured", reason: "audio_src_missing" },
        effects: [
          { type: "StopAudio" },
          { type: "ClearMetadataTimer" },
          { type: "ClearRepeatTimer" },
          { type: "PublishPlaybackState" },
        ],
      };
    case "SourceConfigured":
      return {
        state: {
          cursorMs: event.cursorMs,
          kind: "loading_metadata",
          pendingStart: null,
          sourceFilename: event.sourceFilename,
        },
        effects: [
          { sourceFilename: event.sourceFilename, type: "ConfigureAudioSource" },
          { type: "ProbeAudioMetadata" },
          { timeoutMs: 5000, type: "StartMetadataTimer" },
          { type: "PublishPlaybackState" },
        ],
      };
    case "UserPlayRequested":
      if (state.kind === "loading_metadata") {
        return deferStart(state, event.request, "user", "playback.start_deferred");
      }
      if (state.kind === "ready") return startFromReady(state, event.request);
      return noChange(state);
    case "PostEditAutoplayRequested":
      if (state.kind === "loading_metadata") {
        return deferStart(state, event.request, "post_edit", "playback.post_edit_deferred");
      }
      if (state.kind === "ready") return startFromReady(state, event.request);
      return noChange(state);
    case "MetadataLoaded":
      if (state.kind !== "loading_metadata") return noChange(state);
      if (state.pendingStart) {
        return startPlayback(
          state.pendingStart.request,
          event.durationMs,
          state.sourceFilename,
          [{ type: "ClearMetadataTimer" }],
        );
      }
      return {
        state: {
          cursorMs: state.cursorMs,
          durationMs: event.durationMs,
          kind: "ready",
          sourceFilename: state.sourceFilename,
        },
        effects: [
          { type: "ClearMetadataTimer" },
          { type: "PublishPlaybackState" },
        ],
      };
    case "MetadataTimeout":
      if (state.kind !== "loading_metadata") return noChange(state);
      return {
        state: fail(state.cursorMs, "metadata_timeout", state.sourceFilename),
        effects: [
          { type: "ClearMetadataTimer" },
          { type: "PublishPlaybackState" },
          status("editor.status.browser_audio_unavailable"),
          telemetry("playback.metadata_timeout"),
        ],
      };
    case "PlayResolved":
      if (state.kind !== "starting") return noChange(state);
      return {
        state: { ...state, kind: "playing" },
        effects: [
          { type: "PublishPlaybackState" },
          status("editor.playback.playing", "info"),
        ],
      };
    case "PlayRejected":
      if (state.kind !== "starting") return noChange(state);
      return {
        state: fail(event.cursorMs, event.reason, state.sourceFilename),
        effects: [
          { type: "StopAudio" },
          { type: "PublishPlaybackState" },
          status("editor.status.browser_audio_unavailable"),
          telemetry("playback.html_failed", { reason: event.reason }),
        ],
      };
    case "PauseRequested":
      if (state.kind !== "playing") return noChange(state);
      return {
        state: {
          durationMs: state.durationMs,
          kind: "paused",
          pausedAtMs: event.cursorMs,
          request: state.request,
          sourceFilename: state.sourceFilename,
        },
        effects: [
          { type: "PauseAudio" },
          { type: "PublishPlaybackState" },
          status("editor.playback.paused", "info"),
        ],
      };
    case "ResumeRequested":
      if (state.kind !== "paused") return noChange(state);
      return startPlayback(
        { ...state.request, cursorMs: state.pausedAtMs },
        state.durationMs,
        state.sourceFilename,
      );
    case "BoundaryReached":
      if (state.kind !== "playing") return noChange(state);
      if (!state.request.loop) {
        return {
          state: readyState(event.cursorMs, state.durationMs, state.sourceFilename),
          effects: [
            { type: "StopAudio" },
            { type: "PublishPlaybackState" },
          ],
        };
      }
      if (state.request.repeatPauseMs > 0) {
        return {
          state: {
            durationMs: state.durationMs,
            kind: "repeat_waiting",
            request: state.request,
            resumeAtMs: state.request.cursorMs,
            sourceFilename: state.sourceFilename,
          },
          effects: [
            { type: "StopAudio" },
            { pauseMs: state.request.repeatPauseMs, type: "StartRepeatTimer" },
            { type: "PublishPlaybackState" },
          ],
        };
      }
      return startPlayback(state.request, state.durationMs, state.sourceFilename);
    case "RepeatDelayElapsed":
      if (state.kind !== "repeat_waiting") return noChange(state);
      return startPlayback(state.request, state.durationMs, state.sourceFilename);
    case "StopRequested":
      if (!("durationMs" in state)) return noChange(state);
      return {
        state: readyState(event.cursorMs, state.durationMs, state.sourceFilename),
        effects: [
          { type: "StopAudio" },
          { type: "ClearRepeatTimer" },
          { type: "PublishPlaybackState" },
        ],
      };
    case "SeekSucceeded":
      if (state.kind === "ready") {
        return {
          state: { ...state, cursorMs: event.cursorMs },
          effects: [{ type: "PublishPlaybackState" }],
        };
      }
      return noChange(state);
    case "SeekFailed":
    case "AudioError":
      if (state.kind === "unconfigured") return noChange(state);
      return {
        state: fail(event.cursorMs, event.reason, sourceFilenameFor(state)),
        effects: [
          { type: "StopAudio" },
          { type: "ClearMetadataTimer" },
          { type: "ClearRepeatTimer" },
          { type: "PublishPlaybackState" },
          telemetry("playback.html_failed", { reason: event.reason }),
        ],
      };
    case "RuntimeDisposed":
      return {
        state: { cursorMs: cursorMsFor(state), kind: "unconfigured", reason: "audio_src_missing" },
        effects: [
          { type: "StopAudio" },
          { type: "ClearMetadataTimer" },
          { type: "ClearRepeatTimer" },
          { type: "PublishPlaybackState" },
        ],
      };
    default:
      return exhaustive(event);
  }
}

function deferStart(
  state: Extract<SourcePlaybackState, { kind: "loading_metadata" }>,
  request: SourcePlaybackRequest,
  source: SourcePlaybackRequest["source"],
  event: string,
): SourcePlaybackTransition {
  return {
    state: {
      ...state,
      cursorMs: request.cursorMs,
      pendingStart: { request, source },
    },
    effects: [
      { type: "PublishPlaybackState" },
      telemetry(event, { source }),
    ],
  };
}

function startFromReady(
  state: Extract<SourcePlaybackState, { kind: "ready" }>,
  request: SourcePlaybackRequest,
): SourcePlaybackTransition {
  return startPlayback(request, state.durationMs, state.sourceFilename);
}

function startPlayback(
  request: SourcePlaybackRequest,
  durationMs: number,
  sourceFilename: string,
  prefixEffects: SourcePlaybackEffect[] = [],
): SourcePlaybackTransition {
  return {
    state: {
      durationMs,
      kind: "starting",
      request,
      sourceFilename,
    },
    effects: [
      ...prefixEffects,
      { cursorMs: request.cursorMs, type: "SeekAudio" },
      { type: "PlayAudio" },
      { type: "PublishPlaybackState" },
    ],
  };
}

function readyState(cursorMs: number, durationMs: number, sourceFilename: string): SourcePlaybackState {
  return {
    cursorMs,
    durationMs,
    kind: "ready",
    sourceFilename,
  };
}

function fail(
  cursorMs: number,
  reason: SourcePlaybackFailureReason,
  sourceFilename: string | null,
): SourcePlaybackState {
  return {
    cursorMs,
    kind: "failed",
    reason,
    sourceFilename,
  };
}

function cursorMsFor(state: SourcePlaybackState): number {
  switch (state.kind) {
    case "unconfigured":
    case "loading_metadata":
    case "ready":
    case "failed":
      return state.cursorMs;
    case "paused":
      return state.pausedAtMs;
    case "repeat_waiting":
    case "starting":
    case "playing":
      return state.request.cursorMs;
    default:
      return exhaustive(state);
  }
}

function sourceFilenameFor(state: Exclude<SourcePlaybackState, { kind: "unconfigured" }>): string | null {
  return state.sourceFilename;
}

function status(
  statusKey: string,
  kind: "info" | "warning" | "error" = "warning",
): SourcePlaybackEffect {
  return { kind, statusKey, type: "ShowPlaybackStatus" };
}

function telemetry(event: string, data: Record<string, unknown> = {}): SourcePlaybackEffect {
  return { data, event, type: "LogPlaybackTelemetry" };
}

function noChange(state: SourcePlaybackState): SourcePlaybackTransition {
  return { effects: [], state };
}

function exhaustive(value: never): never {
  throw new Error(`Unhandled source playback state/event: ${JSON.stringify(value)}`);
}
