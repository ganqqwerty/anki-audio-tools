import type { HtmlAudioSessionEvent } from "../html-audio-session-types.js";

export type TransportIdentityScope = "runtime" | "source" | "attempt";

export const TRANSPORT_EVENT_IDENTITY = {
  AudioError: "source",
  BoundaryReached: "attempt",
  MetadataLoaded: "source",
  MetadataTimeout: "source",
  PauseRequested: "runtime",
  PlayRejected: "attempt",
  PlayResolved: "attempt",
  RecoveryClaimed: "source",
  ResumeRequested: "runtime",
  RuntimeDisposed: "runtime",
  SeekFailed: "attempt",
  SourceCleared: "runtime",
  SourceConfigured: "runtime",
  StartRequested: "runtime",
  StopRequested: "runtime",
} satisfies Record<HtmlAudioSessionEvent["type"], TransportIdentityScope>;

export function transportIdentityScopeFor(event: HtmlAudioSessionEvent): TransportIdentityScope {
  return TRANSPORT_EVENT_IDENTITY[event.type];
}

/** Returns whether a synchronously emitted event invalidates remaining effects. */
export function eventInterruptsEffectBatch(event: HtmlAudioSessionEvent): boolean {
  return event.type === "AudioError"
    || event.type === "PauseRequested"
    || event.type === "RuntimeDisposed"
    || event.type === "SeekFailed"
    || event.type === "SourceCleared"
    || event.type === "SourceConfigured"
    || event.type === "StartRequested"
    || event.type === "StopRequested";
}
