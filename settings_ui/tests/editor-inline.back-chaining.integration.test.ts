import { readFileSync } from "node:fs";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import {
  dragGraphSelection,
  graphClientX,
  muteConsole,
  openPlayOptions,
  prepareHtmlAudio,
  renderFields,
  setGraphBounds,
  track,
} from "./editor-inline.integration.helpers.js";

const visualizerCss = readFileSync(
  "src/editor-inline/styles/visualizer.css",
  "utf8",
);
const selectionCss = readFileSync(
  "src/editor-inline/styles/selection.css",
  "utf8",
);

describe("editor inline back-chaining integration", () => {
  let restoreConsole: () => void;

  beforeEach(() => {
    installVisualizerStyles();
    restoreConsole = muteConsole();
    renderFields();
  });

  afterEach(() => {
    disposeEditorRuntime();
    restoreConsole();
    vi.restoreAllMocks();
  });

  it("shows practice controls for a committed graph selection and edits markers", async () => {
    const { row, svg } = await prepareBackChainingSelection();
    await openPlayOptions();
    const playPopover = document.querySelector<HTMLElement>('[data-testid="aqe-split-0-play-popover"]')!;
    expect(playPopover.querySelector('[data-testid="aqe-back-chaining-0-edit"]')).toBeNull();

    await enterBackChaining();
    const panel = document.querySelector<HTMLElement>('[data-testid="aqe-back-chaining-0-panel"]')!;
    const edit = panel.querySelector<HTMLButtonElement>('[data-testid="aqe-back-chaining-0-edit"]')!;
    expect(edit).not.toBeNull();
    expect(edit.disabled).toBe(false);
    expect(panel.closest('[data-testid="aqe-selection-toolbar-0"]')).not.toBeNull();
    const videoLink = panel.querySelector<HTMLAnchorElement>(".aqe-back-chaining-video-link")!;
    expect(videoLink.textContent).toBe("See video");
    const linkClick = new MouseEvent("click", { bubbles: true, cancelable: true });
    videoLink.dispatchEvent(linkClick);
    expect(linkClick.defaultPrevented).toBe(true);
    expectIconOnlyButton(panel, "previous", "Previous");
    expectIconOnlyButton(panel, "next", "Next");
    expectIconOnlyButton(panel, "clear", "Clear markers");
    expect(panel.querySelector('[data-testid="aqe-back-chaining-0-exit"]')).toBeNull();
    for (const button of panel.querySelectorAll<HTMLButtonElement>(".aqe-back-chaining-button")) {
      expectPointerGuards(button);
    }
    expect(row.querySelectorAll(".aqe-back-chaining-boundary-marker")).toHaveLength(1);
    expect(row.closest('[data-testid="aqe-graph-svg-0"]')).not.toBeNull();
    const trackRect = row.querySelector<SVGRectElement>(".aqe-back-chaining-marker-track")!;
    expect(getComputedStyle(trackRect).fill.replaceAll(",", "")).toBe("rgb(255 255 255)");
    expect(trackRect.getAttribute("y")).toBe("10.00");
    expect(trackRect.hasAttribute("rx")).toBe(false);
    expect(row.querySelector(".aqe-back-chaining-base-range")).toBeNull();
    expect(row.querySelector(".aqe-back-chaining-active-range")).toBeNull();
    expect(getComputedStyle(row).opacity).toBe("1");
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      backChainingBaseEndMs: 800,
      backChainingBaseStartMs: 200,
      backChainingEditing: true,
      backChainingMarkersMs: [200, 400, 600],
    });

    clickMarkerRow(row, svg, 0.4);
    clickMarkerRow(row, svg, 0.7);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      backChainingBaseEndMs: 800,
      backChainingBaseStartMs: 200,
      backChainingEditing: true,
      backChainingMarkersMs: [200, 600, 700],
    });

    clickMarkerRow(row, svg, 0.705);
    expect(window.__aqeGraphStateForTest?.(0)?.backChainingMarkersMs).toEqual([200, 600]);

    panel.querySelector<HTMLButtonElement>('[data-testid="aqe-back-chaining-0-clear"]')!.click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      backChainingBaseEndMs: 800,
      backChainingBaseStartMs: 200,
      backChainingEditing: true,
      backChainingMarkersMs: [],
      backChainingPanelOpen: true,
    });
  });

  it("places markers using zoomed viewport time rather than full duration", async () => {
    const { row, svg } = await prepareBackChainingSelection();
    await enterBackChaining();
    window.__aqeSetTimeViewportForTest?.(0, 200, 800);

    clickMarkerRow(row, svg, 0.5);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      backChainingMarkersMs: [200, 400, 500, 600],
      viewportEndMs: 800,
      viewportStartMs: 200,
    });
  });

  it("starts practice from the rightmost default marker and normal Play pauses practice", async () => {
    await prepareBackChainingSelection();
    prepareHtmlAudio();
    await enterBackChaining();
    await Promise.resolve();

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-back-chaining-0-practice"]')!.click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackEndMs: 800,
      playbackRegionMode: "selection",
      playbackStartMs: 600,
      repeatEnabled: true,
      backChainingActiveMarkerIndex: 2,
      backChainingActiveStartMs: 600,
      backChainingState: "playing",
      selectionEndMs: 800,
      selectionStartMs: 600,
    });

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-back-chaining-0-next"]')!.click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackStartMs: 400,
      backChainingActiveMarkerIndex: 1,
      selectionEndMs: 800,
      selectionStartMs: 400,
    });

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-back-chaining-0-next"]')!.click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackStartMs: 200,
      backChainingActiveMarkerIndex: 0,
      selectionEndMs: 800,
      selectionStartMs: 200,
    });

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-back-chaining-0-previous"]')!.click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackStartMs: 400,
      backChainingActiveMarkerIndex: 1,
      selectionEndMs: 800,
      selectionStartMs: 400,
    });

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      repeatEnabled: false,
      backChainingState: "paused",
    });

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-back-chaining-0-edit"]')!.click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      backChainingEditing: false,
    });
  });

  it("toggles the attached back-chaining section without rendering an exit action", async () => {
    await prepareBackChainingSelection();
    await enterBackChaining();
    const backChainingButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-selection-toolbar-back-chaining-0"]')!;
    expectPointerGuards(backChainingButton);
    expect(document.querySelector('[data-testid="aqe-back-chaining-0-panel"]')).not.toBeNull();
    expect(backChainingButton.getAttribute("aria-pressed")).toBe("true");
    expect(backChainingButton.getAttribute("aria-expanded")).toBe("true");
    expect(backChainingButton.getAttribute("aria-controls")).toBe("aqe-back-chaining-0-panel");
    expect(backChainingButton.querySelector(".aqe-back-chaining-disclosure-open")).not.toBeNull();
    expect(backChainingButton.querySelector(".aqe-back-chaining-disclosure-closed")).not.toBeNull();

    backChainingButton.click();
    await Promise.resolve();
    expect(document.querySelector('[data-testid="aqe-back-chaining-0-panel"]')).toBeNull();
    expect(backChainingButton.getAttribute("aria-pressed")).toBe("false");
    expect(backChainingButton.getAttribute("aria-expanded")).toBe("false");
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      backChainingBaseStartMs: 200,
      backChainingEditing: true,
      backChainingPanelOpen: false,
    });

    backChainingButton.click();
    await Promise.resolve();
    await Promise.resolve();
    expect(document.querySelector('[data-testid="aqe-back-chaining-0-panel"]')).not.toBeNull();
    expect(document.querySelector('[data-testid="aqe-back-chaining-0-exit"]')).toBeNull();

    backChainingButton.click();
    await Promise.resolve();

    expect(document.querySelector('[data-testid="aqe-back-chaining-0-panel"]')).toBeNull();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      backChainingBaseStartMs: 200,
      backChainingEditing: true,
      backChainingPanelOpen: false,
    });
  });

  it("renders the back-chaining section inside the selection toolbar near graph edges", async () => {
    const { svg } = await prepareBackChainingSelection(0, 0.1);
    expectSelectionToolbarWrap("nowrap");
    await enterBackChaining({ baseEndMs: 100, baseStartMs: 0 });

    expectBackChainingPanelAttachedToToolbar();
    expectSelectionToolbarWrap("wrap");

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-selection-toolbar-back-chaining-0"]')!.click();
    await Promise.resolve();
    dragGraphSelection(svg, 0.9, 1);
    expectSelectionToolbarWrap("nowrap");
    await enterBackChaining({ baseEndMs: 1000, baseStartMs: 900 });

    expectBackChainingPanelAttachedToToolbar();
    expectSelectionToolbarWrap("wrap");
  });

  it("opens the back-chaining section for whole-clip selections", async () => {
    const { row } = await prepareBackChainingSelection(0, 1);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: true,
      selectionEndMs: 1000,
      selectionStartMs: 0,
      selectionToolbarDeleteRegionHidden: true,
      selectionToolbarDeleteRestHidden: true,
      selectionToolbarHidden: false,
    });

    await enterBackChaining({ baseEndMs: 1000, baseStartMs: 0 });

    expect(document.querySelector('[data-testid="aqe-back-chaining-0-panel"]')).not.toBeNull();
    expectBackChainingPanelAttachedToToolbar();
    expect(row.querySelectorAll(".aqe-back-chaining-boundary-marker")).toHaveLength(1);
  });
});

