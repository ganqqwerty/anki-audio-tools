export type HtmlAudioSource =
  | { kind: "source"; sourceFilename: string }
  | { kind: "learner_recording"; sourceFilename: string; startCursorMs: number; generation: number };

export type HtmlAudioFailureReason =
  | "audio_error"
  | "audio_play_rejected"
  | "metadata_timeout"
  | "audio_seek_failed";

export interface HtmlAudioStartRequest {
  ord: number;
  cursorMs: number;
  endMs: number;
  loop: boolean;
  regionMode: "full" | "selection";
  resetCursorMs?: number;
  source: "user" | "post_edit" | "chorusing" | "learner_recording";
}

export interface PostEditAutoplayIntent {
  fieldOrd: number;
  generation: number;
  sourceFilename: string;
  sourceKind: "generated_edit" | "existing_media";
  requireGraphRedraw: boolean;
  expectedDurationMs?: number;
}

export type HtmlAudioSessionState =
  | { kind: "empty"; ord: number; cursorMs: number }
  | {
      kind: "loading";
      ord: number;
      source: HtmlAudioSource;
      cursorMs: number;
      pendingStart: HtmlAudioStartRequest | null;
    }
  | { kind: "ready"; ord: number; source: HtmlAudioSource; durationMs: number; cursorMs: number }
  | { kind: "starting"; ord: number; source: HtmlAudioSource; request: HtmlAudioStartRequest; durationMs: number }
  | {
      kind: "playing";
      ord: number;
      source: HtmlAudioSource;
      request: HtmlAudioStartRequest;
      durationMs: number;
      startedAtMs: number;
    }
  | {
      kind: "paused";
      ord: number;
      source: HtmlAudioSource;
      request: HtmlAudioStartRequest;
      durationMs: number;
      pausedAtMs: number;
    }
  | {
      kind: "repeat_waiting";
      ord: number;
      source: HtmlAudioSource;
      request: HtmlAudioStartRequest;
      durationMs: number;
      resumeAtMs: number;
    }
  | {
      kind: "post_edit_waiting";
      ord: number;
      source: HtmlAudioSource;
      postEdit: PostEditAutoplayIntent;
      request: HtmlAudioStartRequest;
      cursorMs: number;
      graphDurationMs: number | null;
      readyDispatched: boolean;
    }
  | { kind: "failed"; ord: number; source: HtmlAudioSource | null; cursorMs: number; reason: HtmlAudioFailureReason };

export type HtmlAudioSessionEvent =
  | { type: "SourceConfigured"; source: HtmlAudioSource; cursorMs: number }
  | { type: "SourceCleared" }
  | { type: "MetadataLoaded"; durationMs: number }
  | { type: "MetadataTimeout" }
  | { type: "StartRequested"; request: HtmlAudioStartRequest }
  | { type: "PostEditAutoplayRequested"; intent: PostEditAutoplayIntent; request: HtmlAudioStartRequest }
  | { type: "GraphRenderedForSource"; sourceFilename: string; durationMs: number }
  | { type: "PostEditReadyConfirmed"; sourceFilename: string; durationMs: number }
  | { type: "PlayResolved"; nowMs: number; sourceFilename: string }
  | { type: "PlayRejected"; reason: "audio_play_rejected"; sourceFilename: string }
  | { type: "SeekFailed"; reason: "audio_seek_failed"; cursorMs: number }
  | { type: "PauseRequested"; cursorMs: number }
  | { type: "ResumeRequested" }
  | { type: "StopRequested"; cursorMs: number }
  | {
      type: "BoundaryReached";
      cursorMs: number;
      repeatPauseMs?: number;
      request?: HtmlAudioStartRequest;
      resetCursorMs?: number;
      restartAudio?: boolean;
      repeatEnabled?: boolean;
    }
  | { type: "RepeatDelayElapsed"; repeatEnabled?: boolean }
  | { type: "AudioError"; reason: "audio_error"; cursorMs: number }
  | { type: "RuntimeDisposed" };

export type HtmlAudioSessionEffect =
  | { type: "ConfigureAudioSource"; sourceFilename: string }
  | { type: "ClearAudioSource" }
  | { type: "SeekAudio"; cursorMs: number }
  | { type: "ReloadAudioSource" }
  | { type: "PlayAudio" }
  | { type: "PauseAudio" }
  | { type: "StartProgressFrame"; cursorMs: number; endMs: number }
  | { type: "ClearProgressFrame" }
  | { type: "StartMetadataTimer"; timeoutMs: number }
  | { type: "ClearMetadataTimer" }
  | { type: "StartRepeatTimer"; pauseMs: number }
  | { type: "ClearRepeatTimer" }
  | { type: "RequestGraphForSource"; ord: number; sourceFilename: string }
  | { type: "DispatchPostEditReady"; ord: number; generation: number; sourceFilename: string }
  | { type: "QueueBackendPlayback"; request: HtmlAudioStartRequest }
  | { type: "PublishPlaybackState"; status: "stopped" | "playing" | "paused"; cursorMs?: number }
  | { type: "PublishRepeatWaitingState"; cursorMs: number }
  | { type: "CompletePlayback"; cursorMs: number }
  | { type: "ShowPlaybackStatus"; statusKey: string }
  | { type: "ShowPostEditPlaybackWarning"; statusKey: string }
  | { type: "LogPlaybackTelemetry"; event: string; data: Record<string, unknown> };

export interface HtmlAudioSessionTransition {
  state: HtmlAudioSessionState;
  effects: HtmlAudioSessionEffect[];
}
