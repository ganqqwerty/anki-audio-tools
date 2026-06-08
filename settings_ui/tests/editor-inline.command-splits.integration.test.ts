import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  disposeEditorRuntime,
  initializeEditorRuntime,
  scan,
} from "../src/editor-inline/runtime.js";
import type { EditorCommandPayload } from "../src/editor-inline/types.js";
import {
  bridgeCommands,
  muteConsole,
  renderFields,
  track,
} from "./editor-inline.integration.helpers.js";

describe("editor inline split-button command integration", () => {
  let restoreConsole: () => void;

  beforeEach(() => {
    restoreConsole = muteConsole();
    renderFields();
  });

  afterEach(() => {
    disposeEditorRuntime();
    restoreConsole();
    vi.restoreAllMocks();
  });

  it("dispatches denoise split commands and renders collapsed help", async () => {
    const config = {
      audioFieldIndices: [0],
      splitButtonDefaults: {
        denoiseAlgorithm: "standard" as const,
        dpdfnetAttnLimitDb: 8.5,
        pauseAggressiveness: "normal" as const,
        repeatPauseSeconds: 0,
        speedStep: 1.5,
        volumeStepDb: 15,
      },
    };
    initializeEditorRuntime(config);
    scan(config);

    const help = document.querySelector<HTMLDetailsElement>('[data-testid="aqe-help-0"]')!;
    expect(help.open).toBe(false);
    expect(help.querySelectorAll(".aqe-help-command")).toHaveLength(16);
    expect(help.querySelector(".aqe-help-triangle")).not.toBeNull();
    expect(help).toHaveTextContent("Shift-drag on the graph to select a region.");
    expect(help).toHaveTextContent("Delete Region removes the selected region; Delete the rest keeps only the selected region.");
    expect(help).toHaveTextContent("Delete Region / Delete the rest");
    expect(help).toHaveTextContent("Creates a new file that removes the selected region or keeps only that region.");
    expect(help).toHaveTextContent("Creates a new file with louder audio.");
    expect(help).toHaveTextContent("Creates a compressed MP3 by lowering safe audio parameters.");
    expect(help).toHaveTextContent("Compress Audio");
    expect(help).toHaveTextContent("Share this file online. The link will be copied to the clipboard.");
    expect(help).toHaveTextContent(/GitHub Pages.*Report a bug.*Request an idea/s);
    expect(help).toHaveTextContent("Every edit creates a new media file and updates the field to point at it.");
    expect(help).toHaveTextContent("grey is loudness and lines are pitch of the voice.");
    expect(document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-denoise-standard"]')?.getAttribute("data-aqe-tooltip-content")).toBe(
      "Denoise\nCreate a new file cleaned with Standard",
    );

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-denoise-standard"]')!.click();
    expect(bridgeCommands()).toContain("aqe:command-payload");
    expect(window.__aqePendingCommandPayload?.command).toBe("aqe:denoise-standard");
    expect(window.__aqePendingCommandPayload?.fieldOrd).toBe(0);
    expect(window.__aqePendingCommandPayload?.overrides?.denoiseAlgorithm).toBe("standard");

    window.__aqePrepareForNewNote?.();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-denoise-standard-menu"]')!.click();
    await Promise.resolve();
    const dpdfnetPreset = document.querySelector<HTMLButtonElement>(
      '[data-testid="aqe-split-0-denoise-standard-preset-dpdfnet"]',
    )!;
    expect(dpdfnetPreset.getAttribute("data-aqe-tooltip-content")).toContain(
      "Create a new file cleaned with DPDFNet, Aggressiveness: Gentle",
    );
    dpdfnetPreset.click();
    await Promise.resolve();
    expect(document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-denoise-standard"]')?.getAttribute("data-aqe-tooltip-content")).toBe(
      "Denoise\nCreate a new file cleaned with DPDFNet",
    );
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-denoise-standard"]')!.click();
    expect(window.__aqePendingCommandPayload?.command).toBe("aqe:dpdfnet");
    expect(window.__aqePendingCommandPayload?.fieldOrd).toBe(0);
    expect(window.__aqePendingCommandPayload?.overrides?.denoiseAlgorithm).toBe("dpdfnet");
  });

  it("dispatches graph split requests with field-local graph settings", async () => {
    const config = {
      audioFieldIndices: [0],
      splitButtonDefaults: {
        denoiseAlgorithm: "standard" as const,
        graphConnectShortDropoutsMs: 0,
        graphRecordingCondition: "auto" as const,
        graphSmoothness: "balanced" as const,
        graphVoiceLock: "balanced" as const,
        graphVoiceRange: "general" as const,
        pauseAggressiveness: "normal" as const,
        repeatPauseSeconds: 0,
        speedStep: 1.5,
        volumeStepDb: 15,
      },
    };
    initializeEditorRuntime(config);
    scan(config);
    await Promise.resolve();
    window.__aqeSetBusy?.(0, false);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-graph-menu"]')!.click();
    await Promise.resolve();
    expect(document.querySelector('[data-testid="aqe-split-0-graph-popover"]')).not.toHaveTextContent("Current settings:");
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-graph-voice-range-child"]')!.click();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-graph-recording-condition-studio"]')!.click();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-graph-voice-lock-stable"]')!.click();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-graph-smoothness-very_smooth"]')!.click();
    const connectDropoutsInput = document.querySelector<HTMLInputElement>('[data-testid="aqe-split-0-graph-connect-dropouts"]')!;
    connectDropoutsInput.value = "90";
    connectDropoutsInput.dispatchEvent(new Event("input", { bubbles: true }));
    await Promise.resolve();

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-graph"]')!.click();

    expect(bridgeCommands()).toContain("aqe:analyze-field");
    expect(window.__aqePopPendingGraphAnalysisRequest?.()).toEqual({
      graphSettings: {
        connectShortDropoutsMs: 90,
        recordingCondition: "studio",
        smoothness: "very_smooth",
        voiceLock: "stable",
        voiceRange: "child",
      },
      ord: 0,
      sourceFilename: "clip one.mp3",
    });
  });

  it("falls back to backend graph analysis when the current field no longer has audio", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, { ...track, sourceFilename: "clip one.mp3" }, 0);
    document.getElementById("f0")!.innerHTML = "";
    await Promise.resolve();

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-graph"]')!.click();

    expect(window.__aqePopPendingGraphAnalysisRequest?.()).toBeNull();
    expect(bridgeCommands()).toContain("focus:0");
    expect(bridgeCommands()).toContain("aqe:command-payload");
    const payload = window.__aqePendingCommandPayload as EditorCommandPayload | null | undefined;
    expect(payload?.command).toBe("aqe:analyze");
    expect(payload?.fieldOrd).toBe(0);
    expect(payload?.graphSettings).toMatchObject({ smoothness: expect.any(String) });
  });

  it("dispatches convert commands with the selected output format", async () => {
    window.__AQE_EDITOR_CONFIG__ = {
      audioFieldIndices: [0],
      splitButtonDefaults: {
        denoiseAlgorithm: "standard",
        outputFormat: "m4a",
        pauseAggressiveness: "normal",
        repeatPauseSeconds: 0,
        speedStep: 1.5,
        volumeStepDb: 15,
      },
    };
    initializeEditorRuntime(window.__AQE_EDITOR_CONFIG__);
    scan(window.__AQE_EDITOR_CONFIG__);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-convert"]')!.click();
    const defaultPayload = window.__aqePendingCommandPayload as EditorCommandPayload | null | undefined;
    window.__aqePendingCommandPayload = null;
    window.__aqeSetBusy?.(0, false);
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-convert-menu"]')!.click();
    await Promise.resolve();
    expect(document.querySelector('[data-testid="aqe-split-0-convert-preset-source"]')).toBeNull();
    expect(document.querySelector('[data-testid="aqe-split-0-convert-preset-flac"]')).not.toBeNull();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-convert-preset-flac"]')!.click();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-convert"]')!.click();

    expect(defaultPayload?.overrides?.targetFormat).toBe("m4a");
    expect(window.__aqePendingCommandPayload).toMatchObject({
      command: "aqe:convert",
      fieldOrd: 0,
      overrides: {
        targetFormat: "flac",
      },
    });
  });

  it("dispatches share commands with the selected host and exposes save-default", async () => {
    const config = {
      audioFieldIndices: [0],
      splitButtonDefaults: {
        denoiseAlgorithm: "dpdfnet" as const,
        dpdfnetAttnLimitDb: 18,
        pauseAggressiveness: "normal" as const,
        repeatPauseSeconds: 0,
        speedStep: 1.5,
        volumeStepDb: 15,
      },
    };
    initializeEditorRuntime(config);
    scan(config);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-share-menu"]')!.click();
    await Promise.resolve();

    expect(document.querySelector('[data-testid="aqe-split-0-share-save-default"]')).not.toBeNull();
    expect(document.querySelector('[data-testid="aqe-split-0-share-dpdfnet-aggressiveness"]')).toBeNull();

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-share-preset-catbox"]')!.click();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-share"]')!.click();

    expect(bridgeCommands()).toContain("aqe:command-payload");
    expect(window.__aqePendingCommandPayload).toMatchObject({
      command: "aqe:share",
      fieldOrd: 0,
      shareTarget: "catbox",
    });
  });

  it("promotes the selected share host to defaults", async () => {
    window.__aqeSplitButtonStates = {};
    initializeEditorRuntime({ audioFieldIndices: [0, 1] });
    scan({ audioFieldIndices: [0, 1] });

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-1-share-menu"]')!.click();
    await Promise.resolve();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-1-share-preset-catbox"]')!.click();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-1-share-save-default"]')!.click();
    await Promise.resolve();

    expect(bridgeCommands()).toContain("aqe:save-split-defaults");
    expect(window.__aqePopPendingSplitDefaultSaveRequest?.()).toEqual({
      defaults: {
        shareTarget: "catbox",
      },
      fieldOrd: 1,
    });
    expect(window.__AQE_EDITOR_CONFIG__?.splitButtonDefaults?.shareTarget).toBe("catbox");
    expect(window.__aqeSplitButtonStates?.[0]?.shareTarget).toBe("catbox");
    expect(window.__aqeSplitButtonStates?.[1]?.shareTarget).toBe("catbox");
  });

});
