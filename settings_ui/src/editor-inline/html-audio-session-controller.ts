import { clearPlaybackWarning } from "./control-status-renderer.js";
import {
  createHtmlAudioElementOperations,
  type HtmlAudioPortSnapshot,
} from "./html-audio-session-audio-element.js";
import {
  initialHtmlAudioSessionState,
  transitionHtmlAudioSession,
  type HtmlAudioFailureReason,
  type HtmlAudioSessionEvent,
  type HtmlAudioSessionState,
  type HtmlAudioStartRequest,
} from "./html-audio-session-machine.js";
import { createHtmlAudioPortEventHandlers } from "./html-audio-session-port-events.js";
import { createHtmlAudioSessionEffectExecutor } from "./html-audio-session-effect-executor.js";
import { HtmlAudioSessionDispatcher } from "./html-audio-session-dispatcher.js";
import {
  htmlAudioSessionEventSummary,
  htmlAudioSessionStateSummary,
} from "./html-audio-session-logging.js";
import { HtmlAudioSessionResources } from "./html-audio-session-resources.js";
import { HtmlAudioSessionReader } from "./html-audio-session-reader.js";
import { HtmlAudioSessionRecovery } from "./html-audio-session-recovery.js";
import {
  requireTransportAttemptIdentity,
  requireTransportFailureIdentity,
  requireTransportSourceIdentity,
} from "./html-audio-session-identities.js";
import {
  enforceTransportInvariants,
  type TransportInvariantRecovery,
} from "./html-audio-session-invariants.js";
import { logger } from "./logger.js";
import { htmlAudioSessionPosition, htmlAudioSourceBindingKey } from "./html-audio-session-types.js";
import {
  TransportIdentityRegistry,
  type TransportAttemptIdentity,
  type TransportFailureIdentity,
  type TransportSourceIdentity,
  validateTransportOwnership,
  validateTransportResources,
  validateTransportState,
  transportLifecycleIsActive,
  type TransportSnapshot,
} from "./transport/index.js";
import type { PlaybackRecoveryAction } from "./playback-recovery-types.js";

const sessionStates = new Map<number, HtmlAudioSessionState>();
const activeMediaPositions = new Map<number, number>();
let activeTransportOrd: number | null = null;
let passCompletedSink: ((ord: number, request: HtmlAudioStartRequest) => boolean) | null = null;
let transportFailureSink: ((fact: HtmlAudioTransportFailureFact) => void) | null = null;
let transportSnapshotSink: ((snapshot: TransportSnapshot) => void) | null = null;
let transportIdentities = new TransportIdentityRegistry();
const audioElementOperations = createHtmlAudioElementOperations(createHtmlAudioPortEventHandlers({
  acceptsAttempt: (ord, identity) => transportIdentities.acceptsAttempt(ord, identity),
  dispatchAttemptFact: dispatchHtmlAudioSessionAttemptFact,
  dispatchSourceFact: dispatchHtmlAudioSessionSourceFact,
  readAttemptIdentity: (ord) => transportIdentities.currentAttempt(ord),
  readState: readHtmlAudioSessionState,
}));
const sessionReader = new HtmlAudioSessionReader({
  audio: audioElementOperations,
  readActiveOrd: () => activeTransportOrd,
  readAttemptIdentity: (ord) => transportIdentities.currentAttempt(ord),
  readFailureIdentity: (ord) => transportIdentities.currentFailure(ord),
  readSession: readHtmlAudioSessionState,
  readSourceIdentity: (ord) => transportIdentities.currentSource(ord),
  readStoredPosition: (ord) => activeMediaPositions.get(ord),
});
const sessionRecovery = new HtmlAudioSessionRecovery({
  acceptsFailure: (ord, identity) => transportIdentities.acceptsFailure(ord, identity),
  claimFailure: (ord, identity) => transportIdentities.claimFailure(ord, identity),
  dispatchFailureFact: dispatchHtmlAudioSessionFailureFact,
  readState: readHtmlAudioSessionState,
});
const sessionResources = new HtmlAudioSessionResources({
  acceptsAttempt: (ord, identity) => transportIdentities.acceptsAttempt(ord, identity),
  dispatchAttemptFact: dispatchHtmlAudioSessionAttemptFact,
  dispatchSourceFact: dispatchHtmlAudioSessionSourceFact,
  readAttemptIdentity: (ord) => requireTransportAttemptIdentity(transportIdentities, ord),
  publishPosition: (ord, positionMs) => activeMediaPositions.set(ord, positionMs),
  readSourceIdentity: (ord) => requireTransportSourceIdentity(transportIdentities, ord),
  readState: readHtmlAudioSessionState,
});
const executeHtmlAudioSessionEffect = createHtmlAudioSessionEffectExecutor({
  audio: audioElementOperations,
  readAttemptIdentity: (ord) => requireTransportAttemptIdentity(transportIdentities, ord),
  readFailureIdentity: (ord) => requireTransportFailureIdentity(transportIdentities, ord),
  readRequest: requestForFieldUpdate,
  readSourceIdentity: (ord) => requireTransportSourceIdentity(transportIdentities, ord),
  readState: readHtmlAudioSessionState,
  reportPassCompleted: (ord, request) => passCompletedSink?.(ord, request) === true,
  resources: sessionResources,
});
const invariantRecovery: TransportInvariantRecovery = {
  clearAttempt: (ord) => transportIdentities.clearAttempt(ord),
  clearAudioSource: (ord) => audioElementOperations.clearAudioSource(ord),
  clearMetadataTimer: (ord) => sessionResources.clearMetadataTimer(ord),
  clearPosition: (ord) => activeMediaPositions.delete(ord),
  clearProgressFrame: (ord) => sessionResources.clearProgressFrame(ord),
  commitFailedState: (ord, state) => {
    sessionStates.set(ord, state);
    if (state.kind !== "failed") return;
    const failureIdentity = transportIdentities.currentFailure(ord)
      ?? transportIdentities.registerFailure(ord);
    if (failureIdentity) {
      transportFailureSink?.({ fieldOrd: ord, failureIdentity, reason: state.reason });
    }
  },
  pauseAudio: (ord) => audioElementOperations.pauseAudio(ord),
  publishSnapshot: (ord) => transportSnapshotSink?.(readHtmlAudioTransportSnapshot(ord)),
  releaseActiveOwner: (ord) => {
    if (activeTransportOrd === ord) activeTransportOrd = null;
  },
};

