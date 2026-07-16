import type { ChorusingState } from "./chorusing-state";
import type { GraphSettings } from "./graph-settings.js";
import type { HtmlAudioReadinessReason, HtmlAudioReadinessState } from "./audio-readiness.js";
import type { PlaybackProgressPlan } from "./playback-progress-clock.js";

export type { FrontendLogPayload as FrontendLogQueueItem } from "../lib/generated/contracts.js";

export interface FieldTarget {
  node: HTMLElement;
  ord: number;
  sourceFilename: string;
}

export interface DefaultGraphTarget {
  ord: number;
  sourceFilename: string;
  graphSettings?: GraphSettings;
}

export interface GraphAnalysisRequest {
  graphSettings?: GraphSettings;
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
  engine?: "html" | "";
  loop?: boolean;
  ord: number;
  regionMode?: "selection" | "full";
  source?: "post_edit" | "user";
}

export interface PostEditPlaybackIntent {
  repeat: boolean;
  repeatPauseSeconds: number;
}

type RegionDeleteOperation = "delete-selection" | "delete-rest";

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

export interface CursorIntent {
  cursorMs: number;
  endMs?: number;
  engine?: "html" | "";
  previousPlaybackState: PlaybackState;
  regionMode?: "selection" | "full";
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
  htmlAudioReadinessReason: HtmlAudioReadinessReason;
  htmlAudioReadinessState: HtmlAudioReadinessState;
  intensity: string;
  learnerDurationMs: number;
  learnerIntensityPaths: number;
  learnerPitchPaths: number;
  learnerPlaybackStatus: string;
  learnerRecordingStatus: string;
  learnerStartCursorMs: number;
  pitchPaths: number;
  pitchMarkerVisible: boolean;
  pitchMarkerX: number | null;
  pitchMarkerY: number | null;
  buttonIconCount: number;
  buttonIconStrokeValues: string[];
  playButtonLabel: string;
  playButtonState: string;
  playbackEngine: "html" | "";
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
  targetDurationMs: number;
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
  selectionToolbarDeleteRegionDisabled: boolean;
  selectionToolbarDeleteRegionHidden: boolean;
  selectionToolbarDeleteRestDisabled: boolean;
  selectionToolbarDeleteRestHidden: boolean;
  selectionToolbarHidden: boolean;
  selectionToolbarLeftPx: number | null;
  selectionToolbarPlayAriaLabel: string;
  selectionToolbarPlayState: "pause" | "play";
  selectionToolbarPreview: "none" | "region" | "rest";
  selectionToolbarTopPx: number | null;
  chorusingActiveEndMs: number | null;
  chorusingActiveMarkerIndex: number | null;
  chorusingActiveStartMs: number | null;
  chorusingBaseEndMs: number | null;
  chorusingBaseStartMs: number | null;
  chorusingAutoAdvance: boolean;
  chorusingCanNext: boolean;
  chorusingCanPrevious: boolean;
  chorusingCanPractice: boolean;
  chorusingMarkerVisibleXs: number[];
  chorusingMarkersMs: number[];
  chorusingRepeatCount: number;
  chorusingRepeatPassesCompleted: number;
  chorusingState: "paused" | "playing" | "stopped";
  chorusingVisibleActiveRangeEndX: number | null;
  chorusingVisibleActiveRangeStartX: number | null;
  sourceFilename: string;
  spinnerVisible: boolean;
  timecodeFlagCurrent: string;
  timecodeFlagPitch: string;
  timecodeFlagTransform: string;
  timecodeFlagVisible: boolean;
  viewportEndMs: number;
  viewportStartMs: number;
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
  __aqeHtmlAudioFailureReason?: HtmlAudioReadinessReason | "";
  __aqeHtmlAudioMediaErrorCode?: number | null;
  __aqeHtmlAudioMediaResponseStatus?: number | null;
  __aqeCursorPaintedAtMs?: number;
  __aqeCursorRenderCache?: CursorRenderCache;
  __aqeCursorTextPaintedAtMs?: number;
  __aqeLiveProgressMs?: number;
  __aqePlaybackGeneration?: number;
  __aqePlaybackPlan?: PlaybackProgressPlan;
  __aqeChorusingState?: ChorusingState;
  __aqeLearnerTrack?: NormalizedProsodyTrack;
  __aqeRecordingCursorFrame?: number | null;
  __aqeRecordingStartedAt?: number | null;
  __aqeRecordCountdownTimer?: number | null;
  __aqeTrack?: NormalizedProsodyTrack;
  __aqePlaybackTimer?: number | null;
  __aqeRepeatPauseTimer?: number | null;
  __aqeRepeatPauseOverlayTimer?: number | null;
};

interface CursorRenderCache {
  cssCursor: HTMLElement | null;
  cssFlag: HTMLElement | null;
  cssFlagCurrent: HTMLElement | null;
  cssFlagPitch: HTMLElement | null;
  cssLine: HTMLElement | null;
  label: HTMLElement | null;
  svg: SVGSVGElement | null;
}

export interface MountedField {
  component: Record<string, unknown>;
  host: HTMLElement;
  ord: number;
  sourceFilename: string;
}
