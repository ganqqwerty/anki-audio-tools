import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  copySupportReport,
  encodeBridgeCommand,
  registerCallbacks,
  sendAsyncCmd,
  sendBridgeCommand,
  settingsCancel,
  settingsResetDefaults,
  settingsSave,
} from "../src/lib/bridge.js";
import {
  DenoiseAlgorithm,
  GraphRecordingCondition,
  GraphSmoothness,
  GraphVoiceLock,
  GraphVoiceRange,
  OutputFormat,
  PauseAggressiveness,
  PitchHumMode,
  VisibleEditorButton,
  type Config,
} from "../src/lib/types.js";

const pycmd = (globalThis as unknown as Record<string, ReturnType<typeof vi.fn>>)["pycmd"]!;
const config: Config = {
  _config_version: 17,
  enabled: true,
  debug_logging: false,
  show_ffmpeg_commands: false,
  repeat_playback_by_default: false,
  repeat_pause_seconds: 0,
  show_graph_by_default: false,
  visible_editor_buttons: [
    VisibleEditorButton.AqePlay,
    VisibleEditorButton.AqeAnalyze,
    VisibleEditorButton.AqeShowFile,
    VisibleEditorButton.AqeConvert,
    VisibleEditorButton.AqeTrimLeft,
    VisibleEditorButton.AqeTrimRight,
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
  ],
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
  output_format: OutputFormat.Mp3,
  ffmpeg_path: "",
  deep_filter_path: "",
  deep_filter_post_filter: true,
  dpdfnet_attn_limit_db: 12.0,
  denoise_algorithm: DenoiseAlgorithm.Standard,
  pitch_hum_mode: PitchHumMode.Direct,
  pause_aggressiveness: PauseAggressiveness.Normal,
};

describe("sendBridgeCommand", () => {
  it("forwards raw commands to pycmd", () => {
    sendBridgeCommand("test-command");
    expect(pycmd).toHaveBeenCalledWith("test-command");
  });
});

describe("encodeBridgeCommand", () => {
  it("wraps commands in the shared JSON envelope", () => {
    expect(encodeBridgeCommand("settings.cancel")).toBe('bridge:{"command":"settings.cancel"}');
    expect(JSON.parse(encodeBridgeCommand("settings.save", { enabled: true }).slice("bridge:".length))).toEqual({
      command: "settings.save",
      payload: { enabled: true },
    });
  });
});

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
  it("sends a copy_support_report payload", () => {
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
  });

  it("registers the supplied callbacks", () => {
    const onAsyncProgress = vi.fn();
    const onAsyncDone = vi.fn();
    const onSaveError = vi.fn();
    registerCallbacks({ onAsyncProgress, onAsyncDone, onSaveError });
    expect(window.onAsyncProgress).toBe(onAsyncProgress);
    expect(window.onAsyncDone).toBe(onAsyncDone);
    expect(window.onSaveError).toBe(onSaveError);
  });
});
