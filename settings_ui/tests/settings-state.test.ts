import { describe, expect, it } from "vitest";

import { saveConfigPayload } from "../src/settings/settings-state.js";
import {
  DenoiseAlgorithm,
  GraphRecordingCondition,
  GraphSmoothness,
  GraphVoiceLock,
  GraphVoiceRange,
  OutputFormat,
  PauseAggressiveness,
  type Config,
} from "../src/lib/types.js";

const config: Config = {
  _config_version: 12,
  enabled: false,
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
  output_format: OutputFormat.Mp3,
  ffmpeg_path: "",
  deep_filter_path: "",
  deep_filter_post_filter: true,
  denoise_algorithm: DenoiseAlgorithm.Standard,
  pause_aggressiveness: PauseAggressiveness.Normal,
};

describe("settings state helpers", () => {
  it("forces inline editor controls on when building a save payload", () => {
    expect(saveConfigPayload(config)).toMatchObject({ enabled: true });
  });
});
