import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  disposeEditorRuntime,
  initializeEditorRuntime,
  scan,
} from "../src/editor-inline/runtime.js";
import type { EditorCommandPayload } from "../src/editor-inline/types.js";
import {
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

  it("dispatches volume and speed split payloads with local values", async () => {
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

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-volume-menu"]')!.click();
    await Promise.resolve();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-volume-preset-6"]')!.click();
    expect(document.querySelector('[data-testid="aqe-split-0-volume-up-menu"]')).toBeNull();
    expect(document.querySelector('[data-testid="aqe-split-0-volume-down-menu"]')).toBeNull();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-volume-down"]')!.click();
    const quieterPayload = window.__aqePendingCommandPayload as EditorCommandPayload | null | undefined;
    window.__aqePendingCommandPayload = null;
    window.__aqeSetBusy?.(0, false);
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-volume-up"]')!.click();
    const louderPayload = window.__aqePendingCommandPayload as EditorCommandPayload | null | undefined;
    window.__aqePendingCommandPayload = null;
    window.__aqeSetBusy?.(0, false);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-speed-menu"]')!.click();
    await Promise.resolve();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-speed-preset-2"]')!.click();
    expect(document.querySelector('[data-testid="aqe-split-0-faster-menu"]')).toBeNull();
    expect(document.querySelector('[data-testid="aqe-split-0-slower-menu"]')).toBeNull();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-slower"]')!.click();
    const slowerPayload = window.__aqePendingCommandPayload as EditorCommandPayload | null | undefined;
    window.__aqePendingCommandPayload = null;
    window.__aqeSetBusy?.(0, false);
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-faster"]')!.click();

    expect(quieterPayload?.command).toBe("aqe:volume-down");
    expect(quieterPayload?.overrides?.volumeStepDb).toBe(6);
    expect(louderPayload?.command).toBe("aqe:volume-up");
    expect(louderPayload?.overrides?.volumeStepDb).toBe(6);
    expect(slowerPayload?.command).toBe("aqe:slower");
    expect(slowerPayload?.overrides?.speedStep).toBe(2);
    const fasterPayload = window.__aqePendingCommandPayload as EditorCommandPayload | null | undefined;
    expect(fasterPayload?.command).toBe("aqe:faster");
    expect(fasterPayload?.overrides?.speedStep).toBe(2);
  });

  it("shows grouped split hover text and keeps volume execution on the primary buttons", async () => {
    window.__aqeSplitButtonStates = {};
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

    const menu = document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-volume-menu"]')!;
    expect(menu.getAttribute("data-aqe-tooltip-content")).toBe("Volume quick settings.");

    menu.click();
    await Promise.resolve();

    const header = document.querySelector<HTMLElement>('[data-testid="aqe-split-0-volume-popover"] .aqe-split-popover-title')!;
    expect(header.textContent?.trim()).toBe("Volume");
    expect(document.querySelector('[data-testid="aqe-split-0-volume-popover"]')).toHaveTextContent(
      "How much louder or quieter to make the audio.",
    );
    expect(document.querySelector('[data-testid="aqe-split-0-volume-run"]')).toBeNull();
    expect(document.querySelector('[data-testid="aqe-split-0-volume-run-volume-down"]')).not.toBeNull();
    expect(document.querySelector('[data-testid="aqe-split-0-volume-run-volume-up"]')).not.toBeNull();

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-volume-preset-6"]')!.click();
    await Promise.resolve();
    expect(menu.getAttribute("data-aqe-tooltip-content")).toBe("Volume quick settings.");

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-volume-up"]')!.click();

    expect(window.__aqePendingCommandPayload).toMatchObject({
      command: "aqe:volume-up",
      fieldOrd: 0,
      overrides: {
        volumeStepDb: 6,
      },
    });
    await Promise.resolve();
    expect(document.querySelector('[data-testid="aqe-split-0-volume-popover"]')).toBeNull();
  });

  it("syncs split tooltip value inputs with sliders", async () => {
    window.__aqeSplitButtonStates = {};
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

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-volume-menu"]')!.click();
    await Promise.resolve();
    const volumeInput = document.querySelector<HTMLInputElement>('[data-testid="aqe-split-0-volume-value"]')!;
    const volumeSlider = document.querySelector<HTMLInputElement>('[data-testid="aqe-split-0-volume-slider"]')!;
    volumeInput.value = "6.5";
    volumeInput.dispatchEvent(new Event("input", { bubbles: true }));
    await Promise.resolve();
    expect(volumeSlider.value).toBe("6.5");
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-volume-up"]')!.click();
    const volumePayload = window.__aqePendingCommandPayload as EditorCommandPayload | null | undefined;
    expect(volumePayload?.overrides?.volumeStepDb).toBe(6.5);
    window.__aqePendingCommandPayload = null;
    window.__aqeSetBusy?.(0, false);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-speed-menu"]')!.click();
    await Promise.resolve();
    const speedInput = document.querySelector<HTMLInputElement>('[data-testid="aqe-split-0-speed-value"]')!;
    const speedSlider = document.querySelector<HTMLInputElement>('[data-testid="aqe-split-0-speed-slider"]')!;
    expect(speedInput.value).toBe("1.5");
    speedInput.value = "2";
    speedInput.dispatchEvent(new Event("input", { bubbles: true }));
    await Promise.resolve();
    expect(speedSlider.value).toBe("2");
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-slower"]')!.click();
    const speedPayload = window.__aqePendingCommandPayload as EditorCommandPayload | null | undefined;
    expect(speedPayload?.overrides?.speedStep).toBe(2);
  });
});
