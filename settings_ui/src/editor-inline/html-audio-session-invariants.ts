import type { HtmlAudioSessionState } from "./html-audio-session-machine.js";
import { logger } from "./logger.js";
import type { TransportViolation } from "./transport/index.js";

export interface TransportInvariantRecovery {
  clearAttempt: (ord: number) => void;
  clearAudioSource: (ord: number) => void;
  clearMetadataTimer: (ord: number) => void;
  clearPosition: (ord: number) => void;
  clearProgressFrame: (ord: number) => void;
  commitFailedState: (ord: number, state: HtmlAudioSessionState) => void;
  pauseAudio: (ord: number) => void;
  publishSnapshot: (ord: number) => void;
  releaseActiveOwner: (ord: number) => void;
}

export function enforceTransportInvariants(
  ord: number,
  candidate: HtmlAudioSessionState,
  violations: readonly TransportViolation[],
  recovery: TransportInvariantRecovery,
): boolean {
  if (violations.length === 0) return true;
  logger.error("transport.invariant_failed", {
    invariants: violations.map((violation) => violation.invariantId),
    messages: violations.map((violation) => violation.message),
    ord,
  });
  recovery.pauseAudio(ord);
  recovery.clearAudioSource(ord);
  recovery.clearProgressFrame(ord);
  recovery.clearMetadataTimer(ord);
  recovery.clearPosition(ord);
  recovery.releaseActiveOwner(ord);
  recovery.clearAttempt(ord);
  recovery.commitFailedState(ord, {
    cursorMs: "cursorMs" in candidate ? candidate.cursorMs : candidate.request.cursorMs,
    kind: "failed",
    mediaErrorCode: null,
    mediaResponseStatus: null,
    ord,
    reason: "audio_error",
    recovery: "none",
    source: "source" in candidate ? candidate.source : null,
  });
  recovery.publishSnapshot(ord);
  const runtime = globalThis as typeof globalThis & {
    process?: { env?: { NODE_ENV?: string } };
  };
  if (runtime.process?.env?.NODE_ENV === "test") {
    throw new Error(violations.map((item) => `${item.invariantId}: ${item.message}`).join("; "));
  }
  return false;
}
