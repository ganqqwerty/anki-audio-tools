import type {
  HtmlAudioElementOperations,
  HtmlAudioPortSnapshot,
} from "./html-audio-session-audio-element.js";
import type { HtmlAudioSessionState } from "./html-audio-session-types.js";
import {
  transportLifecycleIsActive,
  type TransportAttemptIdentity,
  type TransportFailureIdentity,
  type TransportSnapshot,
  type TransportSourceIdentity,
} from "./transport/index.js";

interface HtmlAudioSessionReaderDependencies {
  readonly audio: HtmlAudioElementOperations;
  readActiveOrd: () => number | null;
  readAttemptIdentity: (ord: number) => TransportAttemptIdentity | null;
  readFailureIdentity: (ord: number) => TransportFailureIdentity | null;
  readSession: (ord: number) => HtmlAudioSessionState;
  readSourceIdentity: (ord: number) => TransportSourceIdentity | null;
  readStoredPosition: (ord: number) => number | undefined;
}

/** Read-only transport facade kept separate from transition/effect ownership. */
export class HtmlAudioSessionReader {
  constructor(private readonly dependencies: HtmlAudioSessionReaderDependencies) {}

  snapshot(ord: number): TransportSnapshot {
    const session = this.dependencies.readSession(ord);
    return {
      active: this.dependencies.readActiveOrd() === ord && transportLifecycleIsActive(session),
      activeMediaPositionMs: this.position(ord),
      attemptIdentity: this.dependencies.readAttemptIdentity(ord),
      failureIdentity: this.dependencies.readFailureIdentity(ord),
      fieldOrd: ord,
      session,
      sourceIdentity: this.dependencies.readSourceIdentity(ord),
    };
  }

  activeSnapshot(): TransportSnapshot | null {
    const ord = this.dependencies.readActiveOrd();
    return ord === null ? null : this.snapshot(ord);
  }

  position(ord: number): number {
    const state = this.dependencies.readSession(ord);
    const stored = this.dependencies.readStoredPosition(ord);
    if (state.kind === "starting" || state.kind === "playing") {
      const port = this.dependencies.audio.readSnapshot(ord);
      if (port.present) return Math.max(port.currentTimeMs, stored ?? 0);
    }
    if (stored !== undefined) return stored;
    if (state.kind === "paused") return state.pausedAtMs;
    if ("cursorMs" in state) return state.cursorMs;
    if ("request" in state) return state.request.cursorMs;
    return 0;
  }

  previewPosition(ord: number, cursorMs: number, durationMs: number): boolean {
    return this.dependencies.audio.previewPosition(ord, cursorMs, durationMs);
  }

  portSnapshot(ord: number): HtmlAudioPortSnapshot {
    return this.dependencies.audio.readSnapshot(ord);
  }
}
