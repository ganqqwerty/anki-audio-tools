export type {
  AsyncDonePayload,
  AsyncProgressPayload,
  Config,
  CopySupportReportPayload,
  DiagnosticsState,
  ExternalToolHealth,
  FrontendLogPayload,
  HealthReport,
  InitialState,
  ProsodyPayload,
  SaveErrorPayload,
  ShowLogFileResult,
  SupportReportResult,
} from "./generated/contracts.js";
export {
  DenoiseAlgorithm,
  Direction,
  GraphRecordingCondition,
  GraphSmoothness,
  GraphVoiceLock,
  GraphVoiceRange,
  Level,
  OutputFormat,
  PauseAggressiveness,
} from "./generated/contracts.js";

import type {
  Config,
  HealthReport,
  ShowLogFileResult,
  SupportReportResult,
} from "./generated/contracts.js";

export type AsyncOperationName =
  | "health_check"
  | "support_report"
  | "show_log_file";

export interface AsyncOperationPayloads {
  health_check: { config: Config };
  support_report: { config: Config };
  show_log_file: Record<string, never>;
}

export interface AsyncOperationResults {
  health_check: HealthReport;
  support_report: SupportReportResult;
  show_log_file: ShowLogFileResult;
}

export type AsyncOperationResult =
  AsyncOperationResults[keyof AsyncOperationResults];
