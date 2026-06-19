export type LearnerRecordingPublicationStatus =
  | "idle"
  | "countdown"
  | "recording"
  | "stopping"
  | "analyzing"
  | "ready"
  | "failed";

export type LearnerRecordingPlaybackState =
  | { kind: "unavailable"; reason: "not_ready" | "media_missing" }
  | { kind: "ready"; mediaFilename: string; generation: number; durationMs: number; startCursorMs: number; cursorMs: number }
  | { kind: "starting"; mediaFilename: string; generation: number; durationMs: number; startCursorMs: number; cursorMs: number }
  | { kind: "playing"; mediaFilename: string; generation: number; durationMs: number; startCursorMs: number; startedAtMs: number }
  | { kind: "paused"; mediaFilename: string; generation: number; durationMs: number; startCursorMs: number; cursorMs: number }
  | { kind: "failed"; mediaFilename: string | null; generation: number | null; reason: "audio_play_rejected" | "audio_error" | "media_missing" };

export type LearnerRecordingPlaybackEvent =
  | {
      type: "RecordingStatePublished";
      status: LearnerRecordingPublicationStatus;
      mediaFilename?: string | null;
      generation?: number | null;
      recordingDurationMs?: number | null;
      targetDurationMs?: number | null;
      startCursorMs?: number | null;
    }
  | { type: "PlayButtonClicked" }
  | { type: "PlayResolved"; nowMs: number }
  | { type: "PlayRejected"; reason: "audio_play_rejected" }
  | { type: "PauseRequested"; cursorMs: number }
  | { type: "ResumeRequested" }
  | { type: "AudioEnded" }
  | { type: "AudioError"; reason: "audio_error" }
  | { type: "StopRequested" }
  | { type: "RuntimeDisposed" };

export type LearnerRecordingPlaybackEffect =
  | { type: "ConfigureLearnerAudioSource"; mediaFilename: string }
  | { type: "SeekLearnerAudio"; cursorMs: number }
  | { type: "PlayLearnerAudio" }
  | { type: "PauseLearnerAudio" }
  | { type: "StopLearnerAudio" }
  | { type: "StartLearnerProgressFrame" }
  | { type: "ClearLearnerProgressFrame" }
  | { type: "PublishLearnerPlaybackState"; status: "stopped" | "playing" | "paused"; cursorMs?: number }
  | { type: "RenderLearnerPlaybackCursor"; cursorMs: number }
  | { type: "ShowPlaybackStatus"; statusKey: string; kind?: "info" | "warning" | "error" }
  | { type: "LogPlaybackTelemetry"; event: string; data: Record<string, unknown> };

export interface LearnerRecordingPlaybackTransition {
  state: LearnerRecordingPlaybackState;
  effects: LearnerRecordingPlaybackEffect[];
}

export function initialLearnerRecordingPlaybackState(): LearnerRecordingPlaybackState {
  return { kind: "unavailable", reason: "not_ready" };
}

