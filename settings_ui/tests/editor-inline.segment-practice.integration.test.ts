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

describe("editor inline segment practice integration", () => {
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
    expectIconOnlyButton(panel, "previous", "Previous");
    expectIconOnlyButton(panel, "next", "Next");
    expectIconOnlyButton(panel, "clear", "Clear markers");
    expect(panel.querySelector('[data-testid="aqe-segment-0-exit"]')).toBeNull();
    expect(row.querySelectorAll(".aqe-segment-boundary-marker")).toHaveLength(2);
    await Promise.resolve();
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

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      repeatEnabled: false,
      segmentPracticeState: "paused",
    });
  });

  it("toggles the floating segment panel without rendering an exit action", async () => {
    await prepareSegmentSelection();
    await enterSegmentPractice();
    expect(document.querySelector('[data-testid="aqe-segment-0-panel"]')).not.toBeNull();

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-selection-toolbar-practice-segments-0"]')!.click();
    await Promise.resolve();
    expect(document.querySelector('[data-testid="aqe-segment-0-panel"]')).toBeNull();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      segmentBaseStartMs: 200,
      segmentEditing: true,
      segmentPanelOpen: false,
    });

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-selection-toolbar-practice-segments-0"]')!.click();
    await Promise.resolve();
    await Promise.resolve();
    expect(document.querySelector('[data-testid="aqe-segment-0-panel"]')).not.toBeNull();
    expect(document.querySelector('[data-testid="aqe-segment-0-exit"]')).toBeNull();

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-selection-toolbar-practice-segments-0"]')!.click();
    await Promise.resolve();

    expect(document.querySelector('[data-testid="aqe-segment-0-panel"]')).toBeNull();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      segmentBaseStartMs: 200,
      segmentEditing: true,
      segmentPanelOpen: false,
    });
  });

  it("keeps the floating segment panel inside the graph horizontal bounds", async () => {
    const { svg } = await prepareSegmentSelection(0, 0.1);
    await enterSegmentPractice({ baseEndMs: 100, baseStartMs: 0 });

    expectSegmentPanelWithinGraphBounds({ expectLeftFlush: true });

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-selection-toolbar-practice-segments-0"]')!.click();
    await Promise.resolve();
    dragGraphSelection(svg, 0.9, 1);
    await enterSegmentPractice({ baseEndMs: 1000, baseStartMs: 900 });

    expectSegmentPanelWithinGraphBounds({ expectRightFlush: true });
  });

  it("opens the floating segment panel for whole-clip selections", async () => {
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
    expect(row.querySelectorAll(".aqe-segment-boundary-marker")).toHaveLength(2);
  });
});

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
): Promise<{ row: HTMLElement; svg: SVGSVGElement }> {
  initializeEditorRuntime({ audioFieldIndices: [0], repeatPlaybackByDefault: false });
  scan({ audioFieldIndices: [0], repeatPlaybackByDefault: false });
  await Promise.resolve();
  window.__aqeSetVisualizer?.(0, track, 0);
  const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
  setGraphBounds(svg);
  dragGraphSelection(svg, startRatio, endRatio);
  const row = document.querySelector<HTMLElement>('[data-testid="aqe-segment-marker-row-0"]')!;
  return { row, svg };
}

function expectIconOnlyButton(panel: HTMLElement, kind: "clear" | "next" | "previous", label: string): void {
  const button = panel.querySelector<HTMLButtonElement>(`[data-testid="aqe-segment-0-${kind}"]`)!;
  expect(button).not.toBeNull();
  expect(button.getAttribute("aria-label")).toBe(label);
  expect(button.textContent?.trim()).toBe("");
  expect(button.querySelector(".aqe-button-icon")).not.toBeNull();
}

function expectSegmentPanelWithinGraphBounds(
  options: { expectLeftFlush?: boolean; expectRightFlush?: boolean } = {},
): void {
  const plot = document.querySelector<HTMLElement>('[data-testid="aqe-visualizer-plot-0"]')!;
  const panelLeft = cssVarNumber(plot, "--aqe-segment-panel-left-px");
  const panelWidth = cssVarNumber(plot, "--aqe-segment-panel-width-px");
  const plotLeft = 44;
  const plotRight = 610;
  expect(panelLeft).toBeGreaterThanOrEqual(plotLeft);
  expect(panelLeft + panelWidth).toBeLessThanOrEqual(plotRight);
  if (options.expectLeftFlush) expect(panelLeft).toBeCloseTo(plotLeft, 1);
  if (options.expectRightFlush) expect(panelLeft + panelWidth).toBeCloseTo(plotRight, 1);
}

function cssVarNumber(node: HTMLElement, name: string): number {
  return Number.parseFloat(node.style.getPropertyValue(name));
}

function clickMarkerRow(row: HTMLElement, svg: SVGSVGElement, ratio: number): void {
  const EventCtor = window.PointerEvent || window.MouseEvent;
  row.dispatchEvent(new EventCtor("pointerdown", {
    bubbles: true,
    clientX: graphClientX(svg, ratio),
    clientY: 155,
  }));
}
