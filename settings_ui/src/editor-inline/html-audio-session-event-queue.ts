import type { HtmlAudioSessionEffect, HtmlAudioSessionEvent } from "./html-audio-session-machine.js";
import { transportEventIdentityIsCurrent } from "./html-audio-session-identities.js";
import { transportIdentityLogContext } from "./html-audio-session-logging.js";
import { logger } from "./logger.js";
import {
  eventInterruptsEffectBatch,
  type TransportAttemptIdentity,
  type TransportFailureIdentity,
  TransportIdentityRegistry,
  type TransportSourceIdentity,
} from "./transport/index.js";

type EventIdentity = TransportSourceIdentity | TransportAttemptIdentity | TransportFailureIdentity;

export interface QueuedHtmlAudioSessionEvent {
  event: HtmlAudioSessionEvent;
  guard?: () => boolean;
  identity?: EventIdentity;
}

interface HtmlAudioSessionEventQueueDependencies {
  identities: () => TransportIdentityRegistry;
  process: (ord: number, event: HtmlAudioSessionEvent) => void;
}

/** Serializes reentrant media facts and interrupts stale outer effect batches. */
export class HtmlAudioSessionEventQueue {
  private readonly activeEffectBatches = new Map<number, { interrupted: boolean }>();
  private readonly processing = new Set<number>();
  private readonly queued = new Map<number, QueuedHtmlAudioSessionEvent[]>();

  constructor(private readonly dependencies: HtmlAudioSessionEventQueueDependencies) {}

  clear(ord: number): void {
    this.queued.delete(ord);
  }

  enqueue(ord: number, queued: QueuedHtmlAudioSessionEvent): void {
    const queue = this.queued.get(ord) ?? [];
    queue.push(queued);
    this.queued.set(ord, queue);
    const activeBatch = this.activeEffectBatches.get(ord);
    if (activeBatch && eventInterruptsEffectBatch(queued.event)) activeBatch.interrupted = true;
    if (this.processing.has(ord)) return;

    this.processing.add(ord);
    try {
      while (queue.length > 0) {
        const next = queue.shift()!;
        if (!transportEventIdentityIsCurrent(this.dependencies.identities(), ord, next.event, next.identity)
          || (next.guard && !next.guard())) {
          logger.debug("transport.stale_event_ignored", {
            eventType: next.event.type,
            ord,
            ...transportIdentityLogContext(next.identity),
          });
          continue;
        }
        this.dependencies.process(ord, next.event);
      }
    } finally {
      this.processing.delete(ord);
      this.queued.delete(ord);
    }
  }

  executeEffects(
    ord: number,
    effects: readonly HtmlAudioSessionEffect[],
    execute: (ord: number, effect: HtmlAudioSessionEffect) => boolean,
  ): void {
    const batch = { interrupted: false };
    this.activeEffectBatches.set(ord, batch);
    try {
      for (const effect of effects) {
        if (execute(ord, effect) || batch.interrupted) break;
      }
    } finally {
      this.activeEffectBatches.delete(ord);
    }
  }
}
