import { waitFor } from "@testing-library/svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import { muteConsole, renderFields } from "./editor-inline.integration.helpers.js";

const DEFAULT_VIEWPORT_WIDTH = window.innerWidth;
const DEFAULT_VIEWPORT_HEIGHT = window.innerHeight;

interface TestRect {
  left: number;
  top: number;
  width: number;
  height: number;
}

function domRect({ left, top, width, height }: TestRect): DOMRect {
  return {
    bottom: top + height,
    height,
    left,
    right: left + width,
    top,
    width,
    x: left,
    y: top,
    toJSON: () => ({}),
  } as DOMRect;
}

function setViewport(width: number, height: number): void {
  Object.defineProperty(window, "innerWidth", { configurable: true, value: width });
  Object.defineProperty(window, "innerHeight", { configurable: true, value: height });
}

function mockSplitPopoverBounds(anchor: TestRect, popover: TestRect): void {
  vi.spyOn(Element.prototype, "getBoundingClientRect").mockImplementation(function getBoundingClientRect(
    this: Element,
  ) {
    if (this.classList.contains("aqe-split-button")) return domRect(anchor);
    if (this.classList.contains("aqe-split-popover")) return domRect(popover);
    return domRect({ left: 0, top: 0, width: 0, height: 0 });
  });
}

async function openTrimPopover(): Promise<HTMLDivElement> {
  document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-trim-left-menu"]')!.click();
  let popover: HTMLDivElement | null = null;
  await waitFor(() => {
    popover = document.querySelector<HTMLDivElement>('[data-testid="aqe-split-0-trim-left-popover"]');
    expect(popover).not.toBeNull();
    expect(popover!.style.left).not.toBe("");
    expect(popover!.style.top).not.toBe("");
  });
  return popover!;
}

function numericStyle(element: HTMLElement, property: "left" | "top"): number {
  return Number.parseFloat(element.style[property]);
}

describe("split button popover placement", () => {
  let restoreConsole: () => void;

  beforeEach(() => {
    restoreConsole = muteConsole();
    renderFields();
  });

  afterEach(() => {
    disposeEditorRuntime();
    restoreConsole();
    setViewport(DEFAULT_VIEWPORT_WIDTH, DEFAULT_VIEWPORT_HEIGHT);
    vi.restoreAllMocks();
  });

  it("centers split popovers under their button when there is enough room", async () => {
    setViewport(800, 600);
    mockSplitPopoverBounds(
      { left: 300, top: 100, width: 60, height: 28 },
      { left: 0, top: 0, width: 210, height: 140 },
    );
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    const popover = await openTrimPopover();

    expect(numericStyle(popover, "left")).toBe(225);
    expect(numericStyle(popover, "top")).toBe(132);
  });

  it("clamps split popovers inside the right viewport edge", async () => {
    setViewport(320, 600);
    mockSplitPopoverBounds(
      { left: 270, top: 100, width: 40, height: 28 },
      { left: 0, top: 0, width: 210, height: 140 },
    );
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    const popover = await openTrimPopover();

    expect(numericStyle(popover, "left")).toBe(102);
    expect(numericStyle(popover, "left") + 210).toBeLessThanOrEqual(312);
  });

  it("flips split popovers above their button near the bottom viewport edge", async () => {
    setViewport(800, 240);
    mockSplitPopoverBounds(
      { left: 300, top: 200, width: 60, height: 28 },
      { left: 0, top: 0, width: 210, height: 140 },
    );
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    const popover = await openTrimPopover();

    expect(numericStyle(popover, "top")).toBe(56);
    expect(numericStyle(popover, "top") + 140).toBeLessThanOrEqual(232);
  });

  it("keeps closing split popovers on outside click after placement", async () => {
    setViewport(800, 600);
    mockSplitPopoverBounds(
      { left: 300, top: 100, width: 60, height: 28 },
      { left: 0, top: 0, width: 210, height: 140 },
    );
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await openTrimPopover();

    document.body.dispatchEvent(new MouseEvent("mousedown", { bubbles: true }));
    await Promise.resolve();

    expect(document.querySelector('[data-testid="aqe-split-0-trim-left-popover"]')).toBeNull();
  });
});
