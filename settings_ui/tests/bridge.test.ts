import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  copySupportReport,
  registerCallbacks,
  sendAsyncCmd,
  sendBridgeCommand,
  settingsCancel,
  settingsResetDefaults,
  settingsSave,
} from "../src/lib/bridge.js";
import { DenoiseAlgorithm, OutputFormat, PauseAggressiveness, type Config } from "../src/lib/types.js";

const pycmd = (globalThis as unknown as Record<string, ReturnType<typeof vi.fn>>)["pycmd"]!;
const config: Config = {
  _config_version: 11,
  enabled: true,
  debug_logging: false,
  show_ffmpeg_commands: false,
  repeat_playback_by_default: false,
  repeat_pause_seconds: 0,
  show_graph_by_default: false,
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

describe("sendBridgeCommand", () => {
  it("forwards raw commands to pycmd", () => {
    sendBridgeCommand("test-command");
    expect(pycmd).toHaveBeenCalledWith("test-command");
  });
});

describe("settingsSave", () => {
  it("sends a settings_save payload", () => {
    settingsSave(config);
    const call = pycmd.mock.calls[0]?.[0] ?? "";
    expect(call).toMatch(/^settings_save:/);
    expect(JSON.parse(call.slice("settings_save:".length))).toEqual(config);
  });
});

describe("lifecycle commands", () => {
  it("sends settings_cancel", () => {
    settingsCancel();
    expect(pycmd).toHaveBeenCalledWith("settings_cancel");
  });

  it("sends settings_reset_defaults", () => {
    settingsResetDefaults();
    expect(pycmd).toHaveBeenCalledWith("settings_reset_defaults");
  });
});

describe("sendAsyncCmd", () => {
  it("serializes id, op, and payload", () => {
    sendAsyncCmd("job-1", "health_check", { config });
    const call = pycmd.mock.calls[0]?.[0] ?? "";
    expect(call).toMatch(/^async_cmd:/);
    expect(JSON.parse(call.slice("async_cmd:".length))).toEqual({
      id: "job-1",
      op: "health_check",
      payload: {
        config,
      },
    });
  });
});

describe("copySupportReport", () => {
  it("sends a copy_support_report payload", () => {
    copySupportReport("support text");
    const call = pycmd.mock.calls[0]?.[0] ?? "";
    expect(call).toMatch(/^copy_support_report:/);
    expect(JSON.parse(call.slice("copy_support_report:".length))).toEqual({
      text: "support text",
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
