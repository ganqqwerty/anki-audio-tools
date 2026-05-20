import {
  DenoiseAlgorithm,
  Direction,
  GraphRecordingCondition,
  GraphSmoothness,
  GraphVoiceLock,
  GraphVoiceRange,
  OutputFormat,
  PauseAggressiveness,
} from "$lib/types.js";
import type { Config, InitialState } from "$lib/types.js";

export type SettingsTab = "general" | "diagnostics";

export const FALLBACK_INITIAL_STATE: InitialState = {
  config: {
    _config_version: 12,
    enabled: true,
    debug_logging: false,
    show_ffmpeg_commands: false,
    repeat_playback_by_default: false,
    repeat_pause_seconds: 0,
    show_graph_by_default: false,
    graph_voice_range: GraphVoiceRange.General,
    graph_recording_condition: GraphRecordingCondition.Auto,
    graph_smoothness: GraphSmoothness.VerySmooth,
    graph_connect_short_dropouts_ms: 240,
    graph_voice_lock: GraphVoiceLock.Balanced,
    manual_trim_small_ms: 100,
    manual_trim_large_ms: 500,
    speed_step: 0.05,
    min_speed: 0.75,
    max_speed: 1.5,
    volume_step_db: 3.0,
    min_volume_db: -24.0,
    max_volume_db: 24.0,
    internal_pause_silence_threshold_db: -45,
    internal_pause_threshold_ms: 300,
    internal_pause_target_gap_ms: 100,
    pause_aggressiveness: PauseAggressiveness.Normal,
    output_format: OutputFormat.Mp3,
    ffmpeg_path: "",
    deep_filter_path: "",
    deep_filter_post_filter: true,
    denoise_algorithm: DenoiseAlgorithm.Standard,
  },
  version: "",
  addon_dir: "",
  log_file_path: "",
  diagnostics: {
    addon_id: "",
    collection_available: false,
  },
  locale: "en",
  direction: Direction.LTR,
  messages: {},
};

export function initialSettingsState(): InitialState {
  return window.__INITIAL_STATE__ ?? FALLBACK_INITIAL_STATE;
}

export function cloneConfig(config: Config): Config {
  return structuredClone(config);
}

export function saveConfigPayload(config: Config): Config {
  return { ...config, enabled: true };
}

export function messageFromError(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}
