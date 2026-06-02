import type { PlaybackRequest } from "./types.js";
import {
  clampMsToRegion,
  planPlaybackRequest,
  type PlaybackEngine,
  type PlaybackRegion,
  type PlaybackRegionMode,
  type PlaybackSnapshot,
} from "./playback-model.js";

export {
  clampMsToRegion,
};
export type {
  PlaybackEngine,
  PlaybackRegion,
  PlaybackRegionMode,
};

export type PlaybackRequestState = PlaybackSnapshot;

export function buildPlaybackRequestForPython(state: PlaybackRequestState): PlaybackRequest {
  return planPlaybackRequest(state);
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
