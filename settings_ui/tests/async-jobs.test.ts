/**
 * Tests for src/lib/async-jobs.ts
 *
 * Verifies that startAsyncOp:
 *  - sends the correct settings.async bridge command
 *  - returns a Promise that resolves when onAsyncDone fires with ok=true
 *  - returns a Promise that rejects when onAsyncDone fires with ok=false
 *  - calls the progress callback on onAsyncProgress
 */

import { afterEach, describe, expect, it, vi } from "vitest";
import { DEFAULT_EDITOR_BUTTON_MODES } from "../src/lib/editor-toolbar-buttons.js";
import {
  _clearPendingForTest,
  handleAsyncDone,
  handleAsyncProgress,
  startAsyncOp,
} from "../src/lib/async-jobs.js";
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
} from "../src/lib/types.js";

const pycmd = (globalThis as unknown as Record<string, ReturnType<typeof vi.fn>>)["pycmd"]!;
const config = {
  _config_version: 1,
  enabled: true,
  debug_logging: false,
  show_ffmpeg_commands: false,
  repeat_playback_by_default: true,
  repeat_pause_seconds: 0,
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

afterEach(() => {
  _clearPendingForTest();
});

function asyncCommandAt(index: number): { id: string; op: string; payload: unknown } {
  const command = pycmd.mock.calls[index]?.[0] ?? "";
  const envelope = JSON.parse(String(command).slice("bridge:".length)) as {
    command: string;
    payload: { id: string; op: string; payload: unknown };
  };
  expect(envelope.command).toBe("settings.async");
  return envelope.payload;
}

describe("startAsyncOp", () => {
  it("calls pycmd with settings.async containing op and payload", () => {
    void startAsyncOp("health_check", { config });
    const call = pycmd.mock.calls[0]?.[0] ?? "";
    expect(call).toMatch(/^bridge:/);
    const parsed = asyncCommandAt(0);
    expect(parsed.op).toBe("health_check");
    expect(parsed.payload).toEqual({ config });
  });

  it("generates a unique id for each call", () => {
    void startAsyncOp("health_check", { config });
    void startAsyncOp("support_report", { config });
    const id1 = asyncCommandAt(0).id;
    const id2 = asyncCommandAt(1).id;
    expect(id1).not.toBe(id2);
  });

  it("promise resolves with result when onAsyncDone fires ok=true", async () => {
    const promise = startAsyncOp("health_check", { config });
    const id = asyncCommandAt(0).id;

    handleAsyncDone({
      id,
      ok: true,
      result: {
        collection_available: true,
        deck_count: 1,
        note_type_count: 2,
        card_count: 3,
      },
    });

    const result = await promise;
    expect(result.card_count).toBe(3);
  });

  it("promise rejects with error when onAsyncDone fires ok=false", async () => {
    const promise = startAsyncOp("health_check", { config });
    const id = asyncCommandAt(0).id;

    handleAsyncDone({ id, ok: false, error: "API timeout" });

    await expect(promise).rejects.toThrow("API timeout");
  });

  it("calls onProgress callback with pct and message", () => {
    const onProgress = vi.fn();
    void startAsyncOp("show_log_file", {}, onProgress);
    const id = asyncCommandAt(0).id;

    handleAsyncProgress({ id, progress: 50, message: "Fetching…" });
    expect(onProgress).toHaveBeenCalledWith(50, "Fetching…");
  });

  it("ignores onAsyncDone for unknown job ids", () => {
    expect(() => {
      handleAsyncDone({ id: "unknown-id", ok: true, result: {} });
    }).not.toThrow();
  });

  it("cleans up pending map after resolution", async () => {
    const promise = startAsyncOp("support_report", { config });
    const id = asyncCommandAt(0).id;

    handleAsyncDone({ id, ok: true, result: { reportText: "support" } });
    await promise;

    // A second done with the same ID should be silently ignored
    expect(() => {
      handleAsyncDone({ id, ok: false, error: "late" });
    }).not.toThrow();
  });

  it("rejects when an async result payload does not match the operation", async () => {
    const promise = startAsyncOp("show_log_file", {});
    const id = asyncCommandAt(0).id;

    handleAsyncDone({ id, ok: true, result: { reportText: "wrong shape" } });

    await expect(promise).rejects.toThrow("Invalid async result payload for show_log_file");
  });
});

describe("handleAsyncProgress", () => {
  it("silently ignores unknown job ids", () => {
    expect(() => {
      handleAsyncProgress({ id: "no-such-id", progress: 10, message: "x" });
    }).not.toThrow();
  });
});
