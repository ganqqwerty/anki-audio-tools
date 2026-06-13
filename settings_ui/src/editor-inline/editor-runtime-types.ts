import type { OutputFormatValue } from "../lib/audio-operation-parameters.js";
import type { SizeReductionMode } from "../lib/size-reduction-parameters.js";
import type {
  EditorButtonModes,
  EditorCommand as SharedEditorCommand,
  ToolbarButtonSpec,
} from "../lib/editor-toolbar-buttons.js";
import type {
  GraphRecordingCondition,
  GraphSmoothness,
  GraphVoiceLock,
  GraphVoiceRange,
  GraphSettings,
} from "./graph-settings.js";

export type EditorCommand = SharedEditorCommand;

export type ButtonSpec = ToolbarButtonSpec;

export interface HistorySnapshotItem {
  id: string;
  label: string;
}

export interface HistorySnapshot {
  canRedo: boolean;
  canUndo: boolean;
  redoItems: HistorySnapshotItem[];
  undoItems: HistorySnapshotItem[];
}

export interface EditorRuntimeConfig {
  audioFieldIndices: number[];
  audioFieldSources?: Record<number, string>;
  direction?: "ltr" | "rtl";
  editorHistorySize?: number;
  initialStatusByField?: Record<number, { kind?: string; message: string }>;
  initialHistoryAvailabilityByField?: Record<number, { canRedo: boolean; canUndo: boolean }>;
  initialHistorySnapshotsByField?: Record<number, HistorySnapshot>;
  locale?: string;
  messages?: Record<string, string>;
  pendingPostEditPlayback?: {
    fieldOrd: number;
    generation: number;
    requireGraphRedraw?: boolean;
    sourceFilename?: string;
  } | null;
  repeatPlaybackByDefault?: boolean;
  selectionMarkerShiftButtonsEnabled?: boolean;
  showGraphByDefault?: boolean;
  processingPresets?: ProcessingPresetOption[];
  splitButtonDefaults?: SplitButtonDefaults;
  visibleEditorButtons?: EditorCommand[];
  editorButtonModes?: EditorButtonModes;
}

type DenoiseAlgorithm = "standard" | "rnnoise" | "dpdfnet" | "voice_only";
type PauseDetectionAlgorithm = "silencedetect" | "silero_vad";
type PitchHumMode = "direct" | "pitch_tier";

export interface ProcessingPresetOption {
  graphEnabled: boolean;
  hasTransforms: boolean;
  id: string;
  name: string;
}

export interface SplitButtonDefaults {
  denoiseAlgorithm: DenoiseAlgorithm;
  dpdfnetAttnLimitDb?: number;
  graphConnectShortDropoutsMs?: number;
  graphRecordingCondition?: GraphRecordingCondition;
  graphSmoothness?: GraphSmoothness;
  graphVoiceLock?: GraphVoiceLock;
  graphVoiceRange?: GraphVoiceRange;
  outputFormat?: OutputFormatValue;
  sizeReductionMode?: SizeReductionMode;
  sizeReductionBitrateKbps?: number;
  sizeReductionSampleRateHz?: number;
  sizeReductionChannels?: number;
  pauseAggressiveness: "gentle" | "normal" | "aggressive";
  pauseDetectionAlgorithm?: PauseDetectionAlgorithm;
  pauseSilencedetectThresholdDb?: number;
  pauseSilencedetectMinSilenceSeconds?: number;
  pauseSilencedetectMinSpeechSeconds?: number;
  pauseSilencedetectPreprocessDenoise?: boolean;
  pauseSileroThreshold?: number;
  pauseSileroMinSilenceSeconds?: number;
  pauseSileroMinSpeechSeconds?: number;
  pauseSileroPreprocessDenoise?: boolean;
  pitchHumMode?: PitchHumMode;
  repeatPauseSeconds: number;
  shareTarget?: "catbox" | "litterbox";
  speedStep: number;
  voiceRecordingCountdownSeconds?: number;
  volumeStepDb: number;
}

