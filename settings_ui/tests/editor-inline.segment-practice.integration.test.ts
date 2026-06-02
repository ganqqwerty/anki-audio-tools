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

describe("editor inline segment practice integration", () => {
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
    const { row, svg } = await prepareSegmentSelection();
    await openPlayOptions();
    const playPopover = document.querySelector<HTMLElement>('[data-testid="aqe-split-0-play-popover"]')!;
    expect(playPopover.querySelector('[data-testid="aqe-segment-0-edit"]')).toBeNull();

    await enterSegmentPractice();
    const panel = document.querySelector<HTMLElement>('[data-testid="aqe-segment-0-panel"]')!;
    const edit = panel.querySelector<HTMLButtonElement>('[data-testid="aqe-segment-0-edit"]')!;
    expect(edit).not.toBeNull();
    expect(edit.disabled).toBe(false);
    expect(panel.closest('[data-testid="aqe-selection-toolbar-0"]')).not.toBeNull();
    const videoLink = panel.querySelector<HTMLAnchorElement>(".aqe-segment-video-link")!;
    expect(videoLink.textContent).toBe("See video");
    const linkClick = new MouseEvent("click", { bubbles: true, cancelable: true });
    videoLink.dispatchEvent(linkClick);
    expect(linkClick.defaultPrevented).toBe(true);
    expectIconOnlyButton(panel, "previous", "Previous");
    expectIconOnlyButton(panel, "next", "Next");
    expectIconOnlyButton(panel, "clear", "Clear markers");
    expect(panel.querySelector('[data-testid="aqe-segment-0-exit"]')).toBeNull();
    for (const button of panel.querySelectorAll<HTMLButtonElement>(".aqe-segment-practice-button")) {
      expectPointerGuards(button);
    }
    expect(row.querySelectorAll(".aqe-segment-boundary-marker")).toHaveLength(2);
    expect(row.closest('[data-testid="aqe-graph-svg-0"]')).not.toBeNull();
    const trackRect = row.querySelector<SVGRectElement>(".aqe-segment-marker-track")!;
    expect(getComputedStyle(trackRect).fill.replaceAll(",", "")).toBe("rgb(255 255 255)");
    expect(trackRect.getAttribute("y")).toBe("10.00");
    expect(trackRect.hasAttribute("rx")).toBe(false);
    expect(row.querySelector(".aqe-segment-base-range")).toBeNull();
    expect(row.querySelector(".aqe-segment-active-range")).toBeNull();
    expect(getComputedStyle(row).opacity).toBe("1");
    clickMarkerRow(row, svg, 0.4);
    clickMarkerRow(row, svg, 0.7);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      segmentBaseEndMs: 800,
      segmentBaseStartMs: 200,
      segmentEditing: true,
      segmentMarkersMs: [400, 700],
    });

    clickMarkerRow(row, svg, 0.705);
    expect(window.__aqeGraphStateForTest?.(0)?.segmentMarkersMs).toEqual([400]);

    panel.querySelector<HTMLButtonElement>('[data-testid="aqe-segment-0-clear"]')!.click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      segmentBaseEndMs: 800,
      segmentBaseStartMs: 200,
      segmentEditing: true,
      segmentMarkersMs: [],
      segmentPanelOpen: true,
    });
  });

  it("places markers using zoomed viewport time rather than full duration", async () => {
    const { row, svg } = await prepareSegmentSelection();
    await enterSegmentPractice();
    window.__aqeSetTimeViewportForTest?.(0, 200, 800);

    clickMarkerRow(row, svg, 0.5);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      segmentMarkersMs: [500],
      viewportEndMs: 800,
      viewportStartMs: 200,
    });
  });

  it("starts practice from the rightmost marker and normal Play pauses practice", async () => {
    const { row, svg } = await prepareSegmentSelection();
    prepareHtmlAudio();
    await enterSegmentPractice();
    clickMarkerRow(row, svg, 0.4);
    clickMarkerRow(row, svg, 0.7);
    await Promise.resolve();

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-segment-0-practice"]')!.click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackEndMs: 800,
      playbackRegionMode: "selection",
      playbackStartMs: 700,
      repeatEnabled: true,
      segmentActiveMarkerIndex: 1,
      segmentActiveStartMs: 700,
      segmentPracticeState: "playing",
      selectionEndMs: 800,
      selectionStartMs: 700,
    });

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-segment-0-next"]')!.click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackStartMs: 400,
      segmentActiveMarkerIndex: 0,
      selectionEndMs: 800,
      selectionStartMs: 400,
    });

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-segment-0-previous"]')!.click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackStartMs: 700,
      segmentActiveMarkerIndex: 1,
      selectionEndMs: 800,
      selectionStartMs: 700,
    });

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      repeatEnabled: false,
      segmentPracticeState: "paused",
    });

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-segment-0-edit"]')!.click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      segmentEditing: false,
    });
  });

  it("toggles the attached segment section without rendering an exit action", async () => {
    await prepareSegmentSelection();
    await enterSegmentPractice();
    const segmentButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-selection-toolbar-practice-segments-0"]')!;
    expectPointerGuards(segmentButton);
    expect(document.querySelector('[data-testid="aqe-segment-0-panel"]')).not.toBeNull();
    expect(segmentButton.getAttribute("aria-pressed")).toBe("true");
    expect(segmentButton.getAttribute("aria-expanded")).toBe("true");
    expect(segmentButton.getAttribute("aria-controls")).toBe("aqe-segment-0-panel");
    expect(segmentButton.querySelector(".aqe-segment-disclosure-open")).not.toBeNull();
    expect(segmentButton.querySelector(".aqe-segment-disclosure-closed")).not.toBeNull();

    segmentButton.click();
    await Promise.resolve();
    expect(document.querySelector('[data-testid="aqe-segment-0-panel"]')).toBeNull();
    expect(segmentButton.getAttribute("aria-pressed")).toBe("false");
    expect(segmentButton.getAttribute("aria-expanded")).toBe("false");
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      segmentBaseStartMs: 200,
      segmentEditing: true,
      segmentPanelOpen: false,
    });

    segmentButton.click();
    await Promise.resolve();
    await Promise.resolve();
    expect(document.querySelector('[data-testid="aqe-segment-0-panel"]')).not.toBeNull();
    expect(document.querySelector('[data-testid="aqe-segment-0-exit"]')).toBeNull();

    segmentButton.click();
    await Promise.resolve();

    expect(document.querySelector('[data-testid="aqe-segment-0-panel"]')).toBeNull();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      segmentBaseStartMs: 200,
      segmentEditing: true,
      segmentPanelOpen: false,
    });
  });

  it("renders the segment section inside the selection toolbar near graph edges", async () => {
    const { svg } = await prepareSegmentSelection(0, 0.1);
    expectSelectionToolbarWrap("nowrap");
    await enterSegmentPractice({ baseEndMs: 100, baseStartMs: 0 });

    expectSegmentPanelAttachedToToolbar();
    expectSelectionToolbarWrap("wrap");

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-selection-toolbar-practice-segments-0"]')!.click();
    await Promise.resolve();
    dragGraphSelection(svg, 0.9, 1);
    expectSelectionToolbarWrap("nowrap");
    await enterSegmentPractice({ baseEndMs: 1000, baseStartMs: 900 });

    expectSegmentPanelAttachedToToolbar();
    expectSelectionToolbarWrap("wrap");
  });

  it("opens the segment section for whole-clip selections", async () => {
    const { row } = await prepareSegmentSelection(0, 1);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: true,
      selectionEndMs: 1000,
      selectionStartMs: 0,
      selectionToolbarDeleteRegionHidden: true,
      selectionToolbarDeleteRestHidden: true,
      selectionToolbarHidden: false,
    });

    await enterSegmentPractice({ baseEndMs: 1000, baseStartMs: 0 });

    expect(document.querySelector('[data-testid="aqe-segment-0-panel"]')).not.toBeNull();
    expectSegmentPanelAttachedToToolbar();
    expect(row.querySelectorAll(".aqe-segment-boundary-marker")).toHaveLength(2);
  });
});

