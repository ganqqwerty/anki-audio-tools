export type {
  AsyncDonePayload,
  AsyncProgressPayload,
  AudioProcessingPreset,
  AudioProcessingPresetGraph,
  AudioProcessingPresetGraphParameters,
  AudioProcessingPresetParameters,
  AudioProcessingPresetStep,
  BatchErrorPayload,
  BatchFieldGroup,
  BatchFinishPayload,
  BatchInitialState,
  BatchLogPayload,
  BatchOperationOption,
  BatchOperationParameters,
  BatchProcessingPresetOption,
  BatchProgressPayload,
  BatchStartRequest,
  Config,
  CopySupportReportPayload,
  DiagnosticsState,
  ExternalToolHealth,
  FrontendLogPayload,
  HealthReport,
  InitialState,
  ProsodyPayload,
  RuntimeStatus,
  SaveErrorPayload,
  ShowLogFileResult,
  SupportReportResult,
} from "./generated/contracts.js";
export {
  BatchOperationName,
  BatchParameterKind,
  BatchParameterName,
  BatchPauseAggressiveness,
  BatchPauseDetectionAlgorithm,
  BatchPauseAggressiveness as PauseAggressiveness,
  BatchPauseDetectionAlgorithm as PauseDetectionAlgorithm,
  DenoiseAlgorithm,
  Direction,
  EditorButtonMode,
  GraphRecordingCondition,
  GraphSmoothness,
  GraphVoiceLock,
  GraphVoiceRange,
  Level,
  Operation,
  OutputFormat,
  Phase,
  PitchHumMode,
  ShareTarget,
  VisibleEditorButton,
} from "./generated/contracts.js";

import type {
  Config,
  HealthReport,
  RuntimeStatus,
  ShowLogFileResult,
  SupportReportResult,
} from "./generated/contracts.js";

export type AsyncOperationName =
  | "health_check"
  | "support_report"
  | "show_log_file"
  | "runtime_status"
  | "runtime_install";

export interface AsyncOperationPayloads {
  health_check: { config: Config };
  support_report: { config: Config };
  show_log_file: Record<string, never>;
  runtime_status: Record<string, never>;
  runtime_install: Record<string, never>;
}

export interface AsyncOperationResults {
  health_check: HealthReport;
  support_report: SupportReportResult;
  show_log_file: ShowLogFileResult;
  runtime_status: RuntimeStatus;
  runtime_install: RuntimeStatus;
}

export type AsyncOperationResult =
  AsyncOperationResults[keyof AsyncOperationResults];
