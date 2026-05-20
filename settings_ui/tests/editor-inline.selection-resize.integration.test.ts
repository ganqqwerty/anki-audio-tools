import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { PLOT } from "../src/editor-inline/plot.js";
import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import {
  dispatchHandlePointer,
  dragGraphSelection,
  dragSelectionHandle,
  graphClientX,
  muteConsole,
  renderFields,
  setGraphBounds,
  track,
} from "./editor-inline.integration.helpers.js";

describe("editor inline selection resize integration", () => {
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

  it("resizes committed selections by dragging visible handles without Shift", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.2, 0.6);
    const plotHeight = PLOT.height - PLOT.top - PLOT.bottom;
    const expectedHandleHeight = plotHeight * 0.8;
    const expectedHandleY = PLOT.top + (plotHeight - expectedHandleHeight) / 2;
    const startHandle = document.querySelector<SVGRectElement>('[data-testid="aqe-selection-resize-start-0"]')!;
    const startGrip = document.querySelector<SVGGElement>(".aqe-selection-resize-grip-start")!;
    expect(Number(startHandle.getAttribute("height"))).toBeCloseTo(expectedHandleHeight);
    expect(Number(startHandle.getAttribute("y"))).toBeCloseTo(expectedHandleY);
    expect(startGrip.getAttribute("transform")).toBe(
      `translate(${(Number(startHandle.getAttribute("x")) + 5).toFixed(2)} ${(expectedHandleY + expectedHandleHeight / 2).toFixed(2)})`,
    );

    dragSelectionHandle(svg, "start", 0.1);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: true,
      selectionStartMs: 100,
      selectionEndMs: 600,
      selectionDraftActive: false,
      cursorMs: 100,
      playbackStartMs: 100,
      playbackEndMs: 600,
      playButtonLabel: "Play",
    });

    dragSelectionHandle(svg, "end", 0.8);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionStartMs: 100,
      selectionEndMs: 800,
      cursorMs: 100,
      playbackStartMs: 100,
      playbackEndMs: 800,
      playButtonLabel: "Play",
    });
  });

  it("clamps handle drags at the minimum duration without swapping edges", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.2, 0.6);

    dragSelectionHandle(svg, "start", 0.8);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionStartMs: 550,
      selectionEndMs: 600,
    });

    dragSelectionHandle(svg, "end", 0.1);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionStartMs: 550,
      selectionEndMs: 600,
    });
  });

  it("cancels resize drafts without replacing the committed selection", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.2, 0.6);
    const handle = document.querySelector('[data-testid="aqe-selection-resize-end-0"]')!;

    dispatchHandlePointer(handle, "pointerdown", graphClientX(svg, 0.6));
    dispatchHandlePointer(handle, "pointermove", graphClientX(svg, 0.9));
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionStartMs: 200,
      selectionEndMs: 600,
      selectionDraftActive: true,
      selectionDraftStartMs: 200,
      selectionDraftEndMs: 900,
    });

    window.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, key: "Escape" }));
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionStartMs: 200,
      selectionEndMs: 600,
      selectionDraftActive: false,
    });
  });

  it("lets Shift-drag from a visible handle replace the selection", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.2, 0.6);
    const handle = document.querySelector('[data-testid="aqe-selection-resize-end-0"]')!;

    dispatchHandlePointer(handle, "pointerdown", graphClientX(svg, 0.6), true);
    dispatchHandlePointer(handle, "pointermove", graphClientX(svg, 0.9), true);
    dispatchHandlePointer(handle, "pointerup", graphClientX(svg, 0.9), true);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: true,
      selectionStartMs: 600,
      selectionEndMs: 900,
      selectionDraftActive: false,
      cursorMs: 600,
      playbackStartMs: 600,
      playbackEndMs: 900,
    });
  });
});
