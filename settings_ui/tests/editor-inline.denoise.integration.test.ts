import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import { bridgeCommands, muteConsole, renderFields } from "./editor-inline.integration.helpers.js";

describe("editor inline denoise integration", () => {
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
        dpdfnetAttnLimitDb: 18,
        pauseAggressiveness: "normal" as const,
        repeatPauseSeconds: 0,
        speedStep: 0.05,
        trimStepMs: 100,
        volumeStepDb: 3,
      },
    };
    initializeEditorRuntime(config);
    scan(config);

    const help = document.querySelector<HTMLDetailsElement>('[data-testid="aqe-help-0"]')!;
    expect(help.open).toBe(false);
    expect(help.querySelectorAll(".aqe-help-command")).toHaveLength(14);
    expect(help.querySelector(".aqe-help-triangle")).not.toBeNull();
    expect(help).toHaveTextContent("Shift-drag on the graph to select a region.");
    expect(help).toHaveTextContent("Delete Region removes the selected region; Delete the rest keeps only the selected region.");
    expect(help).toHaveTextContent("Delete Region / Delete the rest");
    expect(help).toHaveTextContent("Creates a new file that removes the selected region or keeps only that region.");
    expect(help).toHaveTextContent("Creates a new file with louder audio.");
    expect(help).toHaveTextContent("Every edit creates a new media file and updates the field to point at it.");
    expect(help).toHaveTextContent("grey is loudness and lines are pitch of the voice.");
    expect(document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-denoise-standard"]')?.title).toBe(
      "Denoise speech with DeepFilterNet",
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
    expect(dpdfnetPreset.title).toBe("Denoise speech with DPDFNet, Aggressiveness: Aggressive");
    dpdfnetPreset.click();
    await Promise.resolve();
    expect(
      document.querySelector<HTMLSelectElement>(
        '[data-testid="aqe-split-0-denoise-standard-dpdfnet-aggressiveness"]',
      )?.value,
    ).toBe("18");
    expect(document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-denoise-standard"]')?.title).toBe(
      "Denoise speech with DPDFNet, Aggressiveness: Aggressive",
    );
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-denoise-standard"]')!.click();
    expect(window.__aqePendingCommandPayload?.command).toBe("aqe:dpdfnet");
    expect(window.__aqePendingCommandPayload?.fieldOrd).toBe(0);
    expect(window.__aqePendingCommandPayload?.overrides?.denoiseAlgorithm).toBe("dpdfnet");
    expect(window.__aqePendingCommandPayload?.overrides?.dpdfnetAttnLimitDb).toBe(18);
  });
});
