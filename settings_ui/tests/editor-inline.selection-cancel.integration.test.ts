import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import {
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

describe("editor inline selection cancel integration", () => {
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
    let now = 1000;
    vi.spyOn(performance, "now").mockImplementation(() => now);
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
    await Promise.resolve();
    now = 1100;
    frames.shift()?.(now);

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
});
