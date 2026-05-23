import { waitFor } from "@testing-library/svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import { bridgeCommands, muteConsole, renderFields } from "./editor-inline.integration.helpers.js";

async function openVolumePopover(): Promise<HTMLDivElement> {
  const menu = document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-volume-menu"]')!;
  menu.click();

  let popover: HTMLDivElement | null = null;
  await waitFor(() => {
    popover = document.querySelector<HTMLDivElement>('[data-testid="aqe-split-0-volume-popover"]');
    expect(popover).not.toBeNull();
    expect(popover!.dataset.side).toBeTruthy();
  });

  return popover!;
}

describe("split button popover behavior", () => {
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

  it("opens a bits-ui popover with arrow metadata from the split trigger", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    const menu = document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-volume-menu"]')!;
    expect(menu).toHaveAttribute("aria-expanded", "false");

    const popover = await openVolumePopover();
    const arrow = document.querySelector<HTMLElement>('[data-testid="aqe-split-0-volume-arrow"]');

    expect(menu).toHaveAttribute("aria-expanded", "true");
    expect(popover).toHaveAttribute("data-align", "center");
    expect(popover).toHaveAttribute("data-side");
    expect(arrow).not.toBeNull();
    expect(arrow).toHaveAttribute("data-side", popover.dataset.side);
  });

  it("closes the split popover on Escape", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    const menu = document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-volume-menu"]')!;
    await openVolumePopover();

    document.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, key: "Escape" }));

    await waitFor(() => {
      expect(document.querySelector('[data-testid="aqe-split-0-volume-popover"]')).toBeNull();
      expect(menu).toHaveAttribute("aria-expanded", "false");
    });
  });

  it("queues a split default save request from the popover header", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await openVolumePopover();

    const slider = document.querySelector<HTMLInputElement>('[data-testid="aqe-split-0-volume-slider"]')!;
    slider.value = "6";
    slider.dispatchEvent(new Event("input", { bubbles: true }));
    const save = document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-volume-save-default"]')!;

    expect(save.title).toBe("Promote these settings to default");
    save.click();

    expect(bridgeCommands()).toContain("aqe:save-split-defaults");
    expect(window.__aqePopPendingSplitDefaultSaveRequest?.()).toEqual({
      defaults: {
        volumeStepDb: 6,
      },
      fieldOrd: 0,
    });
    expect(window.__AQE_EDITOR_CONFIG__?.splitButtonDefaults?.volumeStepDb).toBe(6);
    await waitFor(() => expect(save).toHaveClass("aqe-split-default-save-saved"));
  });
});
