import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  disposeEditorRuntime,
  initializeEditorRuntime,
  scan,
} from "../src/editor-inline/runtime.js";
import { PRODUCT_LINKS } from "../src/lib/product-links.js";
import {
  muteConsole,
  renderFields,
} from "./editor-inline.integration.helpers.js";

describe("editor inline split-menu content", () => {
  let restoreConsole: () => void;

  beforeEach(() => {
    restoreConsole = muteConsole();
    renderFields();
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
  });

  afterEach(() => {
    disposeEditorRuntime();
    restoreConsole();
    vi.restoreAllMocks();
  });

  it("shows format and pause aggressiveness descriptions", async () => {
    const convertPopover = await openSplitPopover("convert");

    expect(convertPopover).toHaveTextContent("Most portable. Guaranteed to work in AnkiMobile");
    expect(convertPopover).toHaveTextContent("Small modern file with good quality");
    expect(convertPopover).toHaveTextContent("Uncompressed and large");
    expect(convertPopover).toHaveTextContent("Lossless and smaller than WAV");

    const pausePopover = await openSplitPopover("remove-pauses");

    expect(pausePopover).toHaveTextContent("700 ms");
    expect(pausePopover).toHaveTextContent("450 ms");
    expect(pausePopover).toHaveTextContent("250 ms");
    expect(pausePopover).toHaveTextContent("rushed");
  });

  it("shows corresponding video links for command and grouped split menus", async () => {
    const cases = [
      ["graph", PRODUCT_LINKS.editorVideos.graph],
      ["share", PRODUCT_LINKS.editorVideos.share],
      ["convert", PRODUCT_LINKS.editorVideos.convert],
      ["remove-pauses", PRODUCT_LINKS.editorVideos.pauseShortening],
      ["volume", PRODUCT_LINKS.editorVideos.volume],
      ["speed", PRODUCT_LINKS.editorVideos.speed],
    ] as const;

    for (const [slug, expectedUrl] of cases) {
      const popover = await openSplitPopover(slug);
      expect(popover.querySelector<HTMLAnchorElement>(".aqe-split-video-link")).toHaveAttribute("href", expectedUrl);
      expect(popover.querySelector(".aqe-split-video-link")).toHaveTextContent("See video");
    }
  });
});

async function openSplitPopover(slug: string): Promise<HTMLElement> {
  document.querySelector<HTMLButtonElement>(`[data-testid="aqe-split-0-${slug}-menu"]`)!.click();
  await Promise.resolve();
  return document.querySelector<HTMLElement>(`[data-testid="aqe-split-0-${slug}-popover"]`)!;
}
