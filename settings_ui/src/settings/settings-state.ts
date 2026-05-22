import {
  DenoiseAlgorithm,
  Direction,
  GraphRecordingCondition,
  GraphSmoothness,
  GraphVoiceLock,
  GraphVoiceRange,
  OutputFormat,
  PauseAggressiveness,
  PitchHumMode,
  VisibleEditorButton,
} from "$lib/types.js";
import { DEFAULT_EDITOR_BUTTON_MODES } from "$lib/editor-toolbar-buttons.js";
import type { Config, InitialState } from "$lib/types.js";

export type SettingsTab = "general" | "diagnostics";

export const DEFAULT_VISIBLE_EDITOR_BUTTONS = [
  VisibleEditorButton.AqePlay,
  VisibleEditorButton.AqeAnalyze,
  VisibleEditorButton.AqeShowFile,
  VisibleEditorButton.AqeShare,
  VisibleEditorButton.AqeConvert,
  VisibleEditorButton.AqeRemovePauses,
  VisibleEditorButton.AqeDenoiseStandard,
  VisibleEditorButton.AqePitchHum,
  VisibleEditorButton.AqeSlower,
  VisibleEditorButton.AqeFaster,
  VisibleEditorButton.AqeVolumeDown,
  VisibleEditorButton.AqeVolumeUp,
  VisibleEditorButton.AqeUndo,
  VisibleEditorButton.AqeRedo,
  VisibleEditorButton.AqeSettings,
] as const satisfies readonly VisibleEditorButton[];

export const FALLBACK_INITIAL_STATE: InitialState = {
  config: {
    _config_version: 18,
    enabled: true,
    debug_logging: false,
    show_ffmpeg_commands: false,
    repeat_playback_by_default: false,
    repeat_pause_seconds: 0,
    show_graph_by_default: false,
    visible_editor_buttons: [...DEFAULT_VISIBLE_EDITOR_BUTTONS],
    editor_button_modes: { ...DEFAULT_EDITOR_BUTTON_MODES },
    graph_voice_range: GraphVoiceRange.General,
    graph_recording_condition: GraphRecordingCondition.Auto,
    graph_smoothness: GraphSmoothness.VerySmooth,
    graph_connect_short_dropouts_ms: 240,
    graph_voice_lock: GraphVoiceLock.Balanced,
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
    dpdfnet_attn_limit_db: 12.0,
    denoise_algorithm: DenoiseAlgorithm.Standard,
    pitch_hum_mode: PitchHumMode.Direct,
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
