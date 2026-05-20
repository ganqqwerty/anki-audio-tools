import { fireEvent, render, screen, waitFor } from "@testing-library/svelte";
import { describe, expect, it, vi } from "vitest";

import App from "../src/App.svelte";
import { DenoiseAlgorithm, Direction, OutputFormat, PauseAggressiveness } from "../src/lib/types.js";

const defaultConfig = {
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

function pycmdMock(): ReturnType<typeof vi.fn> {
  const pycmd = (globalThis as unknown as Record<string, ReturnType<typeof vi.fn>>)["pycmd"];
  if (!pycmd) {
    throw new Error("pycmd test mock is not installed");
  }
  return pycmd;
}

function bridgeEnvelopes(): Array<{ command: string; payload?: unknown }> {
  return vi
    .mocked(pycmdMock())
    .mock.calls
    .map(([command]) => command as string)
    .filter((command) => command.startsWith("bridge:"))
    .map((command) => JSON.parse(command.slice("bridge:".length)) as { command: string; payload?: unknown });
}

function bridgePayload<T>(commandName: string): T {
  const envelope = bridgeEnvelopes().find((item) => item.command === commandName);
  if (!envelope) {
    throw new Error(`Bridge command not found: ${commandName}`);
  }
  return envelope.payload as T;
}

function setInitialState(config = defaultConfig, messages: Record<string, string> = {}): void {
  window.__INITIAL_STATE__ = {
    config,
    version: "0.1.0",
    addon_dir: "/tmp/addon",
    log_file_path: "/tmp/addon/log.txt",
    locale: "en",
    direction: Direction.LTR,
    messages,
    diagnostics: { addon_id: "anki_audio_quick_editor", collection_available: true },
  };
}

describe("App", () => {
  it("renders general settings from initial state", () => {
    setInitialState();

    render(App);

    expect(screen.getByText("Audio Quick Editor Settings")).toBeInTheDocument();
    expect(screen.queryByText("Enable inline editor controls")).not.toBeInTheDocument();
    expect(screen.getByText("Show ffmpeg commands while processing")).toBeInTheDocument();
    expect(screen.getByText("Repeat playback by default")).toBeInTheDocument();
    expect(screen.getByText("Pause between repeats (s)")).toBeInTheDocument();
    expect(screen.getByText("Show graph by default")).toBeInTheDocument();
    expect(screen.getByText("ffmpeg path")).toBeInTheDocument();
    expect(screen.getByText("DeepFilterNet path")).toBeInTheDocument();
    expect(screen.getByText("Use DeepFilterNet post-filter")).toBeInTheDocument();
    expect(screen.getByText("Shorten pauses level")).toBeInTheDocument();
    expect(screen.getByText("Default denoise algorithm")).toBeInTheDocument();
    expect(screen.getByText("Volume step (dB)")).toBeInTheDocument();
    expect(screen.getByText("Min volume (dB)")).toBeInTheDocument();
    expect(screen.getByText("Max volume (dB)")).toBeInTheDocument();
    expect(screen.queryByText("Edge silence threshold (dB)")).not.toBeInTheDocument();
    expect(screen.getByText("Internal pause silence threshold (dB)")).toBeInTheDocument();
  });

  it("always saves inline editor controls as enabled", async () => {
    setInitialState({ ...defaultConfig, enabled: false });

    render(App);
    await fireEvent.click(screen.getByRole("button", { name: "Save" }));

    const config = bridgePayload<{ enabled: boolean }>("settings.save");
    expect(config.enabled).toBe(true);
  });

  it("saves edited volume settings", async () => {
    setInitialState();

    render(App);
    await fireEvent.input(screen.getByLabelText("Volume step (dB)"), {
      target: { value: "1.5" },
    });
    await fireEvent.input(screen.getByLabelText("Min volume (dB)"), {
      target: { value: "-18" },
    });
    await fireEvent.input(screen.getByLabelText("Max volume (dB)"), {
      target: { value: "12" },
    });
    await fireEvent.click(screen.getByRole("button", { name: "Save" }));

    const config = bridgePayload<{
      volume_step_db: number;
      min_volume_db: number;
      max_volume_db: number;
    }>("settings.save");
    expect(config.volume_step_db).toBe(1.5);
    expect(config.min_volume_db).toBe(-18);
    expect(config.max_volume_db).toBe(12);
  });

  it("saves split button default settings", async () => {
    setInitialState();

    render(App);
    await fireEvent.change(screen.getByLabelText("Shorten pauses level"), {
      target: { value: PauseAggressiveness.Aggressive },
    });
    await fireEvent.change(screen.getByLabelText("Default denoise algorithm"), {
      target: { value: DenoiseAlgorithm.Rnnoise },
    });
    await fireEvent.input(screen.getByTestId("repeat-pause-seconds"), {
      target: { value: "2.5" },
    });
    await fireEvent.click(screen.getByRole("button", { name: "Save" }));

    const config = bridgePayload<{
      denoise_algorithm: string;
      pause_aggressiveness: string;
      repeat_pause_seconds: number;
    }>("settings.save");
    expect(config.pause_aggressiveness).toBe("aggressive");
    expect(config.denoise_algorithm).toBe("rnnoise");
    expect(config.repeat_pause_seconds).toBe(2.5);
  });

  it("shows diagnostics data and runs a health check", async () => {
    setInitialState();

    const { container } = render(App);
    await fireEvent.click(screen.getByRole("tab", { name: "Diagnostics & About" }));
    await fireEvent.click(screen.getByRole("button", { name: "Run Health Check" }));

    const { id, payload } = bridgePayload<{
      id: string;
      op: string;
      payload: { config: typeof defaultConfig };
    }>("settings.async");
    expect(payload.config.deep_filter_post_filter).toBe(true);
    expect(payload.config.repeat_playback_by_default).toBe(false);
    expect(payload.config.repeat_pause_seconds).toBe(0);
    expect(payload.config.show_graph_by_default).toBe(false);
    window.onAsyncProgress?.({ id, progress: 100, message: "Done" });
    window.onAsyncDone?.({
      id,
      ok: true,
      result: {
        collection_available: true,
        deck_count: 2,
        note_type_count: 3,
        card_count: 5,
      },
    });

    await waitFor(() =>
      expect(screen.getByTestId("health-report")).toHaveTextContent('"card_count": 5')
    );
    expect(container).toHaveTextContent("Health check completed");
  });

  it("copies a support report from diagnostics", async () => {
    setInitialState();

    render(App);
    await fireEvent.click(screen.getByRole("tab", { name: "Diagnostics & About" }));
    await fireEvent.click(screen.getByRole("button", { name: "Copy Support Report" }));

    const { id } = bridgePayload<{ id: string }>("settings.async");

    window.onAsyncDone?.({
      id,
      ok: true,
      result: {
        reportText: "support body",
      },
    });

    await waitFor(() =>
      expect(
        vi
          .mocked(pycmdMock())
          .mock.calls.some(
            ([command]) =>
              typeof command === "string" &&
              command.startsWith("bridge:") &&
              JSON.parse(command.slice("bridge:".length)).command === "support.copy_report" &&
              command.includes("support body"),
          ),
      ).toBe(true)
    );
    expect(screen.getByTestId("diagnostics-message")).toHaveTextContent("Support report copied");
  });

  it("opens the log file from diagnostics", async () => {
    setInitialState();

    render(App);
    await fireEvent.click(screen.getByRole("tab", { name: "Diagnostics & About" }));
    await fireEvent.click(screen.getByRole("button", { name: "Show Log File" }));

    const { id } = bridgePayload<{ id: string }>("settings.async");

    window.onAsyncDone?.({
      id,
      ok: true,
      result: {
        logFilePath: "/tmp/addon/log.txt",
      },
    });

    await waitFor(() =>
      expect(screen.getByTestId("diagnostics-message")).toHaveTextContent(
        "Log file opened: /tmp/addon/log.txt",
      )
    );
  });

  it("renders translated settings labels from initial messages", () => {
    setInitialState(defaultConfig, {
      "settings.title": "Audio-Schnelleditor Einstellungen",
      "settings.show_ffmpeg_commands": "ffmpeg-Befehle anzeigen",
    });

    render(App);

    expect(screen.getByText("Audio-Schnelleditor Einstellungen")).toBeInTheDocument();
    expect(screen.getByText("ffmpeg-Befehle anzeigen")).toBeInTheDocument();
  });
});
