import { fireEvent, render, screen, waitFor } from "@testing-library/svelte";
import { describe, expect, it, vi } from "vitest";

import BatchApp from "../src/batch/BatchApp.svelte";
import { PRODUCT_LINKS } from "../src/lib/product-links.js";
import {
  BatchOperationName,
  BatchParameterKind,
  BatchParameterName,
  BatchPauseAggressiveness,
  BatchPauseDetectionAlgorithm,
  DenoiseAlgorithm,
  Direction,
  OutputFormat,
} from "../src/lib/types.js";

function setInitialState(): void {
  window.__AQE_BATCH_INITIAL_STATE__ = {
    note_count: 2,
    operations: [
      {
        operation: BatchOperationName.Graph,
        label: "Graph",
        requires_target_field: true,
        parameter_kind: BatchParameterKind.None,
        parameter_name: BatchParameterName.None,
      },
      {
        operation: BatchOperationName.Convert,
        label: "Convert",
        requires_target_field: false,
        parameter_kind: BatchParameterKind.Format,
        parameter_name: BatchParameterName.TargetFormat,
      },
      {
        operation: BatchOperationName.RemovePauses,
        label: "Shorten Pauses",
        requires_target_field: false,
        parameter_kind: BatchParameterKind.Pause,
        parameter_name: BatchParameterName.PauseAggressiveness,
      },
      {
        operation: BatchOperationName.Faster,
        label: "Faster",
        requires_target_field: false,
        parameter_kind: BatchParameterKind.Speed,
        parameter_name: BatchParameterName.SpeedStep,
      },
      {
        operation: BatchOperationName.Denoise,
        label: "Denoise",
        requires_target_field: false,
        parameter_kind: BatchParameterKind.Denoise,
        parameter_name: BatchParameterName.DenoiseAlgorithm,
      },
      {
        operation: BatchOperationName.VolumeUp,
        label: "Volume +",
        requires_target_field: false,
        parameter_kind: BatchParameterKind.Volume,
        parameter_name: BatchParameterName.VolumeStepDB,
      },
    ],
    field_groups: [{ notetype_name: "Basic", fields: ["Audio", "Image"] }],
    defaults: {
      speed_step: 0.1,
      volume_step_db: 6,
      pause_aggressiveness: BatchPauseAggressiveness.Aggressive,
      pause_detection_algorithm: BatchPauseDetectionAlgorithm.Silencedetect,
      pause_silencedetect_threshold_db: -52,
      pause_silencedetect_min_silence_seconds: 0.14,
      pause_silencedetect_min_speech_seconds: 0.04,
      pause_silencedetect_preprocess_denoise: true,
      pause_silero_threshold: 0.85,
      pause_silero_min_silence_seconds: 0.15,
      pause_silero_min_speech_seconds: 0.04,
      pause_silero_preprocess_denoise: false,
      denoise_algorithm: DenoiseAlgorithm.Standard,
      dpdfnet_attn_limit_db: 12,
      output_format: OutputFormat.Mp3,
    },
    locale: "en",
    direction: Direction.LTR,
    messages: {},
  };
}

function pycmdMock(): ReturnType<typeof vi.fn> {
  return (globalThis as unknown as Record<string, ReturnType<typeof vi.fn>>)["pycmd"]!;
}

