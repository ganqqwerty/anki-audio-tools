import type { PlaybackRequest, PlaybackState } from "./types.js";

export type PlaybackRegionMode = "selection" | "full";
export type PlaybackEngine = "html" | "native" | "";

export interface PlaybackRegion {
  endMs: number;
  mode: PlaybackRegionMode;
  startMs: number;
}

export interface PlaybackRequestState {
  anchorMs: number;
  currentProgressMs: number | null;
  cursorMs: number;
  engine: PlaybackEngine;
  ord: number;
  playbackState: PlaybackState;
  region: PlaybackRegion;
  repeat: boolean;
  resumeRequiresRestart: boolean;
}

export function clampMsToRegion(ms: number, region: Pick<PlaybackRegion, "startMs" | "endMs">): number {
  return Math.max(region.startMs, Math.min(Number(ms) || 0, region.endMs));
}

export function buildPlaybackRequestForPython(state: PlaybackRequestState): PlaybackRequest {
  let action: PlaybackRequest["action"] = "start";
  if (state.playbackState === "playing") action = "pause";
  if (state.playbackState === "paused") {
    action = state.resumeRequiresRestart ? "start" : "resume";
  }

  let cursorMs = state.anchorMs;
  if (action === "start" && state.region.mode === "selection") {
    cursorMs = state.region.startMs;
  }
  if (action === "pause") {
    cursorMs = progressOrFallback(state.currentProgressMs, state.cursorMs, cursorMs);
  }
  if (action === "resume") {
    cursorMs = progressOrFallback(state.currentProgressMs, state.cursorMs, cursorMs);
    if (state.region.mode === "selection" && (cursorMs < state.region.startMs || cursorMs > state.region.endMs)) {
      action = "start";
      cursorMs = state.region.startMs;
    }
  }

  return {
    action,
    cursorMs: Math.round(cursorMs),
    endMs: Math.round(state.region.endMs),
    engine: state.engine,
    loop: state.repeat,
    ord: state.ord,
    regionMode: state.region.mode,
  };
}

export function playbackRegionForCompletion(
  region: PlaybackRegion,
  anchorMs: number,
  playbackRegionMode: PlaybackRegionMode,
): number {
  return playbackRegionMode === "selection" ? region.startMs : anchorMs;
}

export function shouldLoopAtBoundary(nextMs: number, endMs: number, repeat: boolean): boolean {
  return repeat && nextMs >= endMs;
}

function progressOrFallback(currentProgressMs: number | null, cursorMs: number, fallbackMs: number): number {
  return Number(currentProgressMs || cursorMs || fallbackMs || 0);
}
