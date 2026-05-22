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
  renderTwoAudioFields,
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
        speedStep: 0.05,
        volumeStepDb: 3,
      },
    };
    initializeEditorRuntime(config);
    scan(config);

    const help = document.querySelector<HTMLDetailsElement>('[data-testid="aqe-help-0"]')!;
    expect(help.open).toBe(false);
    expect(help.querySelectorAll(".aqe-help-command")).toHaveLength(15);
    expect(help.querySelector(".aqe-help-triangle")).not.toBeNull();
    expect(help).toHaveTextContent("Shift-drag on the graph to select a region.");
    expect(help).toHaveTextContent("Delete Region removes the selected region; Delete the rest keeps only the selected region.");
    expect(help).toHaveTextContent("Delete Region / Delete the rest");
    expect(help).toHaveTextContent("Creates a new file that removes the selected region or keeps only that region.");
    expect(help).toHaveTextContent("Creates a new file with louder audio.");
    expect(help).toHaveTextContent("Uploads the current audio and copies a public link without changing the note.");
    expect(help).toHaveTextContent("Every edit creates a new media file and updates the field to point at it.");
    expect(help).toHaveTextContent("grey is loudness and lines are pitch of the voice.");
    expect(document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-denoise-standard"]')?.title).toBe(
      "Remove noise and music using Standard",
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
    expect(dpdfnetPreset.title).toBe("Denoise speech with DPDFNet, Aggressiveness: Gentle");
    dpdfnetPreset.click();
    await Promise.resolve();
    expect(document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-denoise-standard"]')?.title).toBe(
      "Remove noise and music using DPDFNet",
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
        speedStep: 0.05,
        volumeStepDb: 3,
      },
    };
    initializeEditorRuntime(config);
    scan(config);
    await Promise.resolve();
    window.__aqeSetBusy?.(0, false);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-graph-menu"]')!.click();
    await Promise.resolve();
    for (const [slug, value] of [
      ["voice-range", "4"],
      ["recording-condition", "5"],
      ["smoothness", "3"],
      ["connect-dropouts", "90"],
      ["voice-lock", "2"],
    ] as const) {
      const input = document.querySelector<HTMLInputElement>(`[data-testid="aqe-split-0-graph-${slug}"]`)!;
      input.value = value;
      input.dispatchEvent(new Event("input", { bubbles: true }));
    }
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
        speedStep: 0.05,
        volumeStepDb: 3,
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

  it("dispatches share commands with the selected host and no save-default button", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-share-menu"]')!.click();
    await Promise.resolve();

    expect(document.querySelector('[data-testid="aqe-split-0-share-save-default"]')).toBeNull();

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-share-preset-catbox"]')!.click();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-share"]')!.click();

    expect(bridgeCommands()).toContain("aqe:command-payload");
    expect(window.__aqePendingCommandPayload).toMatchObject({
      command: "aqe:share",
      fieldOrd: 0,
      shareTarget: "catbox",
    });
  });

  it("dispatches volume and speed split payloads with local values", async () => {
    window.__AQE_EDITOR_CONFIG__ = {
      audioFieldIndices: [0],
      splitButtonDefaults: {
        denoiseAlgorithm: "standard",
        pauseAggressiveness: "normal",
        repeatPauseSeconds: 0,
        speedStep: 0.05,
        volumeStepDb: 3,
      },
    };
    initializeEditorRuntime(window.__AQE_EDITOR_CONFIG__);
    scan(window.__AQE_EDITOR_CONFIG__);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-volume-up-menu"]')!.click();
    await Promise.resolve();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-volume-up-preset-6"]')!.click();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-volume-up"]')!.click();
    const volumePayload = window.__aqePendingCommandPayload as EditorCommandPayload | null | undefined;
    window.__aqePendingCommandPayload = null;
    window.__aqeSetBusy?.(0, false);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-faster-menu"]')!.click();
    await Promise.resolve();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-faster-preset-0.1"]')!.click();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-faster"]')!.click();

    expect(volumePayload?.overrides?.volumeStepDb).toBe(6);
    const speedPayload = window.__aqePendingCommandPayload as EditorCommandPayload | null | undefined;
    expect(speedPayload?.overrides?.speedStep).toBe(0.1);
  });

  it("syncs split tooltip value inputs with sliders", async () => {
    window.__aqeSplitButtonStates = {};
    window.__AQE_EDITOR_CONFIG__ = {
      audioFieldIndices: [0],
      splitButtonDefaults: {
        denoiseAlgorithm: "standard",
        pauseAggressiveness: "normal",
        repeatPauseSeconds: 0,
        speedStep: 0.05,
        volumeStepDb: 3,
      },
    };
    initializeEditorRuntime(window.__AQE_EDITOR_CONFIG__);
    scan(window.__AQE_EDITOR_CONFIG__);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-volume-up-menu"]')!.click();
    await Promise.resolve();
    const volumeInput = document.querySelector<HTMLInputElement>('[data-testid="aqe-split-0-volume-up-value"]')!;
    const volumeSlider = document.querySelector<HTMLInputElement>('[data-testid="aqe-split-0-volume-up-slider"]')!;
    volumeInput.value = "6.5";
    volumeInput.dispatchEvent(new Event("input", { bubbles: true }));
    await Promise.resolve();
    expect(volumeSlider.value).toBe("6.5");
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-volume-up"]')!.click();
    const volumePayload = window.__aqePendingCommandPayload as EditorCommandPayload | null | undefined;
    expect(volumePayload?.overrides?.volumeStepDb).toBe(6.5);
    window.__aqePendingCommandPayload = null;
    window.__aqeSetBusy?.(0, false);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-slower-menu"]')!.click();
    await Promise.resolve();
    const slowerInput = document.querySelector<HTMLInputElement>('[data-testid="aqe-split-0-slower-value"]')!;
    const slowerSlider = document.querySelector<HTMLInputElement>('[data-testid="aqe-split-0-slower-slider"]')!;
    expect(slowerInput.value).toBe("0.95");
    slowerInput.value = "0.88";
    slowerInput.dispatchEvent(new Event("input", { bubbles: true }));
    await Promise.resolve();
    expect(slowerSlider.value).toBe("0.12");
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-slower"]')!.click();
    const speedPayload = window.__aqePendingCommandPayload as EditorCommandPayload | null | undefined;
    expect(speedPayload?.overrides?.speedStep).toBe(0.12);
  });

  it("dispatches pause aggressiveness split payloads with local values", async () => {
    window.__AQE_EDITOR_CONFIG__ = {
      audioFieldIndices: [0],
      splitButtonDefaults: {
        denoiseAlgorithm: "standard",
        pauseAggressiveness: "normal",
        repeatPauseSeconds: 0,
        speedStep: 0.05,
        volumeStepDb: 3,
      },
    };
    initializeEditorRuntime(window.__AQE_EDITOR_CONFIG__);
    scan(window.__AQE_EDITOR_CONFIG__);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-remove-pauses-menu"]')!.click();
    await Promise.resolve();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-remove-pauses-preset-aggressive"]')!.click();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-remove-pauses"]')!.click();

    expect(bridgeCommands()).toContain("aqe:command-payload");
    expect(window.__aqePendingCommandPayload).toMatchObject({
      command: "aqe:remove-pauses",
      fieldOrd: 0,
      overrides: {
        pauseAggressiveness: "aggressive",
      },
    });
  });

});
