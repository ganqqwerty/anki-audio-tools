import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import {
  bridgeCommands,
  dragGraphSelection,
  muteConsole,
  renderFields,
  selectionToolbarButton,
  setGraphBounds,
  track,
} from "./editor-inline.integration.helpers.js";

describe("editor inline selection delete integration", () => {
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

  it("shows Delete Region for valid selections and queues a scoped button request", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 250);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: true,
      selectionStartMs: 0,
      selectionEndMs: 1000,
      selectionToolbarHidden: true,
      regionDeleteButtonHidden: true,
      regionDeleteButtonDisabled: true,
    });

    dragGraphSelection(svg, 0.2, 0.6);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionToolbarHidden: false,
      regionDeleteButtonHidden: false,
      regionDeleteButtonDisabled: false,
    });

    const button = selectionToolbarButton("delete-region");
    button.click();

    expect(window.__aqePopPendingRegionDeleteRequest?.()).toEqual({
      operation: "delete-selection",
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

  it("shows Delete the rest for valid selections and queues a keep-selection request", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 250);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: true,
      selectionStartMs: 0,
      selectionEndMs: 1000,
      selectionToolbarHidden: true,
      regionDeleteRestButtonHidden: true,
      regionDeleteRestButtonDisabled: true,
    });

    dragGraphSelection(svg, 0.2, 0.6);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionToolbarHidden: false,
      regionDeleteRestButtonHidden: false,
      regionDeleteRestButtonDisabled: false,
    });

    const button = selectionToolbarButton("delete-rest");
    button.click();

    expect(window.__aqePopPendingRegionDeleteRequest?.()).toEqual({
      operation: "delete-rest",
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
      operation: "delete-selection",
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
      selectionToolbarHidden: true,
      regionDeleteButtonHidden: true,
      regionDeleteButtonDisabled: true,
      regionDeleteRestButtonHidden: true,
      regionDeleteRestButtonDisabled: true,
    });

    graph.focus();
    graph.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, cancelable: true, key: "Backspace" }));

    expect(window.__aqePopPendingRegionDeleteRequest?.()).toBeNull();
    expect(bridgeCommands()).not.toContain("aqe:delete-selection");
  });
});
