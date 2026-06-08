import type { ProsodyPayload } from "../lib/generated/contracts.js";
import type { NormalizedProsodyTrack, PlaybackState, ProsodyPoint } from "./editor-playback-types";

export type {
  AudioClockElement,
  CursorIntent,
  CursorPositionForTest,
  DefaultGraphTarget,
  FrontendLogQueueItem,
  FieldTarget,
  GraphAnalysisRequest,
  GraphStateForTest,
  MountedField,
  NormalizedProsodyTrack,
  PlaybackRequest,
  PlaybackState,
  PostEditPlaybackIntent,
  ProgressClockMode,
  ProsodyPoint,
  RegionDeleteRequest,
  VisualizerElement,
} from "./editor-playback-types";
export type {
  ButtonSpec,
  EditorCommand,
  EditorCommandPayload,
  EditorRuntimeConfig,
  FieldSplitButtonState,
  SplitButtonDefaults,
} from "./editor-runtime-types";

export function normalizeTrack(track: ProsodyPayload): NormalizedProsodyTrack {
  return {
    analyzerName: track.analyzerName,
    durationMs: Number(track.durationMs) || 0,
    pitchMaxHz: track.pitchMaxHz,
    pitchMinHz: track.pitchMinHz,
    points: track.points.map(normalizePoint),
    sourceFilename: track.sourceFilename,
  };
}

function normalizePoint(point: Array<boolean | number | null>): ProsodyPoint {
  const time = typeof point[0] === "number" ? point[0] : 0;
  const pitch = typeof point[1] === "number" ? point[1] : null;
  const intensity = typeof point[2] === "number" ? point[2] : null;
  const voiced = typeof point[3] === "boolean" ? point[3] : false;
  return [time, pitch, intensity, voiced];
}

export function isPlaybackState(value: string | undefined): value is PlaybackState {
  return value === "playing" || value === "paused" || value === "stopped";
}