function installVisualizerStyles(): void {
  if (document.querySelector("style[data-aqe-test-visualizer-styles]")) return;
  const style = document.createElement("style");
  style.dataset.aqeTestVisualizerStyles = "true";
  style.textContent = `${visualizerCss}\n${selectionCss}`;
  document.head.appendChild(style);
}

async function enterBackChaining(
  expected: { baseEndMs: number; baseStartMs: number } = { baseEndMs: 800, baseStartMs: 200 },
): Promise<void> {
  document.querySelector<HTMLButtonElement>('[data-testid="aqe-selection-toolbar-back-chaining-0"]')!.click();
  await Promise.resolve();
  expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
    backChainingBaseEndMs: expected.baseEndMs,
    backChainingBaseStartMs: expected.baseStartMs,
    backChainingEditing: true,
    backChainingMarkersMs: [
      expected.baseStartMs,
      expected.baseStartMs + Math.round((expected.baseEndMs - expected.baseStartMs) / 3),
      expected.baseStartMs + Math.round(((expected.baseEndMs - expected.baseStartMs) * 2) / 3),
    ],
    backChainingPanelOpen: true,
  });
}

async function prepareBackChainingSelection(
  startRatio = 0.2,
  endRatio = 0.8,
): Promise<{ row: SVGGElement; svg: SVGSVGElement }> {
  initializeEditorRuntime({ audioFieldIndices: [0], repeatPlaybackByDefault: false });
  scan({ audioFieldIndices: [0], repeatPlaybackByDefault: false });
  await Promise.resolve();
  window.__aqeSetVisualizer?.(0, track, 0);
  const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
  setGraphBounds(svg);
  dragGraphSelection(svg, startRatio, endRatio);
  const row = document.querySelector<SVGGElement>('[data-testid="aqe-back-chaining-marker-row-0"]')!;
  return { row, svg };
}

