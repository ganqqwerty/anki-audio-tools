import type { FrontendLogPayload, ProsodyPayload } from "../lib/generated/contracts.js";
import type { CommandIconName } from "../lib/icon-types.js";

export type EditorCommand =
  | "aqe:play"
  | "aqe:analyze"
  | "aqe:show-file"
  | "aqe:delete-selection"
  | "aqe:delete-rest"
  | "aqe:trim-left"
  | "aqe:trim-right"
  | "aqe:remove-pauses"
  | "aqe:denoise-standard"
  | "aqe:rnnoise"
  | "aqe:slower"
  | "aqe:faster"
  | "aqe:volume-down"
  | "aqe:volume-up"
  | "aqe:undo"
  | "aqe:redo"
  | "aqe:settings";

export type EditorIconName = CommandIconName;

export interface ButtonSpec {
  activeIcon?: EditorIconName;
  command: EditorCommand;
  icon: EditorIconName;
  iconOnly?: boolean;
  label: string;
  title: string;
}

export interface EditorRuntimeConfig {
  audioFieldIndices: number[];
  audioFieldSources?: Record<number, string>;
  direction?: "ltr" | "rtl";
  locale?: string;
  messages?: Record<string, string>;
  repeatPlaybackByDefault?: boolean;
  showGraphByDefault?: boolean;
  splitButtonDefaults?: SplitButtonDefaults;
}

export interface SplitButtonDefaults {
  denoiseAlgorithm: "standard" | "rnnoise";
  pauseAggressiveness: "gentle" | "normal" | "aggressive";
  repeatPauseSeconds: number;
  speedStep: number;
  trimStepMs: number;
  volumeStepDb: number;
}

export interface EditorCommandPayload {
  command: EditorCommand;
  fieldOrd: number;
  overrides?: {
    denoiseAlgorithm?: "standard" | "rnnoise";
    pauseAggressiveness?: "gentle" | "normal" | "aggressive";
    speedStep?: number;
    trimStepMs?: number;
    volumeStepDb?: number;
  };
}

export interface FieldSplitButtonState {
  defaultDenoiseAlgorithm: "standard" | "rnnoise";
  defaultPauseAggressiveness: "gentle" | "normal" | "aggressive";
  defaultRepeatPauseSeconds: number;
  defaultTrimStepMs: number;
  defaultSpeedStep: number;
  defaultVolumeStepDb: number;
  denoiseAlgorithm: "standard" | "rnnoise";
  denoiseEdited: boolean;
  pauseAggressiveness: "gentle" | "normal" | "aggressive";
  pauseEdited: boolean;
  repeatPauseEdited: boolean;
  repeatPauseSeconds: number;
  speedEdited: boolean;
  speedStep: number;
  trimEdited: boolean;
  trimStepMs: number;
  volumeEdited: boolean;
  volumeStepDb: number;
}

export interface FieldTarget {
  node: HTMLElement;
  ord: number;
  sourceFilename: string;
}

export interface DefaultGraphTarget {
  ord: number;
  sourceFilename: string;
}

export interface GraphAnalysisRequest {
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
  endMs?: number;
  engine?: "html" | "native" | "";
  loop?: boolean;
  ord: number;
  regionMode?: "selection" | "full";
}

export interface RegionDeleteRequest {
  cursorMs: number;
  durationMs: number;
  operation: RegionDeleteOperation;
  ord: number;
  playbackActive: boolean;
  selectionEndMs: number;
  selectionStartMs: number;
  sourceFilename: string;
  trigger: "button" | "backspace";
}

type RegionDeleteOperation = "delete-selection" | "delete-rest";

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
  graphButtonState: string;
  graphButtonTitle: string;
  hasTrack: boolean;
  hidden: boolean;
  intensity: string;
  pitchPaths: number;
  buttonIconCount: number;
  buttonIconStrokeValues: string[];
  playButtonLabel: string;
  playButtonState: string;
  playbackEngine: "html" | "native";
  playbackEndMs: number;
  playbackRegionMode: "selection" | "full";
  playbackStartMs: number;
  playbackState: PlaybackState;
  progressClockMode: ProgressClockMode;
  progressMs: number;
  repeatControlDisabled: boolean;
  regionDeleteButtonDisabled: boolean;
  regionDeleteButtonHidden: boolean;
  regionDeleteRestButtonDisabled: boolean;
  regionDeleteRestButtonHidden: boolean;
  repeatEnabled: boolean;
  repeatPauseSeconds: number;
  repeatPauseWaiting: boolean;
  resumeRequiresRestart: boolean;
  selectionActive: boolean;
  selectionDraftActive: boolean;
  selectionDraftEndMs: number | null;
  selectionDraftStartMs: number | null;
  selectionEndHandleVisible: boolean;
  selectionEndHandleX: number | null;
  selectionEndMs: number | null;
  selectionStartHandleVisible: boolean;
  selectionStartHandleX: number | null;
  selectionStartMs: number | null;
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
  __aqeRepeatPauseTimer?: number | null;
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
