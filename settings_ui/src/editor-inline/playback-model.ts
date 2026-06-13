import type { PlaybackRequest, PlaybackState } from "./types.js";

export type PlaybackRegionMode = "selection" | "full";
export type PlaybackEngine = "html" | "native" | "";

export interface PlaybackRegion {
  endMs: number;
  mode: PlaybackRegionMode;
  startMs: number;
}

export interface PlaybackSnapshot {
  anchorMs: number;
  currentProgressMs: number | null;
  cursorMs: number;
  durationMs: number;
  engine: PlaybackEngine;
  ord: number;
  playbackState: PlaybackState;
  region: PlaybackRegion;
  repeat: boolean;
  resumeRequiresRestart: boolean;
}

export interface PlaybackPass {
  endMs: number;
  loop: boolean;
  regionMode: PlaybackRegionMode;
  resetCursorMs: number;
  startMs: number;
}

export type PlaybackBoundaryPlan =
  | { kind: "continue" }
  | { kind: "loop"; pass: PlaybackPass; repeatPauseMs: number }
  | { kind: "complete"; resetCursorMs: number };

export function clampMsToRegion(ms: number, region: Pick<PlaybackRegion, "startMs" | "endMs">): number {
  return Math.max(region.startMs, Math.min(finiteMs(ms), region.endMs));
}

export function planPlaybackRequest(snapshot: PlaybackSnapshot): PlaybackRequest {
  let action: PlaybackRequest["action"] = "start";
  if (snapshot.playbackState === "playing") action = "pause";
  if (snapshot.playbackState === "paused") {
    action = snapshot.resumeRequiresRestart ? "start" : "resume";
  }

  let cursorMs = progressOrFallback(null, snapshot.anchorMs, snapshot.cursorMs);
  const pausedRestart = snapshot.playbackState === "paused" && snapshot.resumeRequiresRestart;
  const fullCoverSelection = selectionCoversFullDuration(snapshot.region, snapshot.durationMs);
  if (action === "start" && snapshot.region.mode === "selection") {
    cursorMs = pausedRestart
      ? clampMsToRegion(progressOrFallback(snapshot.currentProgressMs, snapshot.cursorMs, cursorMs), snapshot.region)
      : fullCoverSelection
        ? clampMsToRegion(progressOrFallback(null, snapshot.anchorMs, snapshot.region.startMs), snapshot.region)
        : snapshot.region.startMs;
  }
  if (action === "pause") {
    cursorMs = progressOrFallback(snapshot.currentProgressMs, snapshot.cursorMs, cursorMs);
  }
  if (action === "resume") {
    cursorMs = progressOrFallback(snapshot.currentProgressMs, snapshot.cursorMs, cursorMs);
    if (snapshot.region.mode === "selection" && (cursorMs < snapshot.region.startMs || cursorMs > snapshot.region.endMs)) {
      action = "start";
      cursorMs = snapshot.region.startMs;
    }
  }
  const regionMode = fullCoverSelection && cursorMs > snapshot.region.startMs
    ? "full"
    : snapshot.region.mode;

  return {
    action,
    cursorMs: Math.round(cursorMs),
    endMs: Math.round(snapshot.region.endMs),
    engine: snapshot.engine,
    loop: snapshot.repeat,
    ord: snapshot.ord,
    regionMode,
  };
}

export function planPlaybackPass(snapshot: PlaybackSnapshot, startMs: number): PlaybackPass {
  const regionMode = snapshot.region.mode;
  const resetCursorMs = regionMode === "selection"
    ? snapshot.region.startMs
    : progressOrFallback(null, snapshot.anchorMs, snapshot.cursorMs);
  return {
    endMs: Math.round(snapshot.region.endMs),
    loop: snapshot.repeat,
    regionMode,
    resetCursorMs: Math.round(resetCursorMs),
    startMs: Math.round(startMs),
  };
}

export function planPlaybackBoundary(input: {
  nextMs: number;
  pass: PlaybackPass;
  repeat: boolean;
  repeatPauseMs: number;
}): PlaybackBoundaryPlan {
  if (input.nextMs < input.pass.endMs) return { kind: "continue" };
  if (input.repeat) {
    return {
      kind: "loop",
      pass: playbackLoopPass(input.pass),
      repeatPauseMs: input.repeatPauseMs,
    };
  }
  return {
    kind: "complete",
    resetCursorMs: playbackCompletionCursor(input.pass),
  };
}

export function playbackCompletionCursor(pass: Pick<PlaybackPass, "regionMode" | "resetCursorMs">): number {
  return Math.round(pass.resetCursorMs);
}

function playbackLoopPass(pass: PlaybackPass): PlaybackPass {
  return {
    ...pass,
    startMs: playbackCompletionCursor(pass),
  };
}

export function selectionCoversFullDuration(region: PlaybackRegion, durationMs: number): boolean {
  const duration = Math.max(0, finiteMs(durationMs));
  return region.mode === "selection" && duration > 0 && region.startMs <= 0 && region.endMs >= duration;
}

function progressOrFallback(currentProgressMs: number | null, cursorMs: number, fallbackMs: number): number {
  return finiteMsOrNull(currentProgressMs) ?? finiteMsOrNull(cursorMs) ?? finiteMs(fallbackMs);
}

function finiteMsOrNull(value: number | null): number | null {
  if (value === null || value === undefined) return null;
  return Number.isFinite(value) ? value : null;
}

function finiteMs(value: number): number {
  return Number.isFinite(value) ? value : 0;
}