describe("BatchApp", () => {
  it("renders controls and sends a graph start request", async () => {
    setInitialState();
    render(BatchApp);

    expect(screen.getByText("Choose an operation and fields for the selected notes.")).toBeInTheDocument();
    expect(screen.getByLabelText("Target field")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "GitHub Pages" })).toHaveAttribute(
      "href",
      PRODUCT_LINKS.githubPages,
    );
    expect(screen.getByRole("link", { name: "See video" })).toHaveAttribute(
      "href",
      PRODUCT_LINKS.editorVideos.batchProcessing,
    );
    expect(screen.getByRole("link", { name: "Report a bug" })).toHaveAttribute(
      "href",
      PRODUCT_LINKS.bugReport,
    );
    expect(screen.getByRole("link", { name: "Request an idea" })).toHaveAttribute(
      "href",
      PRODUCT_LINKS.ideaRequest,
    );
    expect(screen.queryByRole("button", { name: "Cancel" })).not.toBeInTheDocument();

    await fireEvent.click(screen.getByRole("button", { name: "Start" }));

    const call = pycmdMock().mock.calls.find(([command]) => String(command).includes('"batch.start"'))?.[0] as string;
    const envelope = JSON.parse(call.slice("bridge:".length));
    expect(envelope.command).toBe("batch.start");
    expect(envelope.payload).toEqual({
      operation: BatchOperationName.Graph,
      source_field: "Audio",
      target_field: "Audio",
      parameters: {},
    });
  });

  it("shows only operation-specific parameter controls", async () => {
    setInitialState();
    render(BatchApp);

    await fireEvent.change(screen.getByLabelText("Operation"), {
      target: { value: BatchOperationName.Faster },
    });
    expect(screen.queryByLabelText("Target field")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Speed factor")).toBeInTheDocument();

    await fireEvent.change(screen.getByLabelText("Operation"), {
      target: { value: BatchOperationName.Convert },
    });
    expect(screen.getByLabelText("Default convert format")).toBeInTheDocument();
    expect(screen.queryByLabelText("Target field")).not.toBeInTheDocument();

    await fireEvent.change(screen.getByLabelText("Operation"), {
      target: { value: BatchOperationName.RemovePauses },
    });
    expect(screen.getByTestId("batch-pause-aggressiveness-aggressive")).toBeInTheDocument();
    expect(screen.getByTestId("batch-pause-advanced-params")).toBeInTheDocument();
    expect(screen.getByTestId("batch-pause-threshold-help")).toBeInTheDocument();
    expect(screen.getByTestId("batch-pause-min-silence-seconds-help")).toBeInTheDocument();
    expect(screen.getByTestId("batch-pause-preprocess-denoise-help")).toBeInTheDocument();
    expect(screen.queryByLabelText("Speed factor")).not.toBeInTheDocument();

    await fireEvent.change(screen.getByLabelText("Operation"), {
      target: { value: BatchOperationName.Denoise },
    });
    expect(screen.getByTestId(`batch-denoise-algorithm-${DenoiseAlgorithm.Standard}`)).toBeInTheDocument();
    await fireEvent.click(screen.getByTestId(`batch-denoise-algorithm-${DenoiseAlgorithm.Dpdfnet}`));
    expect(screen.getByTestId("batch-dpdfnet-attn-limit-db")).toBeInTheDocument();
  });

  it("sends a convert start request with the selected format", async () => {
    setInitialState();
    render(BatchApp);

    await fireEvent.change(screen.getByTestId("batch-operation"), {
      target: { value: BatchOperationName.Convert },
    });
    await fireEvent.change(screen.getByTestId("batch-output-format"), {
      target: { value: OutputFormat.FLAC },
    });
    await fireEvent.click(screen.getByTestId("batch-start"));

    const call = pycmdMock().mock.calls.find(([command]) => String(command).includes('"batch.start"'))?.[0] as string;
    const envelope = JSON.parse(call.slice("bridge:".length));
    expect(envelope.payload).toEqual({
      operation: BatchOperationName.Convert,
      source_field: "Audio",
      target_field: null,
      parameters: { target_format: "flac" },
    });
  });

  it("updates progress, log, finish state, and copy log command", async () => {
    setInitialState();
    render(BatchApp);

    await fireEvent.click(screen.getByRole("button", { name: "Start" }));
    expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();
    window.onBatchLog?.({ line: "Starting batch" });
    window.onBatchProgress?.({
      processed: 1,
      total: 2,
      current_audio: "clip.mp3",
      failures: 0,
      message: "Processed 1/2 notes. Current audio: clip.mp3. Failures: 0.",
    });
    await fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(pycmdMock()).toHaveBeenCalledWith('bridge:{"command":"batch.cancel"}');

    window.onBatchFinish?.({
      processed: 2,
      total: 2,
      written: 1,
      skipped: 1,
      failures: 0,
      canceled: false,
      summary: "Completed: 2/2 notes processed, 1 written, 1 skipped, 0 failures.",
    });

    await waitFor(() => expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "2"));
    expect(screen.getByText("Starting batch")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Close" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Cancel" })).not.toBeInTheDocument();

    await fireEvent.click(screen.getByRole("button", { name: "Copy Log" }));
    expect(pycmdMock()).toHaveBeenCalledWith('bridge:{"command":"batch.copy_log"}');
  });
});
