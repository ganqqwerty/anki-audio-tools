import { fireEvent, render, screen, waitFor } from "@testing-library/svelte";
import { describe, expect, it, vi } from "vitest";

import App from "../src/App.svelte";

const defaultConfig = {
  _config_version: 7,
  enabled: true,
  debug_logging: false,
  show_ffmpeg_commands: false,
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
  output_format: "mp3" as const,
  ffmpeg_path: "",
  deep_filter_path: "",
  deep_filter_post_filter: true,
};

function pycmdMock(): ReturnType<typeof vi.fn> {
  const pycmd = (globalThis as unknown as Record<string, ReturnType<typeof vi.fn>>)["pycmd"];
  if (!pycmd) {
    throw new Error("pycmd test mock is not installed");
  }
  return pycmd;
}

describe("App", () => {
  it("renders general settings from initial state", () => {
    window.__INITIAL_STATE__ = {
      config: defaultConfig,
      version: "0.1.0",
      addon_dir: "/tmp/addon",
      log_file_path: "/tmp/addon/log.txt",
      diagnostics: { addon_id: "anki_audio_quick_editor", collection_available: true },
    };

    render(App);

    expect(screen.getByText("Audio Quick Editor Settings")).toBeInTheDocument();
    expect(screen.queryByText("Enable inline editor controls")).not.toBeInTheDocument();
    expect(screen.getByText("Show ffmpeg commands while processing")).toBeInTheDocument();
    expect(screen.getByText("ffmpeg path")).toBeInTheDocument();
    expect(screen.getByText("DeepFilterNet path")).toBeInTheDocument();
    expect(screen.getByText("Use DeepFilterNet post-filter")).toBeInTheDocument();
    expect(screen.getByText("Volume step (dB)")).toBeInTheDocument();
    expect(screen.getByText("Min volume (dB)")).toBeInTheDocument();
    expect(screen.getByText("Max volume (dB)")).toBeInTheDocument();
    expect(screen.queryByText("Edge silence threshold (dB)")).not.toBeInTheDocument();
    expect(screen.getByText("Internal pause silence threshold (dB)")).toBeInTheDocument();
  });

  it("always saves inline editor controls as enabled", async () => {
    window.__INITIAL_STATE__ = {
      config: { ...defaultConfig, enabled: false },
      version: "0.1.0",
      addon_dir: "/tmp/addon",
      log_file_path: "/tmp/addon/log.txt",
      diagnostics: { addon_id: "anki_audio_quick_editor", collection_available: true },
    };

    render(App);
    await fireEvent.click(screen.getByRole("button", { name: "Save" }));

    const call = vi
      .mocked(pycmdMock())
      .mock.calls
      .map(([command]) => command as string)
      .find((command) => command.startsWith("settings_save:")) as string;
    const config = JSON.parse(call.slice("settings_save:".length)) as { enabled: boolean };
    expect(config.enabled).toBe(true);
  });

  it("saves edited volume settings", async () => {
    window.__INITIAL_STATE__ = {
      config: defaultConfig,
      version: "0.1.0",
      addon_dir: "/tmp/addon",
      log_file_path: "/tmp/addon/log.txt",
      diagnostics: { addon_id: "anki_audio_quick_editor", collection_available: true },
    };

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

    const call = vi
      .mocked(pycmdMock())
      .mock.calls
      .map(([command]) => command as string)
      .find((command) => command.startsWith("settings_save:")) as string;
    const config = JSON.parse(call.slice("settings_save:".length)) as {
      volume_step_db: number;
      min_volume_db: number;
      max_volume_db: number;
    };
    expect(config.volume_step_db).toBe(1.5);
    expect(config.min_volume_db).toBe(-18);
    expect(config.max_volume_db).toBe(12);
  });

  it("shows diagnostics data and runs a health check", async () => {
    window.__INITIAL_STATE__ = {
      config: defaultConfig,
      version: "0.1.0",
      addon_dir: "/tmp/addon",
      log_file_path: "/tmp/addon/log.txt",
      diagnostics: { addon_id: "anki_audio_quick_editor", collection_available: true },
    };

    const { container } = render(App);
    await fireEvent.click(screen.getByRole("tab", { name: "Diagnostics & About" }));
    await fireEvent.click(screen.getByRole("button", { name: "Run Health Check" }));

    const call = vi
      .mocked(pycmdMock())
      .mock.calls
      .map(([command]) => command as string)
      .find((command) => command.startsWith("async_cmd:")) as string;
    const { id, payload } = JSON.parse(call.slice("async_cmd:".length)) as {
      id: string;
      payload: { config: typeof defaultConfig };
    };
    expect(payload.config.deep_filter_post_filter).toBe(true);
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
    window.__INITIAL_STATE__ = {
      config: defaultConfig,
      version: "0.1.0",
      addon_dir: "/tmp/addon",
      log_file_path: "/tmp/addon/log.txt",
      diagnostics: { addon_id: "anki_audio_quick_editor", collection_available: true },
    };

    render(App);
    await fireEvent.click(screen.getByRole("tab", { name: "Diagnostics & About" }));
    await fireEvent.click(screen.getByRole("button", { name: "Copy Support Report" }));

    const call = vi
      .mocked(pycmdMock())
      .mock.calls
      .map(([command]) => command as string)
      .find((command) => command.startsWith("async_cmd:")) as string;
    const { id } = JSON.parse(call.slice("async_cmd:".length)) as { id: string };

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
              command.startsWith("copy_support_report:") &&
              command.includes("support body"),
          ),
      ).toBe(true)
    );
    expect(screen.getByTestId("diagnostics-message")).toHaveTextContent("Support report copied");
  });

  it("opens the log file from diagnostics", async () => {
    window.__INITIAL_STATE__ = {
      config: defaultConfig,
      version: "0.1.0",
      addon_dir: "/tmp/addon",
      log_file_path: "/tmp/addon/log.txt",
      diagnostics: { addon_id: "anki_audio_quick_editor", collection_available: true },
    };

    render(App);
    await fireEvent.click(screen.getByRole("tab", { name: "Diagnostics & About" }));
    await fireEvent.click(screen.getByRole("button", { name: "Show Log File" }));

    const call = vi
      .mocked(pycmdMock())
      .mock.calls
      .map(([command]) => command as string)
      .find((command) => command.startsWith("async_cmd:")) as string;
    const { id } = JSON.parse(call.slice("async_cmd:".length)) as { id: string };

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
});
