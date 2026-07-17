import type { PlaybackRequest, PlaybackState } from "./types.js";

export type PlaybackRegionMode = "selection" | "full";
export type PlaybackEngine = "html" | "";

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

export function clampMsToRegion(ms: number, region: Pick<PlaybackRegion, "startMs" | "endMs">): number {
  return Math.max(region.startMs, Math.min(finiteMs(ms), region.endMs));
}

export function planPlaybackRequest(snapshot: PlaybackSnapshot): PlaybackRequest {
  const fullCoverSelection = selectionCoversFullDuration(snapshot.region, snapshot.durationMs);
  const pausedSelectedRepeatRestart = snapshot.playbackState === "paused"
    && snapshot.repeat
    && snapshot.region.mode === "selection"
    && !fullCoverSelection;
  let action: PlaybackRequest["action"] = "start";
  if (snapshot.playbackState === "playing") action = "pause";
  if (snapshot.playbackState === "paused") {
    action = snapshot.resumeRequiresRestart || pausedSelectedRepeatRestart ? "start" : "resume";
  }

  let cursorMs = progressOrFallback(null, snapshot.anchorMs, snapshot.cursorMs);
  const pausedRestart = snapshot.playbackState === "paused"
    && snapshot.resumeRequiresRestart
    && !pausedSelectedRepeatRestart;
  if (action === "start" && snapshot.region.mode === "selection") {
    if (pausedSelectedRepeatRestart) {
      cursorMs = snapshot.region.startMs;
    } else {
      cursorMs = pausedRestart
        ? clampMsToRegion(snapshot.cursorMs, snapshot.region)
        : fullCoverSelection
          ? clampMsToRegion(progressOrFallback(null, snapshot.anchorMs, snapshot.region.startMs), snapshot.region)
          : snapshot.region.startMs;
    }
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

export function playbackStateIsStopped(state: PlaybackState): boolean {
  return state === "stopped";
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
