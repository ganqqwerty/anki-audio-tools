import { DEFAULT_EDITOR_BUTTON_MODES } from "../src/lib/editor-toolbar-buttons.js";
import {
  DenoiseAlgorithm,
  Direction,
  GraphRecordingCondition,
  GraphSmoothness,
  GraphVoiceLock,
  GraphVoiceRange,
  OutputFormat,
  PauseAggressiveness,
  PauseDetectionAlgorithm,
  Phase,
  PitchHumMode,
  ShareTarget,
  VisibleEditorButton,
} from "../src/lib/types.js";
import { pycmdMock as installedPycmdMock } from "./setup.js";

export const defaultConfig = {
  _config_version: 1,
  enabled: true,
  debug_logging: false,
  show_ffmpeg_commands: false,
  repeat_playback_by_default: true,
  repeat_pause_seconds: 0,
  voice_recording_countdown_seconds: 3,
  share_target: ShareTarget.Litterbox,
  show_graph_by_default: true,
  visible_editor_buttons: [
    VisibleEditorButton.AqePlay,
    VisibleEditorButton.AqeAnalyze,
    VisibleEditorButton.AqeShowFile,
    VisibleEditorButton.AqeShare,
    VisibleEditorButton.AqeRemovePauses,
    VisibleEditorButton.AqeDenoiseStandard,
    VisibleEditorButton.AqeSlower,
    VisibleEditorButton.AqeFaster,
    VisibleEditorButton.AqeUndo,
    VisibleEditorButton.AqeRedo,
    VisibleEditorButton.AqeSettings,
  ],
  editor_button_modes: { ...DEFAULT_EDITOR_BUTTON_MODES },
  graph_voice_range: GraphVoiceRange.General,
  graph_recording_condition: GraphRecordingCondition.Auto,
  graph_smoothness: GraphSmoothness.VerySmooth,
  graph_connect_short_dropouts_ms: 240,
  graph_voice_lock: GraphVoiceLock.Balanced,
  speed_step: 1.5,
  min_speed: 0.2,
  max_speed: 5.0,
  volume_step_db: 15.0,
  min_volume_db: -40.0,
  max_volume_db: 40.0,
  pause_silencedetect_threshold_db: -45,
  pause_silencedetect_min_silence_seconds: 0.3,
  pause_silencedetect_min_speech_seconds: 0.1,
  pause_silencedetect_preprocess_denoise: true,
  pause_silero_threshold: 0.5,
  pause_silero_min_silence_seconds: 0.45,
  pause_silero_min_speech_seconds: 0.1,
  pause_silero_preprocess_denoise: false,
  output_format: OutputFormat.Mp3,
  ffmpeg_path: "/opt/homebrew/bin/ffmpeg",
  deep_filter_post_filter: true,
  dpdfnet_attn_limit_db: 12.0,
  denoise_algorithm: DenoiseAlgorithm.Standard,
  pitch_hum_mode: PitchHumMode.Direct,
  pause_aggressiveness: PauseAggressiveness.Normal,
  pause_detection_algorithm: PauseDetectionAlgorithm.Silencedetect,
};

export function pycmdMock(): typeof installedPycmdMock {
  return installedPycmdMock;
}

export function bridgeEnvelopes(): Array<{ command: string; payload?: unknown }> {
  return pycmdMock()
    .mock.calls.map(([command]) => command)
    .filter((command) => command.startsWith("bridge:"))
    .map((command) => JSON.parse(command.slice("bridge:".length)) as { command: string; payload?: unknown });
}

export function bridgePayload<T>(commandName: string): T {
  const envelope = bridgeEnvelopes().find((item) => item.command === commandName);
  if (!envelope) {
    throw new Error(`Bridge command not found: ${commandName}`);
  }
  return envelope.payload as T;
}

export function asyncPayload<T>(op: string): T {
  const envelope = bridgeEnvelopes().find(
    (item) => item.command === "settings.async" && (item.payload as { op?: string }).op === op,
  );
  if (!envelope) {
    throw new Error(`Async operation not found: ${op}`);
  }
  return envelope.payload as T;
}

export function setInitialState(config = defaultConfig, messages: Record<string, string> = {}): void {
  window.__INITIAL_STATE__ = {
    config,
    version: "0.1.0",
    addon_dir: "/tmp/addon",
    log_file_path: "/tmp/addon/log.txt",
    locale: "en",
    direction: Direction.LTR,
    messages,
    diagnostics: {
      addon_id: "anki_audio_quick_editor",
      collection_available: true,
      release_info: { commit_hash: "", commit_message: "" },
      runtime: {
        phase: Phase.Missing,
        runtime_manifest_id: "",
        platform: "",
        runtime_root: "",
        progress: 0,
        message: "",
        error: "",
      },
    },
  };
}