export function transitionLearnerRecordingPlayback(
  state: LearnerRecordingPlaybackState,
  event: LearnerRecordingPlaybackEvent,
): LearnerRecordingPlaybackTransition {
  switch (event.type) {
    case "RecordingStatePublished":
      return recordingStatePublished(event);
    case "PlayButtonClicked":
      return playButtonClicked(state);
    case "PlayResolved":
      if (state.kind !== "starting") return noChange(state);
      return {
        state: {
          durationMs: state.durationMs,
          generation: state.generation,
          kind: "playing",
          mediaFilename: state.mediaFilename,
          startedAtMs: event.nowMs,
          startCursorMs: state.startCursorMs,
        },
        effects: [
          publish("playing"),
          { type: "StartLearnerProgressFrame" },
        ],
      };
    case "PlayRejected":
      if (state.kind !== "starting") return noChange(state);
      return {
        state: failed(state, event.reason),
        effects: [
          { type: "StopLearnerAudio" },
          { type: "ClearLearnerProgressFrame" },
          publish("stopped"),
          status("editor.status.browser_audio_unavailable"),
          telemetry("recording.playback.html_failed", { reason: event.reason }),
        ],
      };
    case "PauseRequested":
      if (state.kind !== "playing") return noChange(state);
      return pausePlaying(state, event.cursorMs);
    case "ResumeRequested":
      if (state.kind !== "paused") return noChange(state);
      return startFromPaused(state);
    case "AudioEnded":
      if (state.kind !== "playing") return noChange(state);
      return {
        state: readyState(state, 0),
        effects: [
          { type: "ClearLearnerProgressFrame" },
          publish("stopped", 0),
          { cursorMs: state.startCursorMs, type: "RenderLearnerPlaybackCursor" },
        ],
      };
    case "AudioError":
      if (state.kind === "unavailable") return noChange(state);
      return {
        state: failed(state, event.reason),
        effects: [
          { type: "StopLearnerAudio" },
          { type: "ClearLearnerProgressFrame" },
          publish("stopped"),
          status("editor.status.browser_audio_unavailable"),
          telemetry("recording.playback.html_failed", { reason: event.reason }),
        ],
      };
    case "StopRequested":
      if (!isConfigured(state)) return noChange(state);
      return {
        state: readyState(state, 0),
        effects: [
          { type: "StopLearnerAudio" },
          { type: "ClearLearnerProgressFrame" },
          publish("stopped", 0),
        ],
      };
    case "RuntimeDisposed":
      return {
        state: { kind: "unavailable", reason: "media_missing" },
        effects: [
          { type: "StopLearnerAudio" },
          { type: "ClearLearnerProgressFrame" },
          publish("stopped"),
        ],
      };
    default:
      return exhaustive(event);
  }
}

function recordingStatePublished(
  event: Extract<LearnerRecordingPlaybackEvent, { type: "RecordingStatePublished" }>,
): LearnerRecordingPlaybackTransition {
  const mediaFilename = (event.mediaFilename ?? "").trim();
  const generation = finiteNumberOrNull(event.generation);
  if (event.status !== "ready" || mediaFilename.length === 0 || generation === null) {
    return {
      state: {
        kind: "unavailable",
        reason: event.status === "ready" ? "media_missing" : "not_ready",
      },
      effects: [
        { type: "StopLearnerAudio" },
        { type: "ClearLearnerProgressFrame" },
        publish("stopped"),
      ],
    };
  }
  const durationMs = Math.max(0, Math.round(
    finiteNumberOrNull(event.recordingDurationMs)
      ?? finiteNumberOrNull(event.targetDurationMs)
      ?? 0,
  ));
  const state: LearnerRecordingPlaybackState = {
    cursorMs: 0,
    durationMs,
    generation,
    kind: "ready",
    mediaFilename,
    startCursorMs: Math.max(0, Math.round(finiteNumberOrNull(event.startCursorMs) ?? 0)),
  };
  return {
    state,
    effects: [
      { type: "StopLearnerAudio" },
      { type: "ClearLearnerProgressFrame" },
      { mediaFilename, type: "ConfigureLearnerAudioSource" },
      publish("stopped"),
    ],
  };
}

function playButtonClicked(state: LearnerRecordingPlaybackState): LearnerRecordingPlaybackTransition {
  switch (state.kind) {
    case "unavailable":
      return {
        state,
        effects: [
          status("editor.status.referenced_audio_missing"),
          telemetry("recording.playback.ignored_missing"),
        ],
      };
    case "ready":
      return startReady(state);
    case "playing":
      return pausePlaying(state, 0);
    case "paused":
      return startFromPaused(state);
    case "failed":
    case "starting":
      return noChange(state);
    default:
      return exhaustive(state);
  }
}

