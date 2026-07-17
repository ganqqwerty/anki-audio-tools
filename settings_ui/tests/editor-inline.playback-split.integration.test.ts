import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import {
  muteConsole,
  renderFields,
  track,
} from "./editor-inline.integration.helpers.js";

describe("editor inline Play split menu", () => {
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

  it("enables selected-repeat auto-advance controls only when repeat is selected", async () => {
    const config = {
      audioFieldIndices: [0],
      splitButtonDefaults: {
        chorusingAutoAdvanceByDefault: true,
        chorusingAutoAdvanceRepeats: 5,
        denoiseAlgorithm: "standard" as const,
        pauseAggressiveness: "normal" as const,
        repeatPauseSeconds: 0,
        speedStep: 1.5,
        volumeStepDb: 15,
      },
    };
    initializeEditorRuntime(config);
    scan(config);
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 0);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-play-menu"]')!.click();
    await Promise.resolve();
    await Promise.resolve();

    const autoAdvance = document.querySelector<HTMLInputElement>('[data-testid="aqe-split-0-play-auto-advance"]')!;
    const repeats = document.querySelector<HTMLInputElement>('[data-testid="aqe-split-0-play-auto-advance-repeats"]')!;
    const repeat = document.querySelector<HTMLInputElement>('[data-testid="aqe-repeat-0"]')!;
    expect(autoAdvance).not.toBeNull();
    expect(repeats).not.toBeNull();
    expect(autoAdvance.disabled).toBe(true);
    expect(autoAdvance.checked).toBe(false);
    expect(repeats.disabled).toBe(true);
    expect(repeats.value).toBe("5");

    autoAdvance.click();
    repeats.value = "4";
    repeats.dispatchEvent(new Event("input", { bubbles: true }));
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-play-save-default"]')!.click();

    expect(window.__aqePopPendingSplitDefaultSaveRequest?.()).toMatchObject({
      defaults: {
        chorusingAutoAdvanceByDefault: false,
        chorusingAutoAdvanceRepeats: 5,
        repeatPauseSeconds: 0,
        repeatPlaybackByDefault: false,
      },
      fieldOrd: 0,
    });

    repeat.click();
    await Promise.resolve();
    expect(repeat.checked).toBe(true);
    expect(autoAdvance.disabled).toBe(false);
    expect(autoAdvance.checked).toBe(false);
    expect(repeats.disabled).toBe(false);

    autoAdvance.click();
    repeats.value = "4";
    repeats.dispatchEvent(new Event("input", { bubbles: true }));
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-play-save-default"]')!.click();

    expect(window.__aqePopPendingSplitDefaultSaveRequest?.()).toMatchObject({
      defaults: {
        chorusingAutoAdvanceByDefault: true,
        chorusingAutoAdvanceRepeats: 4,
        repeatPauseSeconds: 0,
        repeatPlaybackByDefault: true,
      },
      fieldOrd: 0,
    });
  });
});
