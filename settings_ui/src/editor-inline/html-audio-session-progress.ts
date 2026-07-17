import type { HtmlAudioSessionEvent, HtmlAudioSessionState, HtmlAudioStartRequest } from "./html-audio-session-types.js";

export interface HtmlAudioProgressClock {
  cursorMs: number;
  endMs: number;
  startedAtMs: number;
}

type ActiveHtmlAudioSessionState = Extract<HtmlAudioSessionState, { kind: "starting" | "playing" }>;
type BoundaryReachedEvent = Extract<HtmlAudioSessionEvent, { type: "BoundaryReached" }>;

export interface HtmlAudioProgressDecisionInput {
  audioProgressMs: number;
  clock: HtmlAudioProgressClock;
  graphDurationMs: number;
  nowMs: number;
  state: ActiveHtmlAudioSessionState;
}

export type HtmlAudioProgressDecision =
  | { kind: "learner_progress"; progressMs: number; learnerCursorMs: number }
  | { kind: "source_progress"; progressMs: number }
  | { kind: "boundary"; progressMs: number; event: BoundaryReachedEvent };

export function htmlAudioProgressDecision(input: HtmlAudioProgressDecisionInput): HtmlAudioProgressDecision {
  const progressMs = htmlAudioProgressMs(input.clock, input.nowMs, input.audioProgressMs);
  if (input.state.source.kind === "learner_recording") {
    return {
      kind: "learner_progress",
      learnerCursorMs: input.state.source.startCursorMs + progressMs,
      progressMs,
    };
  }
  if (input.audioProgressMs < htmlAudioBoundaryMsForRequest(
    input.state.request,
    input.graphDurationMs,
    input.clock.endMs,
  )) {
    return { kind: "source_progress", progressMs };
  }
  return {
    kind: "boundary",
    progressMs,
    event: boundaryReachedEvent(
      input.state.request,
      input.clock.endMs,
    ),
  };
}

export function htmlAudioProgressMs(
  clock: HtmlAudioProgressClock,
  nowMs: number,
  audioProgressMs: number,
): number {
  const elapsedProgressMs = Math.round(clock.cursorMs + Math.max(0, nowMs - clock.startedAtMs));
  return Math.min(Math.max(audioProgressMs, elapsedProgressMs), clock.endMs);
}

export function htmlAudioBoundaryMsForRequest(
  request: HtmlAudioStartRequest,
  graphDurationMs: number,
  endMs: number,
): number {
  if (
    request.cursorMs <= 0 &&
    request.loop &&
    (request.regionMode === "full" || (graphDurationMs > 0 && request.endMs >= Math.max(0, graphDurationMs - 20)))
  ) {
    return Math.max(0, endMs - 40);
  }
  return endMs;
}

function boundaryReachedEvent(
  request: HtmlAudioStartRequest,
  endMs: number,
): BoundaryReachedEvent {
  return {
    cursorMs: endMs,
    resetCursorMs: request.cursorMs,
    type: "BoundaryReached",
  };
}