export interface EditorCommandPayload {
  command: EditorCommand | "aqe:history-jump" | "aqe:open-url" | "aqe:post-edit-playback-ready";
  direction?: "redo" | "undo";
  fieldOrd?: number;
  generation?: number;
  presetId?: string;
  sourceFilename?: string;
  startCursorMs?: number;
  steps?: number;
  url?: string;
  shareTarget?: "catbox" | "litterbox";
  overrides?: {
    denoiseAlgorithm?: DenoiseAlgorithm;
    dpdfnetAttnLimitDb?: number;
    pauseAggressiveness?: "gentle" | "normal" | "aggressive";
    pauseDetectionAlgorithm?: PauseDetectionAlgorithm;
    pauseThreshold?: number;
    pauseMinSilenceSeconds?: number;
    pauseMinSpeechSeconds?: number;
    pausePreprocessDenoise?: boolean;
    pitchHumMode?: PitchHumMode;
    sizeReductionMode?: SizeReductionMode;
    sizeReductionBitrateKbps?: number;
    sizeReductionSampleRateHz?: number;
    sizeReductionChannels?: number;
    speedStep?: number;
    targetFormat?: OutputFormatValue;
    volumeStepDb?: number;
  };
  graphSettings?: GraphSettings;
}

export interface FieldSplitButtonState {
  defaultDenoiseAlgorithm: DenoiseAlgorithm;
  defaultGraphConnectShortDropoutsMs: number;
  defaultGraphRecordingCondition: GraphRecordingCondition;
  defaultGraphSmoothness: GraphSmoothness;
  defaultGraphVoiceLock: GraphVoiceLock;
  defaultGraphVoiceRange: GraphVoiceRange;
  defaultOutputFormat: OutputFormatValue;
  defaultPauseAggressiveness: "gentle" | "normal" | "aggressive";
  defaultPauseDetectionAlgorithm: PauseDetectionAlgorithm;
  defaultPauseSilencedetectThresholdDb: number;
  defaultPauseSilencedetectMinSilenceSeconds: number;
  defaultPauseSilencedetectMinSpeechSeconds: number;
  defaultPauseSilencedetectPreprocessDenoise: boolean;
  defaultPauseSileroThreshold: number;
  defaultPauseSileroMinSilenceSeconds: number;
  defaultPauseSileroMinSpeechSeconds: number;
  defaultPauseSileroPreprocessDenoise: boolean;
  defaultDpdfnetAttnLimitDb: number;
  defaultPitchHumMode: PitchHumMode;
  defaultRepeatPauseSeconds: number;
  defaultSizeReductionMode: SizeReductionMode;
  defaultSizeReductionBitrateKbps: number;
  defaultSizeReductionSampleRateHz: number;
  defaultSizeReductionChannels: number;
  defaultSpeedStep: number;
  defaultVoiceRecordingCountdownSeconds: number;
  defaultVolumeStepDb: number;
  denoiseAlgorithm: DenoiseAlgorithm;
  denoiseEdited: boolean;
  dpdfnetAttnLimitDb: number;
  dpdfnetEdited: boolean;
  graphConnectShortDropoutsMs: number;
  graphEdited: boolean;
  graphRecordingCondition: GraphRecordingCondition;
  graphSmoothness: GraphSmoothness;
  graphVoiceLock: GraphVoiceLock;
  graphVoiceRange: GraphVoiceRange;
  outputFormat: OutputFormatValue;
  outputFormatEdited: boolean;
  pauseAggressiveness: "gentle" | "normal" | "aggressive";
  pauseDetectionAlgorithm: PauseDetectionAlgorithm;
  pauseSilencedetectThresholdDb: number;
  pauseSilencedetectMinSilenceSeconds: number;
  pauseSilencedetectMinSpeechSeconds: number;
  pauseSilencedetectPreprocessDenoise: boolean;
  pauseSileroThreshold: number;
  pauseSileroMinSilenceSeconds: number;
  pauseSileroMinSpeechSeconds: number;
  pauseSileroPreprocessDenoise: boolean;
  pauseEdited: boolean;
  pitchHumEdited: boolean;
  pitchHumMode: PitchHumMode;
  repeatPauseEdited: boolean;
  repeatPauseSeconds: number;
  shareEdited: boolean;
  shareTarget: "catbox" | "litterbox";
  sizeReductionEdited: boolean;
  sizeReductionMode: SizeReductionMode;
  sizeReductionBitrateKbps: number;
  sizeReductionSampleRateHz: number;
  sizeReductionChannels: number;
  speedEdited: boolean;
  speedStep: number;
  voiceRecordingCountdownEdited: boolean;
  voiceRecordingCountdownSeconds: number;
  volumeEdited: boolean;
  volumeStepDb: number;
}
