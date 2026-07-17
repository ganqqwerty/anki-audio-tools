import { visualizerForOrd } from "./dom-selectors.js";
import { readFieldState, setCachedProgressMs } from "./field-state-store.js";
import { audioProgressMsForOrd } from "./html-audio-session-audio-element.js";
import {
  htmlAudioProgressDecision,
  type HtmlAudioProgressClock,
} from "./html-audio-session-progress.js";
import { renderLearnerPlaybackCursor } from "./html-audio-session-learner-projection.js";
import type {
  HtmlAudioSessionEvent,
  HtmlAudioSessionState,
  HtmlAudioStartRequest,
} from "./html-audio-session-types.js";
import { logger } from "./logger.js";
import type {
  TransportAttemptIdentity,
  TransportSourceIdentity,
} from "./transport/index.js";
import { ensurePlaybackCursorVisible } from "./viewport-actions.js";
import { renderPlaybackCursor } from "./visualizer-renderer.js";

interface HtmlAudioSessionResourceDependencies {
  acceptsAttempt: (ord: number, identity: TransportAttemptIdentity) => boolean;
  dispatchAttemptFact: (
    ord: number,
    identity: TransportAttemptIdentity,
    event: HtmlAudioSessionEvent,
  ) => void;
  dispatchSourceFact: (
    ord: number,
    identity: TransportSourceIdentity,
    event: HtmlAudioSessionEvent,
  ) => void;
  readAttemptIdentity: (ord: number) => TransportAttemptIdentity;
  readSourceIdentity: (ord: number) => TransportSourceIdentity;
  readState: (ord: number) => HtmlAudioSessionState;
  publishPosition: (ord: number, positionMs: number) => void;
}

/** Owns every frame and timer allocated by the compatibility transport. */
export class HtmlAudioSessionResources {
  private readonly progressFrames = new Map<number, number | null>();
  private readonly progressClocks = new Map<number, HtmlAudioProgressClock>();
  private readonly progressFrameIdentities = new Map<number, TransportAttemptIdentity>();
  private readonly metadataTimers = new Map<number, number>();

  constructor(private readonly dependencies: HtmlAudioSessionResourceDependencies) {}

  activeOrds(): number[] {
    return [...new Set([
      ...this.progressFrames.keys(),
      ...this.metadataTimers.keys(),
    ])];
  }

  snapshot(ord: number): { hasMetadataTimer: boolean; hasProgressFrame: boolean } {
    return {
      hasMetadataTimer: this.metadataTimers.has(ord),
      hasProgressFrame: this.progressFrames.has(ord),
    };
  }

  startProgressFrame(ord: number, cursorMs: number, endMs: number): void {
    this.clearProgressFrame(ord);
    const attemptIdentity = this.dependencies.readAttemptIdentity(ord);
    const visualizer = visualizerForOrd(ord);
    const session = this.dependencies.readState(ord);
    if (visualizer && "source" in session && session.source?.kind === "source") {
      ensurePlaybackCursorVisible(visualizer, cursorMs);
    }
    this.dependencies.publishPosition(ord, cursorMs);
    setCachedProgressMs(ord, cursorMs, visualizer);
    if (typeof window.requestAnimationFrame !== "function") {
      this.progressFrames.set(ord, null);
      this.progressFrameIdentities.set(ord, attemptIdentity);
      return;
    }
    this.progressClocks.set(ord, { cursorMs, endMs, startedAtMs: performance.now() });
    this.progressFrameIdentities.set(ord, attemptIdentity);
    const tick = (): void => {
      if (
        this.progressFrameIdentities.get(ord) !== attemptIdentity
        || !this.dependencies.acceptsAttempt(ord, attemptIdentity)
      ) {
        logger.debug("transport.stale_progress_frame_ignored", {
          attemptId: attemptIdentity.attemptId,
          fieldInstanceId: attemptIdentity.fieldInstanceId,
          ord,
          runtimeId: attemptIdentity.runtimeId,
          sourceInstanceId: attemptIdentity.sourceInstanceId,
        });
        return;
      }
      const nowMs = performance.now();
      const state = this.dependencies.readState(ord);
      if (state.kind !== "starting" && state.kind !== "playing") {
        this.clearProgressFrame(ord);
        return;
      }
      const clock = this.progressClocks.get(ord);
      if (!clock) return;
      const field = state.source.kind === "source" ? readFieldState(ord) : null;
      const currentVisualizer = state.source.kind === "source" ? visualizerForOrd(ord) : null;
      const graphDurationMs = field?.graph.durationMs ?? state.durationMs;
      const decision = htmlAudioProgressDecision({
        audioProgressMs: audioProgressMsForOrd(ord),
        clock,
        graphDurationMs,
        nowMs,
        state,
      });
      if (decision.kind === "learner_progress") {
        this.dependencies.publishPosition(ord, decision.progressMs);
        renderLearnerPlaybackCursor(ord, decision.learnerCursorMs);
      } else {
        this.dependencies.publishPosition(ord, decision.progressMs);
        setCachedProgressMs(ord, decision.progressMs, currentVisualizer);
        if (currentVisualizer) {
          ensurePlaybackCursorVisible(currentVisualizer, decision.progressMs);
          renderPlaybackCursor(currentVisualizer, decision.progressMs, graphDurationMs, nowMs);
        }
        if (decision.kind === "boundary") {
          this.dependencies.dispatchAttemptFact(ord, attemptIdentity, decision.event);
          return;
        }
      }
      this.progressFrames.set(ord, window.requestAnimationFrame(tick));
    };
    this.progressFrames.set(ord, window.requestAnimationFrame(tick));
  }

  clearProgressFrame(ord: number): void {
    const frame = this.progressFrames.get(ord);
    if (frame !== undefined && frame !== null && typeof window.cancelAnimationFrame === "function") {
      window.cancelAnimationFrame(frame);
    }
    this.progressFrames.delete(ord);
    this.progressClocks.delete(ord);
    this.progressFrameIdentities.delete(ord);
  }

  startMetadataTimer(ord: number, timeoutMs: number): void {
    this.clearMetadataTimer(ord);
    const sourceIdentity = this.dependencies.readSourceIdentity(ord);
    this.metadataTimers.set(ord, window.setTimeout(() => {
      this.metadataTimers.delete(ord);
      this.dependencies.dispatchSourceFact(ord, sourceIdentity, { type: "MetadataTimeout" });
    }, Math.max(0, timeoutMs)));
  }

  clearMetadataTimer(ord: number): void {
    const timer = this.metadataTimers.get(ord);
    if (timer !== undefined) window.clearTimeout(timer);
    this.metadataTimers.delete(ord);
  }

}

export function resetCursorMsForRequest(request: HtmlAudioStartRequest): number {
  if (request.resetCursorMs !== undefined) return Math.round(request.resetCursorMs);
  if (request.regionMode === "selection") {
    const selectionStartMs = readFieldState(request.ord).selection.startMs;
    if (selectionStartMs !== null) return Math.round(selectionStartMs);
  }
  return request.cursorMs;
}