function installVisualizerStyles(): void {
  if (document.querySelector("style[data-aqe-test-visualizer-styles]")) return;
  const style = document.createElement("style");
  style.dataset.aqeTestVisualizerStyles = "true";
  style.textContent = `${visualizerCss}\n${selectionCss}`;
  document.head.appendChild(style);
}

async function enterSegmentPractice(
  expected: { baseEndMs: number; baseStartMs: number } = { baseEndMs: 800, baseStartMs: 200 },
): Promise<void> {
  document.querySelector<HTMLButtonElement>('[data-testid="aqe-selection-toolbar-practice-segments-0"]')!.click();
  await Promise.resolve();
  expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
    segmentBaseEndMs: expected.baseEndMs,
    segmentBaseStartMs: expected.baseStartMs,
    segmentEditing: true,
    segmentPanelOpen: true,
  });
}

async function prepareSegmentSelection(
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
  const row = document.querySelector<SVGGElement>('[data-testid="aqe-segment-marker-row-0"]')!;
  return { row, svg };
}

function expectIconOnlyButton(panel: HTMLElement, kind: "clear" | "next" | "previous", label: string): void {
  const button = panel.querySelector<HTMLButtonElement>(`[data-testid="aqe-segment-0-${kind}"]`)!;
  expect(button).not.toBeNull();
  expect(button.getAttribute("aria-label")).toBe(label);
  expect(button.textContent?.trim()).toBe("");
  expect(button.querySelector(".aqe-button-icon")).not.toBeNull();
}

function expectSegmentPanelAttachedToToolbar(): void {
  const toolbar = document.querySelector<HTMLElement>('[data-testid="aqe-selection-toolbar-0"]')!;
  const panel = document.querySelector<HTMLElement>('[data-testid="aqe-segment-0-panel"]')!;
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
