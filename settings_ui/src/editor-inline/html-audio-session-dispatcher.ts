import { HtmlAudioSessionEventQueue } from "./html-audio-session-event-queue.js";
import type {
  HtmlAudioSessionEffect,
  HtmlAudioSessionEvent,
} from "./html-audio-session-types.js";
import type {
  TransportAttemptIdentity,
  TransportFailureIdentity,
  TransportIdentityRegistry,
  TransportSourceIdentity,
} from "./transport/index.js";

interface HtmlAudioSessionDispatcherDependencies {
  identities: () => TransportIdentityRegistry;
  process: (ord: number, event: HtmlAudioSessionEvent) => void;
}

/** Identity-guards every external fact before it reaches the transport reducer. */
export class HtmlAudioSessionDispatcher {
  private readonly queue: HtmlAudioSessionEventQueue;

  constructor(private readonly dependencies: HtmlAudioSessionDispatcherDependencies) {
    this.queue = new HtmlAudioSessionEventQueue(dependencies);
  }

  event(ord: number, event: HtmlAudioSessionEvent): void {
    this.queue.enqueue(ord, { event });
  }

  sourceFact(ord: number, identity: TransportSourceIdentity, event: HtmlAudioSessionEvent): void {
    this.enqueueIdentityFact(ord, identity, event, () => (
      this.dependencies.identities().acceptsSource(ord, identity)
    ));
  }

  attemptFact(ord: number, identity: TransportAttemptIdentity, event: HtmlAudioSessionEvent): void {
    this.enqueueIdentityFact(ord, identity, event, () => (
      this.dependencies.identities().acceptsAttempt(ord, identity)
    ));
  }

  failureFact(ord: number, identity: TransportFailureIdentity, event: HtmlAudioSessionEvent): void {
    this.enqueueIdentityFact(ord, identity, event, () => (
      this.dependencies.identities().acceptsFailure(ord, identity)
    ));
  }

  executeEffects(
    ord: number,
    effects: readonly HtmlAudioSessionEffect[],
    execute: (ord: number, effect: HtmlAudioSessionEffect) => boolean,
  ): void {
    this.queue.executeEffects(ord, effects, execute);
  }

  clear(ord: number): void {
    this.queue.clear(ord);
  }

  private enqueueIdentityFact(
    ord: number,
    identity: TransportSourceIdentity | TransportAttemptIdentity | TransportFailureIdentity,
    event: HtmlAudioSessionEvent,
    guard: () => boolean,
  ): void {
    this.queue.enqueue(ord, { event, guard, identity });
  }
}
