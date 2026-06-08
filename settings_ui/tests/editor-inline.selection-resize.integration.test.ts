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
    const startHandle = document.querySelector<HTMLElement>('[data-testid="aqe-selection-resize-start-0"]')!;
    expect(startHandle.hidden).toBe(false);

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

  it("resizes selection handles using visible viewport coordinates when zoomed", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 100);
    window.__aqeSetTimeViewportForTest?.(0, 250, 750);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);

    dragGraphSelection(svg, 0.25, 0.75);
    dragSelectionHandle(svg, "end", 1);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionStartMs: 375,
      selectionEndMs: 750,
      cursorMs: 375,
    });
  });

  it("shows resize handles only for true selection edges visible in the viewport", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.25, 0.75);

    window.__aqeSetTimeViewportForTest?.(0, 0, 500);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionEndHandleVisible: false,
      selectionStartHandleVisible: true,
      selectionStartMs: 250,
      selectionEndMs: 750,
    });
    dragSelectionHandle(svg, "start", 0.25);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      cursorMs: 125,
      selectionStartMs: 125,
      selectionEndMs: 750,
    });

    window.__aqeSetTimeViewportForTest?.(0, 500, 1000);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionEndHandleVisible: true,
      selectionStartHandleVisible: false,
    });
    dragSelectionHandle(svg, "end", 0.75);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      cursorMs: 125,
      selectionStartMs: 125,
      selectionEndMs: 875,
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

  it("updates the cursor flag while dragging the left selection handle", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.2, 0.6);
    const handle = document.querySelector('[data-testid="aqe-selection-resize-start-0"]')!;
    const flag = document.querySelector<HTMLElement>('[data-testid="aqe-css-cursor-0"] .aqe-css-cursor-flag')!;

    dispatchHandlePointer(handle, "pointerdown", graphClientX(svg, 0.2));
    dispatchHandlePointer(handle, "pointermove", graphClientX(svg, 0.1));

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      cursorMs: 100,
      progressMs: 100,
      selectionDraftActive: true,
      selectionDraftStartMs: 100,
      selectionDraftEndMs: 600,
    });
    expect(flag.querySelector(".aqe-css-cursor-flag-current")?.textContent).toBe("100 ms");
    expect(flag.querySelector(".aqe-css-cursor-flag-pitch")?.textContent).toBe(" / 150 Hz");
  });

  it("keeps outside shade below selection edges and handles while resizing", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.2, 0.6);

    const pitch = document.querySelector<SVGGElement>('[data-testid="aqe-pitch-0"]')!;
    const shadeBefore = document.querySelector<SVGRectElement>('[data-testid="aqe-selection-outside-preview-before-0"]')!;
    const shadeAfter = document.querySelector<SVGRectElement>('[data-testid="aqe-selection-outside-preview-after-0"]')!;
    const startEdge = document.querySelector<SVGLineElement>('[data-testid="aqe-selection-start-0"]')!;
    const startHandle = document.querySelector<SVGRectElement>('[data-testid="aqe-selection-resize-start-0"]')!;
    const band = document.querySelector<SVGRectElement>('[data-testid="aqe-selection-0"]')!;

    expect(shadeBefore).toHaveAttribute("visibility", "visible");
    expect(shadeAfter).toHaveAttribute("visibility", "visible");
    expect(Boolean(pitch.compareDocumentPosition(shadeBefore) & Node.DOCUMENT_POSITION_FOLLOWING)).toBe(true);
    expect(Boolean(shadeBefore.compareDocumentPosition(startEdge) & Node.DOCUMENT_POSITION_FOLLOWING)).toBe(true);
    expect(Boolean(shadeBefore.compareDocumentPosition(startHandle) & Node.DOCUMENT_POSITION_FOLLOWING)).toBe(true);

    dispatchHandlePointer(startHandle, "pointerdown", graphClientX(svg, 0.2));
    dispatchHandlePointer(startHandle, "pointermove", graphClientX(svg, 0.1));

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionDraftActive: true,
      selectionDraftStartMs: 100,
      selectionDraftEndMs: 600,
    });
    expect(band).toHaveClass("aqe-selection-draft");
    expect(shadeBefore).toHaveAttribute("visibility", "visible");
    expect(shadeAfter).toHaveAttribute("visibility", "visible");
    expect(Boolean(shadeBefore.compareDocumentPosition(startHandle) & Node.DOCUMENT_POSITION_FOLLOWING)).toBe(true);
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

  it("ignores Shift-drag from a visible handle and preserves the selection", () => {
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
      selectionStartMs: 200,
      selectionEndMs: 600,
      selectionDraftActive: false,
      cursorMs: 200,
      playbackStartMs: 200,
      playbackEndMs: 600,
    });
  });
});
