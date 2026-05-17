import type { FrontendLogPayload, ProsodyPayload } from "../lib/generated/contracts.js";

export type EditorCommand =
  | "aqe:play"
  | "aqe:analyze"
  | "aqe:show-file"
  | "aqe:trim-left"
  | "aqe:trim-right"
  | "aqe:remove-pauses"
  | "aqe:remove-noise"
  | "aqe:sidon"
  | "aqe:mp-senet"
  | "aqe:slower"
  | "aqe:faster"
  | "aqe:volume-down"
  | "aqe:volume-up"
  | "aqe:undo";

export interface ButtonSpec {
  command: EditorCommand;
  label: string;
  title: string;
}

export interface EditorRuntimeConfig {
  audioFieldIndices: number[];
}

export interface FieldTarget {
  node: HTMLElement;
  ord: number;
  sourceFilename: string;
}

export type ProsodyPoint = readonly [number, number | null, number | null, boolean | null];

export interface NormalizedProsodyTrack {
  analyzerName: string;
  durationMs: number;
  pitchMaxHz: number | null;
  pitchMinHz: number | null;
  points: ProsodyPoint[];
  sourceFilename: string;
}

export interface PlaybackRequest {
  action: "start" | "pause" | "resume";
  cursorMs: number;
  engine?: "html" | "native" | "";
  ord: number;
}

export interface CursorIntent {
  cursorMs: number;
  engine?: "html" | "native" | "";
  previousPlaybackState: PlaybackState;
  restartPlayback: boolean;
}

export type PlaybackState = "playing" | "paused" | "stopped";
export type ProgressClockMode = "audio" | "manual" | "stopped";

export interface GraphStateForTest {
  active: boolean;
  allButtonsDisabled: boolean;
  anchorMs: number;
  anyButtonDisabled: boolean;
  audioClockCurrentMs: number;
  audioClockFallback: boolean;
  audioClockMuted: boolean;
  audioClockReady: boolean;
  audioClockSrc: string;
  audioPlaybackTestDriver: boolean;
  busy: boolean;
  cursorMs: number;
  cursorX: number;
  durationMs: number;
  graphButtonLabel: string;
  hasTrack: boolean;
  hidden: boolean;
  intensity: string;
  pitchPaths: number;
  playButtonLabel: string;
  playbackEngine: "html" | "native";
  playbackState: PlaybackState;
  progressClockMode: ProgressClockMode;
  progressMs: number;
  resumeRequiresRestart: boolean;
  sourceFilename: string;
  spinnerVisible: boolean;
  xAxisLabels: string[];
}

export interface CursorPositionForTest {
  bounds: {
    left: number;
    width: number;
  };
  cursorMs: number;
  cursorX: number;
}

export type AudioClockElement = HTMLAudioElement & {
  __aqeClockHandlersInstalled?: boolean;
  __aqeTestDriverInstalled?: boolean;
  __aqeTestFrame?: number | null;
  __aqeTestLastNow?: number;
  __aqeTestPlaying?: boolean;
};

export type VisualizerElement = HTMLElement & {
  __aqeAudioClockAvailable?: boolean;
  __aqeAudioClockFallback?: boolean;
  __aqeAudioClockLastSeekedMs?: number;
  __aqePlaybackTimer?: number | null;
};

export interface MountedField {
  component: Record<string, unknown>;
  host: HTMLElement;
  ord: number;
  sourceFilename: string;
}

export type FrontendLogQueueItem = FrontendLogPayload;

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