interface HtmlAudioTransportFailureFact {
  readonly failureIdentity: TransportFailureIdentity;
  readonly fieldOrd: number;
  readonly reason: HtmlAudioFailureReason;
}
const eventDispatcher = new HtmlAudioSessionDispatcher({
  identities: () => transportIdentities,
  process: processHtmlAudioSessionEvent,
});

export function initializeHtmlAudioTransportRuntime(): void {
  transportIdentities.dispose();
  transportIdentities = new TransportIdentityRegistry();
  activeMediaPositions.clear();
  activeTransportOrd = null;
}
export function mountHtmlAudioTransportField(ord: number): void {
  transportIdentities.mountField(ord);
}
export function remountHtmlAudioTransportField(ord: number): void {
  transportIdentities.remountField(ord);
}
export function unmountHtmlAudioTransportField(ord: number): void {
  clearHtmlAudioSession(ord);
  transportIdentities.unmountField(ord);
}

export function readHtmlAudioTransportSourceIdentity(ord: number): TransportSourceIdentity | null {
  return transportIdentities.currentSource(ord);
}
export function readHtmlAudioTransportAttemptIdentity(ord: number): TransportAttemptIdentity | null {
  return transportIdentities.currentAttempt(ord);
}
export function readHtmlAudioTransportFailureIdentity(ord: number): TransportFailureIdentity | null {
  return transportIdentities.currentFailure(ord);
}

export function readHtmlAudioTransportSnapshot(ord: number): TransportSnapshot {
  return sessionReader.snapshot(ord);
}

export function readActiveHtmlAudioTransportSnapshot(): TransportSnapshot | null {
  return sessionReader.activeSnapshot();
}
export function stopAndQuiesceHtmlAudioTransport(): number | null {
  const ord = activeTransportOrd;
  if (ord === null) return null;
  stopActiveTransportOwner();
  return ord;
}

export function readHtmlAudioTransportPosition(ord: number): number {
  return sessionReader.position(ord);
}

export function previewHtmlAudioTransportPosition(
  ord: number,
  cursorMs: number,
  durationMs: number,
): boolean {
  return sessionReader.previewPosition(ord, cursorMs, durationMs);
}

export function readHtmlAudioPortSnapshot(ord: number): HtmlAudioPortSnapshot {
  return sessionReader.portSnapshot(ord);
}

export function claimHtmlAudioPlaybackRecovery(action: PlaybackRecoveryAction): boolean {
  return sessionRecovery.claim(action);
}

export function setHtmlAudioTransportPassCompletedSink(
  sink: ((ord: number, request: HtmlAudioStartRequest) => boolean) | null,
): void {
  passCompletedSink = sink;
}

export function setHtmlAudioTransportFailureSink(
  sink: ((fact: HtmlAudioTransportFailureFact) => void) | null,
): void {
  transportFailureSink = sink;
}

export function setHtmlAudioTransportSnapshotSink(
  sink: ((snapshot: TransportSnapshot) => void) | null,
): void {
  transportSnapshotSink = sink;
}

export function readHtmlAudioSessionState(ord: number): HtmlAudioSessionState {
  return sessionStates.get(ord) ?? initialHtmlAudioSessionState(ord);
}

export function htmlAudioSessionSourceFilename(ord: number): string {
  const state = readHtmlAudioSessionState(ord);
  if (state.kind === "empty") return "";
  return state.source?.sourceFilename ?? "";
}

