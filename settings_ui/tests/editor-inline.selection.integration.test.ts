import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import {
  bridgeCommands,
  dispatchGraphPointer,
  dragGraphSelection,
  graphClientX,
  mockAnimationFrames,
  muteConsole,
  prepareHtmlAudio,
  renderFields,
  setGraphBounds,
  track,
} from "./editor-inline.integration.helpers.js";

describe("editor inline selection integration", () => {

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

    dragGraphSelection(svg, 0.8, 0.3);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionStartMs: 300,
      selectionEndMs: 800,
    });

    dispatchGraphPointer(svg, "pointerdown", graphClientX(svg, 0.5), true);
    dispatchGraphPointer(svg, "pointerup", graphClientX(svg, 0.5), true);
    expect(window.__aqeGraphStateForTest?.(0)?.selectionActive).toBe(false);
    expect(document.querySelector('[data-testid="aqe-selection-0"]')).toHaveAttribute("visibility", "hidden");
  });

  it("shows Delete Region for valid selections and queues a scoped button request", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 250);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    const button = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-delete-selection"]')!;
    setGraphBounds(svg);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      regionDeleteButtonHidden: true,
    });

    dragGraphSelection(svg, 0.2, 0.6);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      regionDeleteButtonHidden: false,
      regionDeleteButtonDisabled: false,
    });

    button.click();

    expect(window.__aqePopPendingRegionDeleteRequest?.()).toEqual({
      ord: 0,
      sourceFilename: "clip one.mp3",
      selectionStartMs: 200,
      selectionEndMs: 600,
      cursorMs: 200,
      durationMs: 1000,
      trigger: "button",
      playbackActive: false,
    });
    expect(bridgeCommands()).toEqual(expect.arrayContaining(["focus:0", "aqe:delete-selection"]));
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      busy: false,
      playbackState: "stopped",
      selectionActive: true,
      allButtonsDisabled: true,
    });
  });

  it("handles Backspace only when the focused graph has a valid selection", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 250);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    const graph = document.querySelector<HTMLElement>('[data-testid="aqe-graph-0"]')!;
    const field = document.getElementById("f0")!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.2, 0.6);

    field.focus();
    field.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, key: "Backspace" }));
    expect(window.__aqePopPendingRegionDeleteRequest?.()).toBeNull();

    graph.focus();
    graph.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, cancelable: true, key: "Backspace" }));

    expect(window.__aqePopPendingRegionDeleteRequest?.()).toMatchObject({
      ord: 0,
      sourceFilename: "clip one.mp3",
      selectionStartMs: 200,
      selectionEndMs: 600,
      trigger: "backspace",
    });
    expect(bridgeCommands()).toEqual(expect.arrayContaining(["focus:0", "aqe:delete-selection"]));
  });

  it("disables Delete Region for whole-clip selections without dispatching", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 0);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    const graph = document.querySelector<HTMLElement>('[data-testid="aqe-graph-0"]')!;
    setGraphBounds(svg);

    dragGraphSelection(svg, 0, 1);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: true,
      regionDeleteButtonHidden: false,
      regionDeleteButtonDisabled: true,
    });

    graph.focus();
    graph.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, cancelable: true, key: "Backspace" }));

    expect(window.__aqePopPendingRegionDeleteRequest?.()).toBeNull();
    expect(bridgeCommands()).not.toContain("aqe:delete-selection");
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

  it("discards draft selection on pointer cancel without replacing the committed selection", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    const band = document.querySelector('[data-testid="aqe-selection-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.2, 0.6);

    dispatchGraphPointer(svg, "pointerdown", graphClientX(svg, 0.7), true);
    dispatchGraphPointer(svg, "pointermove", graphClientX(svg, 0.9), true);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: true,
      selectionStartMs: 200,
      selectionEndMs: 600,
      selectionDraftActive: true,
      selectionDraftStartMs: 700,
      selectionDraftEndMs: 900,
    });
    expect(band).toHaveClass("aqe-selection-draft");

    dispatchGraphPointer(svg, "pointercancel", graphClientX(svg, 0.9), true);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: true,
      selectionStartMs: 200,
      selectionEndMs: 600,
      selectionDraftActive: false,
      selectionDraftStartMs: null,
      selectionDraftEndMs: null,
    });
    expect(band).toHaveAttribute("visibility", "visible");
    expect(band).not.toHaveClass("aqe-selection-draft");
  });

  it("discards draft selection on pointer capture loss", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    const band = document.querySelector('[data-testid="aqe-selection-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.2, 0.6);

    dispatchGraphPointer(svg, "pointerdown", graphClientX(svg, 0.7), true);
    dispatchGraphPointer(svg, "pointermove", graphClientX(svg, 0.9), true);
    expect(band).toHaveClass("aqe-selection-draft");

    const EventCtor = window.PointerEvent || window.MouseEvent;
    svg.dispatchEvent(new EventCtor("lostpointercapture", { bubbles: true, clientX: graphClientX(svg, 0.9), shiftKey: true }));

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: true,
      selectionStartMs: 200,
      selectionEndMs: 600,
      selectionDraftActive: false,
      selectionDraftStartMs: null,
      selectionDraftEndMs: null,
    });
    expect(band).toHaveAttribute("visibility", "visible");
    expect(band).not.toHaveClass("aqe-selection-draft");
  });

  it("discards draft selection with Escape while preserving interrupted playback", async () => {
    const frames = mockAnimationFrames();
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.2, 0.6);
    const audio = prepareHtmlAudio();

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();
    audio.currentTime = 0.3;
    frames.shift()?.(performance.now() + 300);

    dispatchGraphPointer(svg, "pointerdown", graphClientX(svg, 0.7), true);
    dispatchGraphPointer(svg, "pointermove", graphClientX(svg, 0.9), true);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "stopped",
      selectionDraftActive: true,
      cursorMs: 300,
    });

    window.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, key: "Escape" }));

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "playing",
      selectionStartMs: 200,
      selectionEndMs: 600,
      selectionDraftActive: false,
      cursorMs: 300,
    });
    expect(audio.play).toHaveBeenCalledTimes(2);
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
