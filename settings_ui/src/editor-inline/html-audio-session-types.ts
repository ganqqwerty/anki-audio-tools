import type { PlaybackRecoveryProposal } from "./playback-recovery-types.js";

export type HtmlAudioSource =
  | { kind: "source"; sourceFilename: string }
  | { kind: "learner_recording"; sourceFilename: string; startCursorMs: number; attemptId: number };

export function htmlAudioSourceBindingKey(source: HtmlAudioSource): string {
  return source.kind === "learner_recording"
    ? `${source.kind}\u0000${source.sourceFilename}\u0000${String(source.attemptId)}`
    : `${source.kind}\u0000${source.sourceFilename}`;
}

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
  source: "user" | "post_edit" | "learner_recording";
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
  | {
      kind: "ready";
      ord: number;
      source: HtmlAudioSource;
      durationMs: number;
      cursorMs: number;
      mediaExhausted?: true;
    }
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
      kind: "failed";
      ord: number;
      source: HtmlAudioSource | null;
      cursorMs: number;
      reason: HtmlAudioFailureReason;
      mediaErrorCode: number | null;
      mediaResponseStatus: number | null;
      recovery: "available" | "claimed" | "none";
    };

export function htmlAudioSessionPosition(state: HtmlAudioSessionState): number {
  if (state.kind === "paused") return state.pausedAtMs;
  if ("request" in state) return state.request.cursorMs;
  if ("cursorMs" in state) return state.cursorMs;
  return 0;
}

export type HtmlAudioSessionEvent =
  | { type: "SourceConfigured"; source: HtmlAudioSource; cursorMs: number; replace?: boolean }
  | { type: "SourceCleared" }
  | { type: "MetadataLoaded"; durationMs: number }
  | { type: "MetadataTimeout" }
  | { type: "StartRequested"; request: HtmlAudioStartRequest }
  | { type: "PlayResolved"; nowMs: number; sourceFilename: string }
  | { type: "PlayRejected"; reason: "audio_play_rejected"; sourceFilename: string }
  | { type: "SeekFailed"; reason: "audio_seek_failed"; cursorMs: number }
  | { type: "PauseRequested"; cursorMs: number }
  | { type: "ResumeRequested" }
  | { type: "StopRequested"; cursorMs: number }
  | {
      type: "BoundaryReached";
      cursorMs: number;
      resetCursorMs?: number;
    }
  | {
      type: "AudioError";
      reason: "audio_error";
      cursorMs: number;
      mediaErrorCode: number | null;
      mediaResponseStatus: number | null;
    }
  | { type: "RuntimeDisposed" }
  | { type: "RecoveryClaimed" };

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
  | { type: "PublishPlaybackState"; status: "stopped" | "playing" | "paused"; cursorMs?: number }
  | { type: "CompletePlayback"; cursorMs: number }
  | { type: "ReportPassCompleted"; request: HtmlAudioStartRequest }
  | {
      type: "ShowPlaybackStatus";
      kind?: "error" | "warning";
      preserveStableError?: boolean;
      statusCode?: string;
      statusKey: string;
      recovery?: PlaybackRecoveryProposal;
    }
  | {
      type: "ShowPostEditPlaybackWarning";
      statusKey: string;
      statusCode?: string;
      recovery?: PlaybackRecoveryProposal;
    }
  | { type: "LogPlaybackTelemetry"; event: string; data: Record<string, unknown> };

export interface HtmlAudioSessionTransition {
  state: HtmlAudioSessionState;
  effects: HtmlAudioSessionEffect[];
}
