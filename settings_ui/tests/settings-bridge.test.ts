import { beforeEach, describe, expect, it, vi } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { cwd } from "node:process";

import {
  copySupportReport,
  registerCallbacks,
  sendAsyncCmd,
  settingsCancel,
  settingsCheckMedia,
  settingsOpenRuntimeInstaller,
  settingsResetDefaults,
  settingsSave,
} from "../src/settings/bridge.js";
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
import { DEFAULT_EDITOR_BUTTON_MODES as DEFAULT_BUTTON_MODES } from "../src/lib/editor-toolbar-buttons.js";

const pycmd = (globalThis as unknown as Record<string, ReturnType<typeof vi.fn>>)["pycmd"]!;
const config: Config = {
  _config_version: 2,
  enabled: true,
  debug_logging: true,
  show_ffmpeg_commands: false,
  enable_reviewer_editor: true,
  repeat_playback_by_default: true,
  repeat_pause_seconds: 0,
  voice_recording_countdown_seconds: 0,
  share_target: ShareTarget.Litterbox,
  show_graph_by_default: true,
  selection_marker_shift_buttons_enabled: false,
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
  editor_button_modes: { ...DEFAULT_BUTTON_MODES },
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

describe("settingsSave", () => {
  it("sends a settings.save payload", () => {
    settingsSave(config);
    const call = pycmd.mock.calls[0]?.[0] ?? "";
    const envelope = JSON.parse(call.slice("bridge:".length));
    expect(envelope).toEqual({ command: "settings.save", payload: config });
  });
});

describe("lifecycle commands", () => {
  it("sends settings.cancel", () => {
    settingsCancel();
    expect(pycmd).toHaveBeenCalledWith('bridge:{"command":"settings.cancel"}');
  });

  it("sends settings.reset_defaults", () => {
    settingsResetDefaults();
    expect(pycmd).toHaveBeenCalledWith('bridge:{"command":"settings.reset_defaults"}');
  });

  it("sends settings.check_media", () => {
    settingsCheckMedia();
    expect(pycmd).toHaveBeenCalledWith('bridge:{"command":"settings.check_media"}');
  });

  it("sends settings.open_runtime_installer", () => {
    settingsOpenRuntimeInstaller();
    expect(pycmd).toHaveBeenCalledWith('bridge:{"command":"settings.open_runtime_installer"}');
  });
});

describe("sendAsyncCmd", () => {
  it("serializes id, op, and payload", () => {
    sendAsyncCmd("job-1", "health_check", { config });
    const call = pycmd.mock.calls[0]?.[0] ?? "";
    expect(JSON.parse(call.slice("bridge:".length))).toEqual({
      command: "settings.async",
      payload: {
        id: "job-1",
        op: "health_check",
        payload: {
          config,
        },
      },
    });
  });
});

describe("copySupportReport", () => {
  it("sends a support.copy_report payload", () => {
    copySupportReport("support text");
    const call = pycmd.mock.calls[0]?.[0] ?? "";
    expect(JSON.parse(call.slice("bridge:".length))).toEqual({
      command: "support.copy_report",
      payload: {
        text: "support text",
      },
    });
  });
});

describe("registerCallbacks", () => {
  beforeEach(() => {
    delete window.onAsyncProgress;
    delete window.onAsyncDone;
    delete window.onSaveError;
    delete window.onRuntimeInstallerClosed;
  });

  it("registers the supplied callbacks", () => {
    const onAsyncProgress = vi.fn();
    const onAsyncDone = vi.fn();
    const onSaveError = vi.fn();
    const onRuntimeInstallerClosed = vi.fn();
    registerCallbacks({ onAsyncProgress, onAsyncDone, onSaveError, onRuntimeInstallerClosed });
    expect(window.onAsyncProgress).toBe(onAsyncProgress);
    expect(window.onAsyncDone).toBe(onAsyncDone);
    expect(window.onSaveError).toBe(onSaveError);
    expect(window.onRuntimeInstallerClosed).toBe(onRuntimeInstallerClosed);
  });
});

const projectRoot = cwd();

it("keeps settings command names out of the shared bridge transport module", () => {
  const source = readFileSync(join(projectRoot, "src/lib/bridge-transport.ts"), "utf8");

  expect(source).not.toContain("settings.save");
  expect(source).not.toContain("settings.cancel");
  expect(source).not.toContain("settings.reset_defaults");
  expect(source).not.toContain("settings.check_media");
  expect(source).not.toContain("settings.open_runtime_installer");
  expect(source).not.toContain("settings.async");
  expect(source).not.toContain("support.copy_report");
});
