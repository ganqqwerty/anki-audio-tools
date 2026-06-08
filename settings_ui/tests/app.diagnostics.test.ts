import { fireEvent, render, screen, waitFor } from "@testing-library/svelte";
import { describe, expect, it, vi } from "vitest";

import App from "../src/App.svelte";
import { PRODUCT_LINKS } from "../src/lib/product-links.js";
import { Phase } from "../src/lib/types.js";
import { asyncPayload, bridgeEnvelopes, defaultConfig, pycmdMock, setInitialState } from "./settings-app-helpers";

describe("App diagnostics behavior", () => {
  it("shows diagnostics data and runs a health check", async () => {
    setInitialState();

    const { container } = render(App);
    await fireEvent.click(screen.getByRole("tab", { name: "Diagnostics & About" }));
    await fireEvent.click(screen.getByRole("button", { name: "Run Health Check" }));

    const { id, payload } = asyncPayload<{
      id: string;
      op: string;
      payload: { config: typeof defaultConfig };
    }>("health_check");
    expect(payload.config.deep_filter_post_filter).toBe(true);
    expect(payload.config.repeat_playback_by_default).toBe(true);
    expect(payload.config.repeat_pause_seconds).toBe(0);
    expect(payload.config.show_graph_by_default).toBe(true);
    expect(payload.config.selection_marker_shift_buttons_enabled).toBe(false);
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

    const { id } = asyncPayload<{ id: string }>("support_report");

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

    const { id } = asyncPayload<{ id: string }>("show_log_file");

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

  it("opens Clear unused audios from diagnostics", async () => {
    setInitialState();

    render(App);
    await fireEvent.click(screen.getByRole("tab", { name: "Diagnostics & About" }));
    await fireEvent.click(screen.getByRole("button", { name: "Clear unused audios" }));

    expect(bridgeEnvelopes()).toContainEqual({ command: "settings.check_media" });
  });

  it("opens runtime installer from diagnostics and refreshes runtime status", async () => {
    setInitialState();

    render(App);
    await fireEvent.click(screen.getByRole("tab", { name: "Diagnostics & About" }));
    await fireEvent.click(screen.getByRole("button", { name: "Install/Repair Runtime" }));

    expect(bridgeEnvelopes()).toContainEqual({ command: "settings.open_runtime_installer" });
    window.onRuntimeInstallerClosed?.({
      error: "",
      message: "Runtime is ready.",
      phase: Phase.Ready,
      platform: "macos-arm64",
      progress: 100,
      runtime_manifest_id: "runtime-test",
      runtime_root: "/runtime",
    });

    await waitFor(() =>
      expect(screen.getByTestId("runtime-status")).toHaveTextContent("Runtime is ready.")
    );
  });

  it("renders resource and feedback links in diagnostics", async () => {
    setInitialState(); render(App);
    await fireEvent.click(screen.getByRole("tab", { name: "Diagnostics & About" }));
    for (const [name, href] of [
      ["Website", PRODUCT_LINKS.githubPages],
      ["AnkiWeb listing", PRODUCT_LINKS.ankiWeb],
      ["Discord: Yuri's cool software", PRODUCT_LINKS.discord],
      ["Support on Patreon", PRODUCT_LINKS.patreon],
      [/Telegram: Immersoshnaya/, PRODUCT_LINKS.telegram],
      ["Report a bug", PRODUCT_LINKS.bugReport],
      ["Request an idea", PRODUCT_LINKS.ideaRequest],
    ] as const)
      expect(screen.getByRole("link", { name })).toHaveAttribute("href", href);
    expect(screen.getByText("Created by Yuri Katkov (ganqqwerty).")).toBeInTheDocument();
    expect(screen.getByText(/Special thanks to alpha testers:/)).toBeInTheDocument();
  });

  it("renders translated settings labels from initial messages", async () => {
    setInitialState(defaultConfig, {
      "settings.title": "Audio-Schnelleditor Einstellungen",
      "settings.show_ffmpeg_commands": "Debug-Informationen anzeigen",
    });
    render(App);

    expect(screen.getByText("Audio-Schnelleditor Einstellungen")).toBeInTheDocument();
    await fireEvent.click(screen.getByRole("tab", { name: "Diagnostics & About" }));
    expect(screen.getByText("Debug-Informationen anzeigen")).toBeInTheDocument();
  });
});

