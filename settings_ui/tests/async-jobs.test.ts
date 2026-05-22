/**
 * Tests for src/lib/async-jobs.ts
 *
 * Verifies that startAsyncOp:
 *  - sends the correct async_cmd pycmd
 *  - returns a Promise that resolves when onAsyncDone fires with ok=true
 *  - returns a Promise that rejects when onAsyncDone fires with ok=false
 *  - calls the progress callback on onAsyncProgress
 */

import { afterEach, describe, expect, it, vi } from "vitest";
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
  VisibleEditorButton,
} from "../src/lib/types.js";

const pycmd = (globalThis as unknown as Record<string, ReturnType<typeof vi.fn>>)["pycmd"]!;
const config = {
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
  it("calls pycmd with async_cmd containing op and payload", () => {
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
