import { fireEvent, render, screen, waitFor } from "@testing-library/svelte";
import { beforeEach, describe, expect, it, vi } from "vitest";

import BatchApp from "../src/batch/BatchApp.svelte";
import {
  AudioExportMode,
  BatchSurface,
  Direction,
} from "../src/lib/types.js";
import type { AudioExportInitialState } from "../src/lib/types.js";

const pycmd = (globalThis as unknown as Record<string, ReturnType<typeof vi.fn>>)["pycmd"]!;

function setAudioExportInitialState(): void {
  delete window.onBatchProgress;
  delete window.onBatchLog;
  delete window.onBatchFinish;
  delete window.onBatchError;
  delete window.onAudioExportDestination;
  delete window.onAudioExportProgress;
  delete window.onAudioExportLog;
  delete window.onAudioExportFinish;
  delete window.onAudioExportError;
  window.__AQE_BATCH_INITIAL_STATE__ = audioExportInitialState();
}

function audioExportInitialState(): AudioExportInitialState {
  return {
    surface: BatchSurface.AudioExport,
    note_count: 2,
    field_groups: [
      { notetype_name: "Basic", fields: ["Audio", "Image"] },
      { notetype_name: "Cloze", fields: ["SentenceAudio"] },
    ],
    default_field_selections: [{ notetype_name: "Basic", fields: ["Audio"] }],
    defaults: {
      mode: AudioExportMode.Zip,
      silence_between_clips_seconds: 1,
    },
    locale: "en",
    direction: Direction.LTR,
    messages: {},
  };
}

function bridgeEnvelopes(): Array<{ command: string; payload?: unknown }> {
  return pycmd.mock.calls
    .map(([command]) => String(command))
    .filter((command) => command.startsWith("bridge:"))
    .map((command) => JSON.parse(command.slice("bridge:".length)));
}

function bridgeEnvelope(command: string): { command: string; payload?: unknown } | undefined {
  return bridgeEnvelopes().find((envelope) => envelope.command === command);
}

describe("BatchApp audio export surface", () => {
  beforeEach(() => {
    setAudioExportInitialState();
  });

  it("renders export controls for the audio export surface", () => {
    const { container } = render(BatchApp);

    expect(screen.getByRole("heading", { name: "Export Audio" })).toBeInTheDocument();
    expect(screen.getByText("Export audio files from the selected notes. If you choose more than 50 audio files, this can get very, very slow.")).toBeInTheDocument();
    expect(screen.getByTestId("audio-export-controls")).toBeInTheDocument();
    expect(screen.getByLabelText("Destination")).toBeInTheDocument();
    expect(screen.queryByTestId("batch-operation")).not.toBeInTheDocument();
    expect(container.querySelector("label label")).toBeNull();
    expect(container.querySelector("label button")).toBeNull();
  });

  it("sends choose-destination with the current mode", async () => {
    render(BatchApp);

    await fireEvent.click(screen.getByRole("button", { name: "Choose..." }));

    expect(bridgeEnvelope("audio-export.choose-destination")).toEqual({
      command: "audio-export.choose-destination",
      payload: { mode: AudioExportMode.Zip },
    });
  });

  it("fills the readonly destination from the backend callback", async () => {
    render(BatchApp);

    await waitFor(() => expect(window.onAudioExportDestination).toBeTypeOf("function"));
    window.onAudioExportDestination?.({ destination_path: "/tmp/cards.zip" });

    await waitFor(() =>
      expect(screen.getByTestId("audio-export-destination")).toHaveValue("/tmp/cards.zip"),
    );
  });

  it("starts export with destination and selected fields", async () => {
    render(BatchApp);

    await waitFor(() => expect(window.onAudioExportDestination).toBeTypeOf("function"));
    window.onAudioExportDestination?.({ destination_path: "/tmp/cards.zip" });
    await fireEvent.click(screen.getByTestId("batch-start"));

    expect(screen.getByText("0/0")).toBeInTheDocument();
    expect(screen.getByText("Exported 0/0 audio files. Current audio: No audio. Failures: 0.")).toBeInTheDocument();
    expect(bridgeEnvelope("audio-export.start")).toEqual({
      command: "audio-export.start",
      payload: {
        mode: AudioExportMode.Zip,
        destination_path: "/tmp/cards.zip",
        field_selections: [{ notetype_name: "Basic", fields: ["Audio"] }],
        silence_between_clips_seconds: 1,
      },
    });
  });

  it("cancels the running audio export", async () => {
    render(BatchApp);

    await waitFor(() => expect(window.onAudioExportDestination).toBeTypeOf("function"));
    window.onAudioExportDestination?.({ destination_path: "/tmp/cards.zip" });
    await fireEvent.click(screen.getByTestId("batch-start"));
    await fireEvent.click(screen.getByRole("button", { name: "Cancel" }));

    expect(bridgeEnvelope("audio-export.cancel")).toEqual({
      command: "audio-export.cancel",
    });
  });
});