function expectIconOnlyButton(panel: HTMLElement, kind: "clear" | "next" | "previous", label: string): void {
  const button = panel.querySelector<HTMLButtonElement>(`[data-testid="aqe-back-chaining-0-${kind}"]`)!;
  expect(button).not.toBeNull();
  expect(button.getAttribute("aria-label")).toBe(label);
  expect(button.textContent?.trim()).toBe("");
  expect(button.querySelector(".aqe-button-icon")).not.toBeNull();
}

function expectBackChainingPanelAttachedToToolbar(): void {
  const toolbar = document.querySelector<HTMLElement>('[data-testid="aqe-selection-toolbar-0"]')!;
  const panel = document.querySelector<HTMLElement>('[data-testid="aqe-back-chaining-0-panel"]')!;
  expect(panel.closest('[data-testid="aqe-selection-toolbar-0"]')).toBe(toolbar);
}

function expectSelectionToolbarWrap(expected: "nowrap" | "wrap"): void {
  const toolbar = document.querySelector<HTMLElement>('[data-testid="aqe-selection-toolbar-0"]')!;
  expect(getComputedStyle(toolbar).flexWrap).toBe(expected);
}

function expectPointerGuards(element: HTMLElement): void {
  const PointerEventCtor = window.PointerEvent || window.MouseEvent;
  element.dispatchEvent(new PointerEventCtor("pointerdown", { bubbles: true, cancelable: true }));
  const mouseDown = new MouseEvent("mousedown", { bubbles: true, cancelable: true });
  element.dispatchEvent(mouseDown);
  expect(mouseDown.defaultPrevented).toBe(true);
}

function clickMarkerRow(row: SVGGElement, svg: SVGSVGElement, ratio: number): void {
  const EventCtor = window.PointerEvent || window.MouseEvent;
  const clientX = graphClientX(svg, ratio);
  row.dispatchEvent(new EventCtor("pointerdown", {
    bubbles: true,
    clientX,
    clientY: 155,
  }));
  window.dispatchEvent(new EventCtor("pointerup", {
    bubbles: true,
    clientX,
    clientY: 155,
  }));
}
