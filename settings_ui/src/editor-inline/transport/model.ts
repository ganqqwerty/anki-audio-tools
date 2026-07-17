import type { HtmlAudioSessionState } from "../html-audio-session-types.js";
import type {
  TransportAttemptIdentity,
  TransportFailureIdentity,
  TransportSourceIdentity,
} from "./identity.js";

export interface TransportSnapshot {
  readonly active: boolean;
  readonly activeMediaPositionMs: number;
  readonly attemptIdentity: TransportAttemptIdentity | null;
  readonly failureIdentity: TransportFailureIdentity | null;
  readonly fieldOrd: number;
  readonly session: HtmlAudioSessionState;
  readonly sourceIdentity: TransportSourceIdentity | null;
}

export function transportLifecycleIsActive(state: HtmlAudioSessionState): boolean {
  return state.kind === "starting"
    || state.kind === "playing"
    || state.kind === "paused";
}
