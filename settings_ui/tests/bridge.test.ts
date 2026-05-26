import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  copySupportReport,
  encodeBridgeCommand,
  registerCallbacks,
  sendAsyncCmd,
  sendBridgeCommand,
  settingsCancel,
  settingsCheckMedia,
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
  ShareTarget,
  VisibleEditorButton,
  type Config,
} from "../src/lib/types.js";
import { DEFAULT_EDITOR_BUTTON_MODES as DEFAULT_BUTTON_MODES } from "../src/lib/editor-toolbar-buttons.js";

const pycmd = (globalThis as unknown as Record<string, ReturnType<typeof vi.fn>>)["pycmd"]!;
const config: Config = {
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
  editor_button_modes: { ...DEFAULT_BUTTON_MODES },
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
  internal_pause_silence_threshold_db: -45,
  internal_pause_threshold_ms: 300,
  internal_pause_target_gap_ms: 100,
  output_format: OutputFormat.Mp3,
  ffmpeg_path: "/opt/homebrew/bin/ffmpeg",
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

  it("retries until pycmd becomes available", () => {
    vi.useFakeTimers();
    const original = globalThis.pycmd;
    globalThis.pycmd = undefined;

    try {
      sendBridgeCommand("delayed-command");
      expect(pycmd).not.toHaveBeenCalled();

      globalThis.pycmd = pycmd;
      vi.advanceTimersByTime(25);

      expect(pycmd).toHaveBeenCalledWith("delayed-command");
    } finally {
      globalThis.pycmd = original;
      vi.useRealTimers();
    }
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

  it("sends settings.check_media", () => {
    settingsCheckMedia();
    expect(pycmd).toHaveBeenCalledWith('bridge:{"command":"settings.check_media"}');
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
