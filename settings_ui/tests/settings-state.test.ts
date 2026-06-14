import { describe, expect, it } from "vitest";

import { DEFAULT_EDITOR_BUTTON_MODES } from "../src/lib/editor-toolbar-buttons.js";
import { saveConfigPayload } from "../src/settings/settings-state.js";
import {
  DenoiseAlgorithm,
  GraphRecordingCondition,
  GraphSmoothness,
  GraphVoiceLock,
  GraphVoiceRange,
  OutputFormat,
  PauseAggressiveness,
  PauseDetectionAlgorithm,
  PitchHumMode,
  ShareTarget,
  VisibleEditorButton,
  type Config,
} from "../src/lib/types.js";

const config: Config = {
  _config_version: 2,
  enabled: false,
  debug_logging: true,
  show_ffmpeg_commands: false,
  enable_reviewer_editor: true,
  repeat_playback_by_default: true,
  repeat_pause_seconds: 0,
  chorusing_pause_seconds: 0,
  chorusing_auto_advance_by_default: false,
  chorusing_auto_advance_repeats: 3,
  chorusing_marker_interval_ms: 500,
  voice_recording_countdown_seconds: 0,
  share_target: ShareTarget.Litterbox,
  show_graph_by_default: true,
  selection_marker_shift_buttons_enabled: false,
  editor_history_size: 100,
  visible_editor_buttons: [
    VisibleEditorButton.AqePlay,
    VisibleEditorButton.AqeAnalyze,
    VisibleEditorButton.AqeChorusingPractice,
    VisibleEditorButton.AqeChorusingNext,
    VisibleEditorButton.AqeChorusingPrevious,
    VisibleEditorButton.AqeShowFile,
    VisibleEditorButton.AqeShare,
    VisibleEditorButton.AqePreset,
    VisibleEditorButton.AqeReduceSize,
    VisibleEditorButton.AqeRemovePauses,
    VisibleEditorButton.AqeDenoiseStandard,
    VisibleEditorButton.AqeSlower,
    VisibleEditorButton.AqeFaster,
    VisibleEditorButton.AqeDeleteSelection,
    VisibleEditorButton.AqeDeleteREST,
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
  audio_processing_presets: [],
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
  size_reduction_mode: PauseAggressiveness.Normal,
  size_reduction_bitrate_kbps: 64,
  size_reduction_sample_rate_hz: 32000,
  size_reduction_channels: 1,
  ffmpeg_path: "/opt/homebrew/bin/ffmpeg",
  deep_filter_post_filter: true,
  dpdfnet_attn_limit_db: 12.0,
  denoise_algorithm: DenoiseAlgorithm.Standard,
  pitch_hum_mode: PitchHumMode.Direct,
  pause_aggressiveness: PauseAggressiveness.Normal,
  pause_detection_algorithm: PauseDetectionAlgorithm.Silencedetect,
};

describe("settings state helpers", () => {
  it("forces inline editor controls on when building a save payload", () => {
    expect(saveConfigPayload(config)).toMatchObject({ enabled: true });
  });

  it("preserves the selection marker shift toggle when building a save payload", () => {
    expect(saveConfigPayload({
      ...config,
      selection_marker_shift_buttons_enabled: true,
    }).selection_marker_shift_buttons_enabled).toBe(true);
  });

  it("preserves editor history size when building a save payload", () => {
    expect(saveConfigPayload({
      ...config,
      editor_history_size: 25,
    }).editor_history_size).toBe(25);
  });
});
