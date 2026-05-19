import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import {
  dispatchGraphPointer,
  dragGraphSelection,
  graphClientX,
  muteConsole,
  renderFields,
  setGraphBounds,
  track,
} from "./editor-inline.integration.helpers.js";

describe("editor inline selection creation integration", () => {
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

  it("creates, replaces, and clears graph selections with Shift gestures", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);

    dragGraphSelection(svg, 0.2, 0.6);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: true,
      selectionStartMs: 200,
      selectionEndMs: 600,
      cursorMs: 200,
    });
    expect(document.querySelector('[data-testid="aqe-selection-0"]')).toHaveAttribute("visibility", "visible");
    const startHandle = document.querySelector('[data-testid="aqe-selection-resize-start-0"]')!;
    const endHandle = document.querySelector('[data-testid="aqe-selection-resize-end-0"]')!;
    expect(startHandle).toHaveAttribute("visibility", "visible");
    expect(endHandle).toHaveAttribute("visibility", "visible");
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionStartHandleVisible: true,
      selectionEndHandleVisible: true,
    });

    dragGraphSelection(svg, 0.8, 0.3);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionStartMs: 300,
      selectionEndMs: 800,
    });

    dispatchGraphPointer(svg, "pointerdown", graphClientX(svg, 0.5), true);
    dispatchGraphPointer(svg, "pointerup", graphClientX(svg, 0.5), true);
    expect(window.__aqeGraphStateForTest?.(0)?.selectionActive).toBe(false);
    expect(document.querySelector('[data-testid="aqe-selection-0"]')).toHaveAttribute("visibility", "hidden");
    expect(startHandle).toHaveAttribute("visibility", "hidden");
    expect(endHandle).toHaveAttribute("visibility", "hidden");
  });

  it("shows and updates a draft selection during Shift-drag before commit", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    const band = document.querySelector('[data-testid="aqe-selection-0"]')!;
    setGraphBounds(svg);

    dispatchGraphPointer(svg, "pointerdown", graphClientX(svg, 0.2), true);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: false,
      selectionDraftActive: false,
      selectionDraftStartMs: null,
      selectionDraftEndMs: null,
      cursorMs: 100,
    });
    expect(band).toHaveAttribute("visibility", "hidden");

    dispatchGraphPointer(svg, "pointermove", graphClientX(svg, 0.6), true);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: false,
      selectionDraftActive: true,
      selectionDraftStartMs: 200,
      selectionDraftEndMs: 600,
      cursorMs: 100,
    });
    expect(band).toHaveAttribute("visibility", "visible");
    expect(band).toHaveClass("aqe-selection-draft");

    dispatchGraphPointer(svg, "pointermove", graphClientX(svg, 0.8), true);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: false,
      selectionDraftActive: true,
      selectionDraftStartMs: 200,
      selectionDraftEndMs: 800,
    });

    dispatchGraphPointer(svg, "pointerup", graphClientX(svg, 0.8), true);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: true,
      selectionStartMs: 200,
      selectionEndMs: 800,
      selectionDraftActive: false,
      selectionDraftStartMs: null,
      selectionDraftEndMs: null,
      cursorMs: 200,
    });
    expect(band).not.toHaveClass("aqe-selection-draft");
  });

  it("keeps selection stable through normal click and drag gestures", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);

    dragGraphSelection(svg, 0.2, 0.6);
    dispatchGraphPointer(svg, "pointerdown", graphClientX(svg, 0.8));
    dispatchGraphPointer(svg, "pointerup", graphClientX(svg, 0.8));

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: true,
      selectionStartMs: 200,
      selectionEndMs: 600,
      cursorMs: 800,
    });

    dispatchGraphPointer(svg, "pointerdown", graphClientX(svg, 0.1));
    dispatchGraphPointer(svg, "pointermove", graphClientX(svg, 0.9));
    dispatchGraphPointer(svg, "pointerup", graphClientX(svg, 0.9));

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionStartMs: 200,
      selectionEndMs: 600,
      cursorMs: 900,
    });
  });
});
