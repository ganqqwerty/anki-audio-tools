import { fireEvent, render, screen, waitFor, within } from "@testing-library/svelte";
import { describe, expect, it, vi } from "vitest";

import App from "../src/App.svelte";
import { PRODUCT_LINKS } from "../src/lib/product-links.js";
import {
  DenoiseAlgorithm,
  GraphRecordingCondition,
  GraphSmoothness,
  GraphVoiceLock,
  GraphVoiceRange,
  OutputFormat,
  PauseAggressiveness,
  Phase,
  PitchHumMode,
  VisibleEditorButton,
} from "../src/lib/types.js";
import { asyncPayload, bridgeEnvelopes, bridgePayload, defaultConfig, pycmdMock, setInitialState } from "./settings-app-helpers.js";

describe("App", () => {
  it("renders general settings from initial state", () => {
    setInitialState();

    render(App);

    expect(screen.getByText("Audio Quick Editor Settings")).toBeInTheDocument();
    expect(screen.queryByText("Enable inline editor controls")).not.toBeInTheDocument();
    expect(screen.getByText("Repeat playback by default")).toBeInTheDocument();
    expect(screen.getByText("Pause between repeats (s)")).toBeInTheDocument();
    expect(screen.getByText("Show graph by default")).toBeInTheDocument();
    expect(screen.getByText("Editor toolbar buttons")).toBeInTheDocument();
    expect(screen.getByTestId("button-settings-settings")).toBeInTheDocument();
    expect(screen.getByTestId("button-settings-play")).toBeInTheDocument();
    expect(screen.getByTestId("button-settings-back-chaining")).toBeInTheDocument();
    expect(screen.queryByTestId("button-settings-back-chain-previous")).not.toBeInTheDocument();
    expect(screen.getByTestId("button-settings-delete-selection")).toBeInTheDocument();
    expect(screen.getByTestId("button-settings-delete-rest")).toBeInTheDocument();
    expect(screen.getByText("Speaker's voice")).toBeInTheDocument();
    expect(screen.getByText("Recording condition")).toBeInTheDocument();
    expect(screen.getByText("Graph smoothness")).toBeInTheDocument();
    expect(screen.getByText("Connect holes in graph shorter than (ms)")).toBeInTheDocument();
    expect(screen.getByText("Voice lock")).toBeInTheDocument();
    expect(screen.queryByText("ffmpeg path")).not.toBeInTheDocument();
    expect(screen.queryByText("DeepFilterNet path")).not.toBeInTheDocument();
    expect(screen.getByText("Use DeepFilterNet post-filter")).toBeInTheDocument();
    expect(screen.getByText("DPDFNet Aggressiveness")).toBeInTheDocument();
    expect(screen.getByText("Pause detection")).toBeInTheDocument();
    expect(screen.getByText("Shorten pauses level")).toBeInTheDocument();
    expect(within(screen.getByTestId("settings-pause-advanced-params")).getByText("Advanced Params")).toBeInTheDocument();
    expect(screen.getByTestId("settings-pause-threshold-help")).toBeInTheDocument();
    expect(screen.getByTestId("settings-pause-min-silence-seconds-help")).toBeInTheDocument();
    expect(screen.getByTestId("settings-pause-min-speech-seconds-help")).toBeInTheDocument();
    expect(screen.getByTestId("settings-pause-preprocess-denoise-help")).toBeInTheDocument();
    expect(screen.getByText("Default convert format")).toBeInTheDocument();
    expect(screen.getByText("Default denoise algorithm")).toBeInTheDocument();
    expect(screen.getByText("Default pitch hum mode")).toBeInTheDocument();
    expect(screen.getByText("Volume step (dB)")).toBeInTheDocument();
    expect(screen.getByText("Min volume (dB)")).toBeInTheDocument();
    expect(screen.getByText("Max volume (dB)")).toBeInTheDocument();
    expect(screen.queryByText("Edge silence threshold (dB)")).not.toBeInTheDocument();
    expect(screen.queryByText("Internal pause silence threshold (dB)")).not.toBeInTheDocument();
    expect(screen.getByTestId("settings-pause-advanced-params")).not.toHaveAttribute("open");
  });

  it("switches pause threshold explanations with the selected algorithm", async () => {
    setInitialState();

    render(App);
    expect(screen.getByTestId("settings-pause-threshold-help")).toHaveAttribute(
      "data-aqe-tooltip-content",
      expect.stringMatching(/How quiet audio must be before ffmpeg treats it as silence/),
    );

    await fireEvent.click(screen.getByTestId("pause-detection-algorithm-silero_vad"));

    expect(screen.getByTestId("settings-pause-threshold-help")).toHaveAttribute(
      "data-aqe-tooltip-content",
      expect.stringMatching(/How confident Silero must be that a frame is speech/),
    );
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

  it("saves toolbar visibility when Settings is turned off", async () => {
    setInitialState();
    render(App);
    expect(screen.queryByTestId("settings-hidden-warning")).not.toBeInTheDocument();
    const settingsCard = screen.getByTestId("button-settings-settings");
    await fireEvent.click(within(settingsCard).getByRole("checkbox", { name: "Show" }));
    const warning = screen.getByTestId("settings-hidden-warning");
    expect(warning).toHaveTextContent("Settings remain available from Tools -> Anki Audio Quick Editor -> Settings.");
    expect(settingsCard).toContainElement(warning);
    const image = within(warning).getByTestId("settings-hidden-warning-thumbnail-image");
    const thumbnail = within(warning).getByRole("button", { name: "Expand hidden Settings warning image" });
    expect(image).toHaveAttribute("src");
    expect(thumbnail).toHaveAttribute("aria-expanded", "false");
    await fireEvent.click(thumbnail);
    expect(thumbnail).toHaveAttribute("aria-expanded", "true");
    expect(within(warning).getByTestId("settings-hidden-warning-expanded-image")).toHaveAttribute("src", image.getAttribute("src"));
    await fireEvent.click(within(settingsCard).getByRole("checkbox", { name: "Show" }));
    expect(screen.queryByTestId("settings-hidden-warning")).not.toBeInTheDocument();
    await fireEvent.click(within(settingsCard).getByRole("checkbox", { name: "Show" }));
    await fireEvent.click(screen.getByRole("button", { name: "Save" }));

    const config = bridgePayload<{ visible_editor_buttons: string[] }>("settings.save");
    expect(config.visible_editor_buttons).toContain("aqe:play");
    expect(config.visible_editor_buttons).not.toContain("aqe:settings");
  });

  it("saves editor button display mode changes", async () => {
    setInitialState();

    render(App);
    const playCard = screen.getByTestId("button-settings-play");
    await fireEvent.click(within(playCard).getByRole("checkbox", { name: "Icon" }));
    await fireEvent.click(screen.getByRole("button", { name: "Save" }));

    const config = bridgePayload<{ editor_button_modes: Record<string, string> }>("settings.save");
    expect(config.editor_button_modes["aqe:play"]).toBe("text");
    expect(config.editor_button_modes["aqe:settings"]).toBe("icon");
  });

  it("saves selection action visibility and display mode changes", async () => {
    setInitialState();

    render(App);
    const deleteSelectionCard = screen.getByTestId("button-settings-delete-selection");
    await fireEvent.click(within(deleteSelectionCard).getByRole("checkbox", { name: "Show" }));
    await fireEvent.click(within(deleteSelectionCard).getByRole("checkbox", { name: "Icon" }));
    await fireEvent.click(screen.getByRole("button", { name: "Save" }));

    const config = bridgePayload<{ editor_button_modes: Record<string, string>; visible_editor_buttons: string[] }>("settings.save");
    expect(config.visible_editor_buttons).not.toContain("aqe:delete-selection");
    expect(config.visible_editor_buttons).toContain("aqe:delete-rest");
    expect(config.editor_button_modes["aqe:delete-selection"]).toBe("text");
  });

  it("hides all back-chaining commands from one settings panel", async () => {
    setInitialState();

    render(App);

    const backChainingPanel = screen.getByTestId("button-settings-back-chaining");
    expect(screen.queryByTestId("button-settings-back-chain-practice")).not.toBeInTheDocument();
    expect(screen.queryByTestId("button-settings-back-chain-previous")).not.toBeInTheDocument();
    expect(screen.queryByTestId("button-settings-back-chain-next")).not.toBeInTheDocument();
    expect(within(backChainingPanel).getByTestId("button-settings-back-chaining-panel-controls")).toBeInTheDocument();
    expect(within(backChainingPanel).getByRole("checkbox", { name: "Show panel" })).toBeChecked();
    expect(within(backChainingPanel).getByTestId("button-settings-back-chain-practice-visibility-show")).toBeEnabled();
    expect(within(backChainingPanel).getByTestId("button-settings-back-chain-previous-visibility-show")).toBeEnabled();
    expect(within(backChainingPanel).getByTestId("button-settings-back-chain-next-visibility-show")).toBeEnabled();
    expect(within(backChainingPanel).getByTestId("button-settings-back-chain-practice-mode-icon")).toBeEnabled();
    expect(within(backChainingPanel).getByTestId("button-settings-back-chain-previous-mode-icon")).toBeEnabled();
    expect(within(backChainingPanel).getByTestId("button-settings-back-chain-next-mode-icon")).toBeEnabled();

    await fireEvent.click(within(backChainingPanel).getByTestId("button-settings-back-chaining-visibility-show"));
    await fireEvent.click(screen.getByRole("button", { name: "Save" }));

    const config = bridgePayload<{ visible_editor_buttons: string[] }>("settings.save");
    expect(config.visible_editor_buttons).not.toContain("aqe:back-chain-practice");
    expect(config.visible_editor_buttons).not.toContain("aqe:back-chain-previous");
    expect(config.visible_editor_buttons).not.toContain("aqe:back-chain-next");
  });

  it("saves individual back-chaining button visibility and display modes", async () => {
    setInitialState();

    render(App);

    const backChainingPanel = screen.getByTestId("button-settings-back-chaining");
    await fireEvent.click(within(backChainingPanel).getByTestId("button-settings-back-chain-previous-visibility-show"));
    await fireEvent.click(within(backChainingPanel).getByTestId("button-settings-back-chain-next-mode-icon"));
    await fireEvent.click(screen.getByRole("button", { name: "Save" }));

    const config = bridgePayload<{
      editor_button_modes: Record<string, string>;
      visible_editor_buttons: string[];
    }>("settings.save");
    expect(config.visible_editor_buttons).toContain("aqe:back-chain-practice");
    expect(config.visible_editor_buttons).not.toContain("aqe:back-chain-previous");
    expect(config.visible_editor_buttons).toContain("aqe:back-chain-next");
    expect(config.editor_button_modes["aqe:back-chain-next"]).toBe("text");
  });

  it("shows a placeholder for toolbar buttons without extra settings", () => {
    setInitialState();

    render(App);

    const folderCard = screen.getByTestId("button-settings-show-file");
    const deleteRestCard = screen.getByTestId("button-settings-delete-rest");

    expect(within(folderCard).getByText("No extra settings")).toBeInTheDocument();
    expect(within(deleteRestCard).getByText("No extra settings")).toBeInTheDocument();
  });

  it("saves split button default settings", async () => {
    setInitialState();

    render(App);
    await fireEvent.click(screen.getByTestId("share-target-catbox"));
    await fireEvent.click(screen.getByTestId(`pause-aggressiveness-${PauseAggressiveness.Aggressive}`));
    await fireEvent.click(screen.getByTestId(`denoise-algorithm-${DenoiseAlgorithm.Dpdfnet}`));
    await fireEvent.click(screen.getByTestId(`output-format-${OutputFormat.FLAC}`));
    await fireEvent.click(screen.getByTestId(`pitch-hum-mode-${PitchHumMode.PitchTier}`));
    await fireEvent.click(screen.getByTestId("dpdfnet-attn-limit-db-18"));
    await fireEvent.input(screen.getByTestId("repeat-pause-seconds"), {
      target: { value: "2.5" },
    });
    await fireEvent.click(screen.getByRole("button", { name: "Save" }));

    const config = bridgePayload<{
      denoise_algorithm: string;
      dpdfnet_attn_limit_db: number;
      output_format: string;
      pause_aggressiveness: string;
      pause_silencedetect_threshold_db: number;
      pitch_hum_mode: string;
      repeat_pause_seconds: number;
      share_target: string;
    }>("settings.save");
    expect(config.pause_aggressiveness).toBe("aggressive");
    expect(config.pause_silencedetect_threshold_db).toBe(-52);
    expect(config.share_target).toBe("catbox");
    expect(config.output_format).toBe("flac");
    expect(config.denoise_algorithm).toBe("dpdfnet");
    expect(config.pitch_hum_mode).toBe("pitch_tier");
    expect(config.dpdfnet_attn_limit_db).toBe(18);
    expect(config.repeat_pause_seconds).toBe(2.5);
  });

  it("saves graph display defaults", async () => {
    setInitialState();

    render(App);
    await fireEvent.click(screen.getByTestId(`graph-voice-range-${GraphVoiceRange.Child}`));
    await fireEvent.click(screen.getByTestId(`graph-recording-condition-${GraphRecordingCondition.Studio}`));
    await fireEvent.click(screen.getByTestId(`graph-smoothness-${GraphSmoothness.VerySmooth}`));
    await fireEvent.input(screen.getByTestId("graph-connect-short-dropouts-ms"), {
      target: { value: "90" },
    });
    await fireEvent.click(screen.getByTestId(`graph-voice-lock-${GraphVoiceLock.Stable}`));
    await fireEvent.click(screen.getByRole("button", { name: "Save" }));

    const config = bridgePayload<{
      graph_connect_short_dropouts_ms: number;
      graph_recording_condition: string;
      graph_smoothness: string;
      graph_voice_lock: string;
      graph_voice_range: string;
    }>("settings.save");
    expect(config.graph_voice_range).toBe("child");
    expect(config.graph_recording_condition).toBe("studio");
    expect(config.graph_smoothness).toBe("very_smooth");
    expect(config.graph_connect_short_dropouts_ms).toBe(90);
    expect(config.graph_voice_lock).toBe("stable");
  });

  it("enables the learner recording panel with separate display settings", async () => {
    setInitialState();

    render(App);

    const recordingPanel = screen.getByTestId("button-settings-record-play-yours");
    expect(screen.queryByTestId("button-settings-record-voice")).not.toBeInTheDocument();
    expect(screen.queryByTestId("button-settings-play-recording")).not.toBeInTheDocument();
    const recordIconMode = within(recordingPanel).getByTestId("button-settings-record-voice-mode-icon");
    const playYoursIconMode = within(recordingPanel).getByTestId("button-settings-play-recording-mode-icon");
    expect(recordIconMode).toBeEnabled();
    expect(playYoursIconMode).toBeEnabled();

    await fireEvent.click(within(recordingPanel).getByTestId("button-settings-record-play-yours-visibility-show"));
    await fireEvent.click(recordIconMode);
    await fireEvent.click(playYoursIconMode);
    await fireEvent.input(screen.getByTestId("voice-recording-countdown-seconds"), {
      target: { value: "0" },
    });
    await fireEvent.click(screen.getByRole("button", { name: "Save" }));

    const config = bridgePayload<{
      editor_button_modes: Record<string, string>;
      visible_editor_buttons: string[];
      voice_recording_countdown_seconds: number;
    }>("settings.save");
    expect(config.visible_editor_buttons).toContain("aqe:record-voice");
    expect(config.visible_editor_buttons).toContain("aqe:play-recording");
    expect(config.editor_button_modes["aqe:record-voice"]).toBe("text");
    expect(config.editor_button_modes["aqe:play-recording"]).toBe("text");
    expect(config.voice_recording_countdown_seconds).toBe(0);
  });

  it("hides both learner recording commands when the panel is hidden", async () => {
    setInitialState({
      ...defaultConfig,
      visible_editor_buttons: [
        ...defaultConfig.visible_editor_buttons,
        VisibleEditorButton.AqeRecordVoice,
        VisibleEditorButton.AqePlayRecording,
      ],
    });

    render(App);

    const recordingPanel = screen.getByTestId("button-settings-record-play-yours");
    await fireEvent.click(within(recordingPanel).getByTestId("button-settings-record-play-yours-visibility-show"));
    await fireEvent.click(screen.getByRole("button", { name: "Save" }));

    const config = bridgePayload<{ visible_editor_buttons: string[] }>("settings.save");
    expect(config.visible_editor_buttons).not.toContain("aqe:record-voice");
    expect(config.visible_editor_buttons).not.toContain("aqe:play-recording");
  });

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
