export interface Config {
  _config_version: number;
  enabled: boolean;
  debug_logging: boolean;
  show_ffmpeg_commands: boolean;
  manual_trim_small_ms: number;
  manual_trim_large_ms: number;
  speed_step: number;
  min_speed: number;
  max_speed: number;
  volume_step_db: number;
  min_volume_db: number;
  max_volume_db: number;
  edge_silence_threshold_db: number;
  edge_silence_min_ms: number;
  internal_pause_silence_threshold_db: number;
  internal_pause_threshold_ms: number;
  internal_pause_target_gap_ms: number;
  output_format: "mp3";
  ffmpeg_path: string;
  deep_filter_path: string;
  deep_filter_post_filter: boolean;
}

export interface DiagnosticsState {
  addon_id: string;
  collection_available: boolean;
}

export interface InitialState {
  config: Config;
  version: string;
  addon_dir: string;
  log_file_path: string;
  diagnostics: DiagnosticsState;
}

export interface AsyncProgressPayload {
  id: string;
  progress: number;
  message: string;
}

export interface AsyncDonePayload {
  id: string;
  ok: boolean;
  result?: unknown;
  error?: string;
}

export interface SaveErrorPayload {
  error: string;
}

export interface SupportReportResult {
  reportText: string;
}

export interface ShowLogFileResult {
  logFilePath: string;
}

export interface HealthReport {
  collection_available: boolean;
  deck_count: number;
  note_type_count: number;
  card_count: number;
  deep_filter?: {
    available: boolean;
    path: string;
    version: string;
    error: string;
  };
  sidon?: {
    available: boolean;
    path: string;
    model_dir: string;
    version: string;
    error: string;
  };
}