export function dispatchHtmlAudioSessionEvent(ord: number, event: HtmlAudioSessionEvent): void {
  eventDispatcher.event(ord, event);
}

export function dispatchHtmlAudioSessionSourceFact(
  ord: number,
  identity: TransportSourceIdentity,
  event: HtmlAudioSessionEvent,
): void {
  eventDispatcher.sourceFact(ord, identity, event);
}

export function dispatchHtmlAudioSessionAttemptFact(
  ord: number,
  identity: TransportAttemptIdentity,
  event: HtmlAudioSessionEvent,
): void {
  eventDispatcher.attemptFact(ord, identity, event);
}

export function dispatchHtmlAudioSessionFailureFact(
  ord: number,
  identity: TransportFailureIdentity,
  event: HtmlAudioSessionEvent,
): void {
  eventDispatcher.failureFact(ord, identity, event);
}

function processHtmlAudioSessionEvent(ord: number, event: HtmlAudioSessionEvent): void {
  if ((event.type === "StartRequested" || event.type === "ResumeRequested") && activeTransportOrd !== ord) {
    stopActiveTransportOwner();
  }
  if (event.type === "SourceConfigured" || event.type === "PlayResolved") {
    clearPlaybackWarning(ord);
  }
  const current = readHtmlAudioSessionState(ord);
  if (event.type === "SourceConfigured") {
    transportIdentities.bindSource(
      ord,
      htmlAudioSourceBindingKey(event.source),
      event.replace === true || current.kind === "failed",
    );
  }
  const transition = transitionHtmlAudioSession(current, event);
  if (!enforceTransportInvariants(
    ord, transition.state, validateTransportState(transition.state), invariantRecovery,
  )) {
    return;
  }
  sessionStates.set(ord, transition.state);
  if (!enforceTransportInvariants(
    ord, transition.state, validateTransportOwnership(sessionStates), invariantRecovery,
  )) {
    return;
  }
  activeMediaPositions.set(ord, htmlAudioSessionPosition(transition.state));
  if (transportLifecycleIsActive(transition.state)) {
    activeTransportOrd = ord;
  } else if (activeTransportOrd === ord) {
    activeTransportOrd = null;
  }
  let failureFact: HtmlAudioTransportFailureFact | null = null;
  if (transition.effects.some((effect) => effect.type === "PlayAudio")) {
    transportIdentities.beginAttempt(ord);
  } else if (transition.state.kind === "failed" && current.kind !== "failed") {
    const failureIdentity = transportIdentities.registerFailure(ord);
    if (failureIdentity) {
      failureFact = { fieldOrd: ord, failureIdentity, reason: transition.state.reason };
    }
  } else if (
    transition.state.kind === "empty"
    || transition.state.kind === "ready"
  ) {
    transportIdentities.clearAttempt(ord);
  }
  logger.debug("html_audio_session.transition", {
    effects: transition.effects.map((effect) => effect.type),
    event: htmlAudioSessionEventSummary(event),
    from: htmlAudioSessionStateSummary(current),
    ord,
    to: htmlAudioSessionStateSummary(transition.state),
  });
  eventDispatcher.executeEffects(ord, transition.effects, executeHtmlAudioSessionEffect);
  if (!enforceTransportInvariants(
    ord,
    transition.state,
    validateTransportResources(transition.state, sessionResources.snapshot(ord)),
    invariantRecovery,
  )) return;
  if (event.type === "SourceCleared") transportIdentities.clearSource(ord);
  if (event.type === "RuntimeDisposed") transportIdentities.unmountField(ord);
  if (failureFact) transportFailureSink?.(failureFact);
  transportSnapshotSink?.(readHtmlAudioTransportSnapshot(ord));
}

export function clearHtmlAudioSession(ord: number): void {
  audioElementOperations.pauseAudio(ord);
  audioElementOperations.clearAudioSource(ord);
  audioElementOperations.dispose(ord);
  sessionResources.clearProgressFrame(ord);
  sessionResources.clearMetadataTimer(ord);
  sessionStates.delete(ord);
  activeMediaPositions.delete(ord);
  if (activeTransportOrd === ord) activeTransportOrd = null;
  transportIdentities.clearSource(ord);
  eventDispatcher.clear(ord);
}

export function clearAllHtmlAudioSessions(): void {
  for (const ord of new Set([
    ...sessionStates.keys(),
    ...sessionResources.activeOrds(),
  ])) {
    clearHtmlAudioSession(ord);
  }
  transportIdentities.dispose();
  activeMediaPositions.clear();
  activeTransportOrd = null;
}

function requestForFieldUpdate(ord: number): HtmlAudioStartRequest | null {
  const state = readHtmlAudioSessionState(ord);
  return "request" in state ? state.request : null;
}

function stopActiveTransportOwner(): void {
  const ord = activeTransportOrd;
  if (ord === null) return;
  dispatchHtmlAudioSessionEvent(ord, {
    cursorMs: readHtmlAudioTransportPosition(ord),
    type: "StopRequested",
  });
}
