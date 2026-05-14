import { fireEvent, render, screen, waitFor } from "@testing-library/svelte";
import { describe, expect, it, vi } from "vitest";

import App from "../src/App.svelte";

const defaultConfig = {
  _config_version: 3,
  enabled: true,
  debug_logging: false,
  show_ffmpeg_commands: false,
  manual_trim_small_ms: 100,
  manual_trim_large_ms: 500,
  speed_step: 0.05,
  min_speed: 0.75,
  max_speed: 1.5,
  edge_silence_threshold_db: -35,
  edge_silence_min_ms: 100,
  internal_pause_threshold_ms: 300,
  internal_pause_target_gap_ms: 100,
  output_format: "mp3" as const,
  ffmpeg_path: "",
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
    const { id } = JSON.parse(call.slice("async_cmd:".length)) as { id: string };
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
});
