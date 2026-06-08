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

  it("dispatches pause aggressiveness split payloads with local values", async () => {
    window.__AQE_EDITOR_CONFIG__ = {
      audioFieldIndices: [0],
      splitButtonDefaults: {
        denoiseAlgorithm: "standard",
        pauseAggressiveness: "normal",
        repeatPauseSeconds: 0,
        speedStep: 1.5,
        volumeStepDb: 15,
      },
    };
    initializeEditorRuntime(window.__AQE_EDITOR_CONFIG__);
    scan(window.__AQE_EDITOR_CONFIG__);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-remove-pauses-menu"]')!.click();
    await Promise.resolve();
    const popover = document.querySelector<HTMLElement>('[data-testid="aqe-split-0-remove-pauses-popover"]')!;
    expect(popover.querySelector('[data-testid="aqe-split-0-remove-pauses-pause-threshold-help"]')).not.toBeNull();
    expect(popover.querySelector('[data-testid="aqe-split-0-remove-pauses-pause-min-speech-seconds-help"]')).not.toBeNull();
    expect(popover.querySelector('[data-testid="aqe-split-0-remove-pauses-pause-preprocess-denoise-help"]')).not.toBeNull();
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

  it("dispatches size reduction split payloads with advanced params", async () => {
    window.__AQE_EDITOR_CONFIG__ = {
      audioFieldIndices: [0],
      audioFieldSources: {
        0: "clip one.mp3",
      },
      splitButtonDefaults: {
        denoiseAlgorithm: "standard",
        pauseAggressiveness: "normal",
        repeatPauseSeconds: 0,
        sizeReductionMode: "normal",
        sizeReductionBitrateKbps: 64,
        sizeReductionSampleRateHz: 32000,
        sizeReductionChannels: 1,
        speedStep: 1.5,
        volumeStepDb: 15,
      },
    };
    initializeEditorRuntime(window.__AQE_EDITOR_CONFIG__);
    scan(window.__AQE_EDITOR_CONFIG__);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-reduce-size-menu"]')!.click();
    await Promise.resolve();
    const popover = document.querySelector<HTMLElement>('[data-testid="aqe-split-0-reduce-size-popover"]')!;
    expect(popover.querySelector('[data-testid="aqe-split-0-reduce-size-size-reduction-bitrate-kbps-help"]')).not.toBeNull();
    expect(bridgeCommands()).not.toContain("aqe:source-metadata");
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-reduce-size-preset-gentle"]')!.click();
    const bitrateInput = document.querySelector<HTMLInputElement>(
      '[data-testid="aqe-split-0-reduce-size-size-reduction-bitrate-kbps"]',
    )!;
    bitrateInput.value = "80";
    bitrateInput.dispatchEvent(new Event("input", { bubbles: true }));
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-reduce-size"]')!.click();

    expect(window.__aqePendingCommandPayload).toMatchObject({
      command: "aqe:reduce-size",
      fieldOrd: 0,
      overrides: {
        sizeReductionMode: "gentle",
        sizeReductionBitrateKbps: 80,
        sizeReductionSampleRateHz: 44100,
        sizeReductionChannels: 2,
      },
    });
  });
});
