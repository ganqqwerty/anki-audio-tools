import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  disposeEditorRuntime,
  initializeEditorRuntime,
  scan,
} from "../src/editor-inline/runtime.js";
import {
  bridgeCommands,
  muteConsole,
  renderFields,
} from "./editor-inline.integration.helpers.js";

describe("editor inline Voice Only integration", () => {
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

  it("dispatches Voice Only from the denoise split menu", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-denoise-standard-menu"]')!.click();
    await Promise.resolve();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-denoise-standard-preset-voice_only"]')!.click();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-denoise-standard"]')!.click();

    expect(bridgeCommands()).toContain("aqe:command-payload");
    expect(window.__aqePendingCommandPayload).toMatchObject({
      command: "aqe:voice-only",
      fieldOrd: 0,
      overrides: {
        denoiseAlgorithm: "voice_only",
      },
    });
  });
});
