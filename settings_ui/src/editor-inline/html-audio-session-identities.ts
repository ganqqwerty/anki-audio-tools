import type { HtmlAudioSessionEvent } from "./html-audio-session-machine.js";
import {
  transportIdentityScopeFor,
  type TransportAttemptIdentity,
  type TransportFailureIdentity,
  TransportIdentityRegistry,
  type TransportSourceIdentity,
} from "./transport/index.js";

type EventIdentity = TransportSourceIdentity | TransportAttemptIdentity | TransportFailureIdentity;

export function transportEventIdentityIsCurrent(
  identities: TransportIdentityRegistry,
  ord: number,
  event: HtmlAudioSessionEvent,
  identity: EventIdentity | undefined,
): boolean {
  const scope = transportIdentityScopeFor(event);
  if (scope === "runtime") return true;
  if (!identity) return false;
  if (scope === "attempt") {
    return "attemptId" in identity
      && !("failureId" in identity)
      && identities.acceptsAttempt(ord, identity);
  }
  if ("failureId" in identity) return identities.acceptsFailure(ord, identity);
  if ("attemptId" in identity) return identities.acceptsAttempt(ord, identity);
  return identities.acceptsSource(ord, identity);
}

export function requireTransportSourceIdentity(
  identities: TransportIdentityRegistry,
  ord: number,
): TransportSourceIdentity {
  const identity = identities.currentSource(ord);
  if (!identity) throw new Error(`T-02: field ${ord} has no active source identity`);
  return identity;
}

export function requireTransportAttemptIdentity(
  identities: TransportIdentityRegistry,
  ord: number,
): TransportAttemptIdentity {
  const identity = identities.currentAttempt(ord);
  if (!identity) throw new Error(`T-03: field ${ord} has no active playback attempt identity`);
  return identity;
}

export function requireTransportFailureIdentity(
  identities: TransportIdentityRegistry,
  ord: number,
): TransportFailureIdentity {
  const identity = identities.currentFailure(ord);
  if (!identity) throw new Error(`T-10: field ${ord} has no current transport failure identity`);
  return identity;
}
