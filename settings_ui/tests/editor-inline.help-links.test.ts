import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import { PRODUCT_LINKS } from "../src/lib/product-links.js";
import { bridgeCommands, muteConsole, renderFields } from "./editor-inline.integration.helpers.js";

describe("editor inline help links", () => {
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

  it("opens resource links through the editor bridge", () => {
    const config = {
      audioFieldIndices: [0],
      splitButtonDefaults: {
        denoiseAlgorithm: "standard" as const,
        pauseAggressiveness: "normal" as const,
        repeatPauseSeconds: 0,
        speedStep: 1.5,
        volumeStepDb: 15,
      },
    };
    initializeEditorRuntime(config);
    scan(config);

    const link = document.querySelector<HTMLAnchorElement>(`a[href="${PRODUCT_LINKS.githubPages}"]`)!;
    const click = new MouseEvent("click", { bubbles: true, cancelable: true });

    expect(link.dispatchEvent(click)).toBe(false);
    expect(bridgeCommands()).toContain("aqe:command-payload");
    expect(window.__aqePendingCommandPayload).toEqual({
      command: "aqe:open-url",
      url: PRODUCT_LINKS.githubPages,
    });
  });

  it("opens video links through the editor bridge", () => {
    const config = {
      audioFieldIndices: [0],
      splitButtonDefaults: {
        denoiseAlgorithm: "standard" as const,
        pauseAggressiveness: "normal" as const,
        repeatPauseSeconds: 0,
        speedStep: 1.5,
        volumeStepDb: 15,
      },
    };
    initializeEditorRuntime(config);
    scan(config);

    const link = document.querySelector<HTMLAnchorElement>(
      `a[href="${PRODUCT_LINKS.editorVideos.pitchHum}"]`,
    )!;
    const click = new MouseEvent("click", { bubbles: true, cancelable: true });

    expect(link).toHaveClass("aqe-help-text-link");
    expect(link.closest(".aqe-help-description")).not.toBeNull();
    expect(link.closest(".aqe-help-link-row")).toBeNull();
    const helpTitles = [...document.querySelectorAll(".aqe-help-title")].map((title) => title.textContent);
    expect(helpTitles).not.toContain("Videos");
    expect(link.dispatchEvent(click)).toBe(false);
    expect(window.__aqePendingCommandPayload).toEqual({
      command: "aqe:open-url",
      url: PRODUCT_LINKS.editorVideos.pitchHum,
    });
  });
});