function startReady(
  state: Extract<LearnerRecordingPlaybackState, { kind: "ready" }>,
): LearnerRecordingPlaybackTransition {
  return {
    state: {
      cursorMs: state.cursorMs,
      durationMs: state.durationMs,
      generation: state.generation,
      kind: "starting",
      mediaFilename: state.mediaFilename,
      startCursorMs: state.startCursorMs,
    },
    effects: [
      { cursorMs: state.cursorMs, type: "SeekLearnerAudio" },
      { type: "PlayLearnerAudio" },
      publish("playing", state.cursorMs),
    ],
  };
}

function startFromPaused(
  state: Extract<LearnerRecordingPlaybackState, { kind: "paused" }>,
): LearnerRecordingPlaybackTransition {
  return {
    state: {
      cursorMs: state.cursorMs,
      durationMs: state.durationMs,
      generation: state.generation,
      kind: "starting",
      mediaFilename: state.mediaFilename,
      startCursorMs: state.startCursorMs,
    },
    effects: [
      { cursorMs: state.cursorMs, type: "SeekLearnerAudio" },
      { type: "PlayLearnerAudio" },
      publish("playing", state.cursorMs),
    ],
  };
}

function pausePlaying(
  state: Extract<LearnerRecordingPlaybackState, { kind: "playing" }>,
  cursorMs: number,
): LearnerRecordingPlaybackTransition {
  const clampedCursorMs = clampMs(cursorMs, state.durationMs);
  return {
    state: {
      cursorMs: clampedCursorMs,
      durationMs: state.durationMs,
      generation: state.generation,
      kind: "paused",
      mediaFilename: state.mediaFilename,
      startCursorMs: state.startCursorMs,
    },
    effects: [
      { type: "PauseLearnerAudio" },
      { type: "ClearLearnerProgressFrame" },
      publish("paused", clampedCursorMs),
    ],
  };
}

function readyState(
  state: Extract<LearnerRecordingPlaybackState, { kind: "ready" | "starting" | "playing" | "paused" }>,
  cursorMs: number,
): LearnerRecordingPlaybackState {
  return {
    cursorMs: clampMs(cursorMs, state.durationMs),
    durationMs: state.durationMs,
    generation: state.generation,
    kind: "ready",
    mediaFilename: state.mediaFilename,
    startCursorMs: state.startCursorMs,
  };
}

function failed(
  state: Exclude<LearnerRecordingPlaybackState, { kind: "unavailable" }>,
  reason: "audio_play_rejected" | "audio_error",
): LearnerRecordingPlaybackState {
  return {
    generation: "generation" in state ? state.generation : null,
    kind: "failed",
    mediaFilename: "mediaFilename" in state ? state.mediaFilename : null,
    reason,
  };
}

function isConfigured(
  state: LearnerRecordingPlaybackState,
): state is Extract<LearnerRecordingPlaybackState, { kind: "ready" | "starting" | "playing" | "paused" }> {
  return state.kind === "ready" || state.kind === "starting" || state.kind === "playing" || state.kind === "paused";
}

function publish(
  status: "stopped" | "playing" | "paused",
  cursorMs?: number,
): LearnerRecordingPlaybackEffect {
  return cursorMs === undefined
    ? { status, type: "PublishLearnerPlaybackState" }
    : { cursorMs, status, type: "PublishLearnerPlaybackState" };
}

function status(
  statusKey: string,
  kind: "info" | "warning" | "error" = "warning",
): LearnerRecordingPlaybackEffect {
  return { kind, statusKey, type: "ShowPlaybackStatus" };
}

function telemetry(event: string, data: Record<string, unknown> = {}): LearnerRecordingPlaybackEffect {
  return { data, event, type: "LogPlaybackTelemetry" };
}

function finiteNumberOrNull(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function clampMs(value: number, durationMs: number): number {
  return Math.max(0, Math.min(Math.round(Number(value) || 0), Math.max(0, durationMs)));
}

function noChange(state: LearnerRecordingPlaybackState): LearnerRecordingPlaybackTransition {
  return { effects: [], state };
}

function exhaustive(value: never): never {
  throw new Error(`Unhandled learner recording playback state/event: ${JSON.stringify(value)}`);
}
