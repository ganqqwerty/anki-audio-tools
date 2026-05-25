import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  disposeEditorRuntime,
  initializeEditorRuntime,
  scan,
} from "../src/editor-inline/runtime.js";
import { PRODUCT_LINKS } from "../src/lib/product-links.js";
import {
  muteConsole,
  openPlayOptions,
  renderFields,
} from "./editor-inline.integration.helpers.js";

describe("editor inline play option integration", () => {
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

  it("renders repeat as a Play split option and initializes it from runtime config", async () => {
    const config = {
      audioFieldIndices: [0],
      repeatPlaybackByDefault: true,
      splitButtonDefaults: {
        denoiseAlgorithm: "standard" as const,
        pauseAggressiveness: "normal" as const,
        repeatPauseSeconds: 1.5,
        speedStep: 1.5,
        volumeStepDb: 15,
      },
    };
    initializeEditorRuntime(config);
    scan(config);
    await Promise.resolve();

    const playMenu = document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-play-menu"]');
    expect(playMenu).toHaveAttribute("data-aqe-tooltip-content", "Play quick settings.");
    await openPlayOptions();

    const repeat = document.querySelector<HTMLButtonElement>('[data-testid="aqe-repeat-0"]');
    expect(repeat).toHaveAttribute("aria-pressed", "true");
    expect(repeat?.closest(".aqe-split-button")).not.toBeNull();
    expect(window.__aqeGraphStateForTest?.(0)?.repeatPauseSeconds).toBe(1.5);

    const input = document.querySelector<HTMLInputElement>('[data-testid="aqe-split-0-repeat-value"]')!;
    const slider = document.querySelector<HTMLInputElement>('[data-testid="aqe-split-0-repeat-slider"]')!;
    expect(document.querySelector('[data-testid="aqe-split-0-play-popover"]')).not.toBeNull();
    expect(
      document.querySelector<HTMLElement>('[data-testid="aqe-split-0-play-popover"] .aqe-split-popover-title')?.textContent?.trim(),
    ).toBe("Play");
    expect(document.querySelector('[data-testid="aqe-split-0-play-popover"]')).toHaveTextContent(
      "Playback and repeat options for this field.",
    );
    expect(
      document.querySelector<HTMLAnchorElement>('[data-testid="aqe-split-0-play-popover"] .aqe-split-video-link'),
    ).toHaveAttribute("href", PRODUCT_LINKS.editorVideos.playback);
    expect(input.value).toBe("1.5");
    expect(slider.value).toBe("1.5");

    slider.value = "2";
    slider.dispatchEvent(new Event("input", { bubbles: true }));
    await Promise.resolve();
    expect(input.value).toBe("2");
    expect(window.__aqeGraphStateForTest?.(0)?.repeatPauseSeconds).toBe(2);

    input.value = "0.5";
    input.dispatchEvent(new Event("input", { bubbles: true }));
    await Promise.resolve();
    expect(slider.value).toBe("0.5");
    expect(window.__aqeGraphStateForTest?.(0)?.repeatPauseSeconds).toBe(0.5);

    repeat?.click();

    expect(window.__aqeGraphStateForTest?.(0)?.repeatEnabled).toBe(false);
    expect(repeat).toHaveAttribute("aria-pressed", "false");
    expect(playMenu).toHaveAttribute("data-aqe-tooltip-content", "Play quick settings.");
  });
});
