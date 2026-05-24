import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { setControlsBusy } from "../src/editor-inline/actions.js";
import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import { resetSelectionToolbarPreferences } from "../src/editor-inline/selection-toolbar-state.js";
import {
  dispatchGraphPointer,
  dragGraphSelection,
  graphClientX,
  hoverToolbarButton,
  leaveToolbarButton,
  muteConsole,
  renderFields,
  renderTwoAudioFields,
  selectionToolbarButton,
  selectionToolbarDot,
  setGraphBounds,
  track,
} from "./editor-inline.integration.helpers.js";

describe("editor inline selection toolbar integration", () => {
  let restoreConsole: () => void;

  beforeEach(() => {
    restoreConsole = muteConsole();
    renderFields();
  });

  afterEach(() => {
    disposeEditorRuntime();
    resetSelectionToolbarPreferences();
    restoreConsole();
    vi.restoreAllMocks();
  });

  it("keeps the toolbar hidden until a graph has a valid committed selection", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      hasTrack: false,
      selectionToolbarHidden: true,
      selectionToolbarDotHidden: true,
    });

    window.__aqeSetVisualizer?.(0, track, 250);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      hasTrack: true,
      selectionActive: true,
      selectionToolbarHidden: true,
    });

    dragGraphSelection(svg, 0.2, 0.6);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: true,
      selectionDraftActive: false,
      selectionToolbarHidden: false,
      selectionToolbarCollapsed: false,
      selectionToolbarDotHidden: true,
      selectionToolbarPreview: "none",
    });
  });

  it("hides the toolbar during draft selection and positions it at the committed selection end", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 250);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);

    dispatchGraphPointer(svg, "pointerdown", graphClientX(svg, 0.2), true);
    dispatchGraphPointer(svg, "pointermove", graphClientX(svg, 0.6), true);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionDraftActive: true,
      selectionToolbarHidden: true,
    });

    dispatchGraphPointer(svg, "pointerup", graphClientX(svg, 0.6), true);
    const state = window.__aqeGraphStateForTest?.(0);
    expect(state).toMatchObject({
      selectionDraftActive: false,
      selectionToolbarHidden: false,
    });
    expect(state?.selectionToolbarLeftPx).toBeGreaterThan(350);
    expect(state?.selectionToolbarTopPx).toBeGreaterThan(100);

    dragGraphSelection(svg, 0.82, 0.99);
    const clamped = window.__aqeGraphStateForTest?.(0);
    expect(clamped?.selectionToolbarHidden).toBe(false);
    expect(clamped?.selectionToolbarLeftPx).toBeLessThanOrEqual(620);
  });

  it("positions the toolbar against the rendered plot when the SVG viewport is wider than the viewBox", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 250);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg, { height: 150, width: 1240 });

    dragGraphSelection(svg, 0.2, 0.6);

    const state = window.__aqeGraphStateForTest?.(0);
    expect(state).toMatchObject({
      selectionDraftActive: false,
      selectionEndMs: 600,
      selectionToolbarHidden: false,
    });
    expect(state?.selectionToolbarLeftPx).toBeCloseTo(383.6, 1);
    expect(state?.selectionToolbarTopPx).toBeCloseTo(116, 1);
  });

  it("renders icon-only toolbar buttons with accessible labels", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 250);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.2, 0.6);

    const play = selectionToolbarButton("play");
    const deleteRegion = selectionToolbarButton("delete-region");
    const deleteRest = selectionToolbarButton("delete-rest");
    const collapse = selectionToolbarButton("collapse");

    expect(play.getAttribute("data-aqe-tooltip-content")).toBe("Play selection");
    expect(play.getAttribute("aria-label")).toBe("Play selection");
    expect(deleteRegion.getAttribute("data-aqe-tooltip-content")).toBe("Delete selected region");
    expect(deleteRest.getAttribute("data-aqe-tooltip-content")).toBe("Delete audio outside selected region");
    expect(deleteRegion.getAttribute("data-aqe-button-state")).toBe("destructive");
    expect(deleteRest.getAttribute("data-aqe-button-state")).toBe("destructive");
    expect(collapse.getAttribute("data-aqe-tooltip-content")).toBe("Collapse selection actions");
    for (const button of [play, deleteRegion, deleteRest, collapse]) {
      expect(button.querySelector(".aqe-button-label")).toBeNull();
      expect(button.classList.contains("aqe-selection-toolbar-button")).toBe(true);
    }
  });

  it("keeps collapse preference across selection changes until the dot is expanded", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 250);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.2, 0.6);

    selectionToolbarButton("collapse").click();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: true,
      selectionToolbarCollapsed: true,
      selectionToolbarHidden: true,
      selectionToolbarDotHidden: false,
    });
    expect(selectionToolbarDot()).toBeInstanceOf(SVGSVGElement);
    expect(selectionToolbarDot().querySelector(".aqe-selection-toolbar-dot-ring")).not.toBeNull();

    dragGraphSelection(svg, 0.3, 0.7);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionStartMs: 300,
      selectionEndMs: 700,
      selectionToolbarCollapsed: true,
      selectionToolbarHidden: true,
      selectionToolbarDotHidden: false,
    });

    selectionToolbarDot().dispatchEvent(new MouseEvent("click", { bubbles: true }));
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionToolbarCollapsed: false,
      selectionToolbarHidden: false,
      selectionToolbarDotHidden: true,
    });

    dragGraphSelection(svg, 0.2, 0.5);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionStartMs: 200,
      selectionEndMs: 500,
      selectionToolbarCollapsed: false,
      selectionToolbarHidden: false,
    });
  });

  it("preserves toolbar preference across graph redraws after transformations", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 250);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.2, 0.6);

    window.__aqeSetVisualizer?.(0, { ...track, sourceFilename: "transformed-visible.mp3" }, 0);
    dragGraphSelection(svg, 0.3, 0.7);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionToolbarCollapsed: false,
      selectionToolbarHidden: false,
      selectionToolbarDotHidden: true,
    });

    selectionToolbarButton("collapse").click();
    window.__aqeSetVisualizer?.(0, { ...track, sourceFilename: "transformed-collapsed.mp3" }, 0);
    dragGraphSelection(svg, 0.25, 0.5);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionToolbarCollapsed: true,
      selectionToolbarHidden: true,
      selectionToolbarDotHidden: false,
    });

    disposeEditorRuntime();
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, { ...track, sourceFilename: "transformed-remount.mp3" }, 0);
    const remountedSvg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(remountedSvg);
    dragGraphSelection(remountedSvg, 0.35, 0.55);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionToolbarCollapsed: true,
      selectionToolbarHidden: true,
      selectionToolbarDotHidden: false,
    });
  });

  it("expands the collapsed svg circle from the keyboard", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 250);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.2, 0.6);

    selectionToolbarButton("collapse").click();
    const dot = selectionToolbarDot();
    expect(dot.getAttribute("role")).toBe("button");
    expect(dot.getAttribute("tabindex")).toBe("0");
    dot.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, key: "Enter" }));

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionToolbarCollapsed: false,
      selectionToolbarHidden: false,
      selectionToolbarDotHidden: true,
    });
  });

  it("sets and clears destructive hover previews", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 250);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.2, 0.6);
    const restPreviewBefore = document.querySelector<HTMLElement>(".aqe-selection-rest-preview-before");
    const restPreviewAfter = document.querySelector<HTMLElement>(".aqe-selection-rest-preview-after");

    const deleteRegion = selectionToolbarButton("delete-region");
    hoverToolbarButton(deleteRegion);
    expect(window.__aqeGraphStateForTest?.(0)?.selectionToolbarPreview).toBe("region");
    leaveToolbarButton(deleteRegion);
    expect(window.__aqeGraphStateForTest?.(0)?.selectionToolbarPreview).toBe("none");

    const deleteRest = selectionToolbarButton("delete-rest");
    deleteRest.focus();
    expect(window.__aqeGraphStateForTest?.(0)?.selectionToolbarPreview).toBe("rest");
    expect(restPreviewBefore).not.toBeNull();
    expect(restPreviewAfter).not.toBeNull();
    expect(window.getComputedStyle(restPreviewBefore!).display).toBe("block");
    expect(window.getComputedStyle(restPreviewAfter!).display).toBe("block");
    deleteRest.blur();
    expect(window.__aqeGraphStateForTest?.(0)?.selectionToolbarPreview).toBe("none");
  });

  it("clears previews on busy changes and scopes previews per graph", () => {
    renderTwoAudioFields();
    initializeEditorRuntime({ audioFieldIndices: [0, 1] });
    scan({ audioFieldIndices: [0, 1] });
    window.__aqeSetVisualizer?.(0, track, 250);
    window.__aqeSetVisualizer?.(1, { ...track, sourceFilename: "clip two.mp3" }, 400);
    const firstSvg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    const secondSvg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-1"]')!;
    setGraphBounds(firstSvg);
    setGraphBounds(secondSvg);
    dragGraphSelection(firstSvg, 0.2, 0.6);
    dragGraphSelection(secondSvg, 0.3, 0.7);

    hoverToolbarButton(selectionToolbarButton("delete-region", 0));
    expect(window.__aqeGraphStateForTest?.(0)?.selectionToolbarPreview).toBe("region");
    expect(window.__aqeGraphStateForTest?.(1)?.selectionToolbarPreview).toBe("none");

    setControlsBusy(0, true, "Processing", "aqe:test");
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionToolbarPreview: "none",
      selectionToolbarDeleteRegionDisabled: true,
      selectionToolbarDeleteRestDisabled: true,
    });
    setControlsBusy(0, false);
  });
});
