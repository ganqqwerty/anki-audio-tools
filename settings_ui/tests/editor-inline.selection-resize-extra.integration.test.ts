import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import {
  dispatchGraphPointer,
  dispatchHandlePointer,
  dragGraphSelection,
  graphClientX,
  mockAnimationFrames,
  muteConsole,
  prepareHtmlAudio,
  renderFields,
  setGraphBounds,
  track,
} from "./editor-inline.integration.helpers.js";

describe("editor inline selection resize edge cases", () => {
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

  it("keeps resize handles translucent while a draft selection is active", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    const startHandle = document.querySelector('[data-testid="aqe-selection-resize-start-0"]')!;
    const endHandle = document.querySelector('[data-testid="aqe-selection-resize-end-0"]')!;
    setGraphBounds(svg);

    expect(startHandle).toHaveAttribute("visibility", "visible");
    expect(endHandle).toHaveAttribute("visibility", "visible");
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionStartHandleVisible: true,
      selectionEndHandleVisible: true,
    });

    dispatchGraphPointer(svg, "pointerdown", graphClientX(svg, 0.2), true);
    dispatchGraphPointer(svg, "pointermove", graphClientX(svg, 0.6), true);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: true,
      selectionDraftActive: true,
      selectionStartHandleVisible: true,
      selectionEndHandleVisible: true,
    });
    expect(startHandle).toHaveAttribute("visibility", "visible");
    expect(startHandle).toHaveClass("aqe-selection-resize-dragging");
    expect(endHandle).toHaveAttribute("visibility", "visible");
    expect(endHandle).toHaveClass("aqe-selection-resize-dragging");

    dispatchGraphPointer(svg, "pointerup", graphClientX(svg, 0.6), true);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: true,
      selectionDraftActive: false,
      selectionStartHandleVisible: true,
      selectionEndHandleVisible: true,
    });
    expect(startHandle).not.toHaveClass("aqe-selection-resize-dragging");
    expect(endHandle).not.toHaveClass("aqe-selection-resize-dragging");
  });

  it("cancels resize drafts from pointer cancel, capture loss, and blur", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    const handle = document.querySelector('[data-testid="aqe-selection-resize-end-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.2, 0.6);

    const startResizeDraft = (): void => {
      dispatchHandlePointer(handle, "pointerdown", graphClientX(svg, 0.6));
      dispatchHandlePointer(handle, "pointermove", graphClientX(svg, 0.9));
      expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
        selectionStartMs: 200,
        selectionEndMs: 600,
        selectionDraftActive: true,
        selectionDraftStartMs: 200,
        selectionDraftEndMs: 900,
      });
    };
    const expectOriginalSelection = (): void => {
      expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
        selectionStartMs: 200,
        selectionEndMs: 600,
        selectionDraftActive: false,
        selectionStartHandleVisible: true,
        selectionEndHandleVisible: true,
      });
    };

    startResizeDraft();
    dispatchHandlePointer(handle, "pointercancel", graphClientX(svg, 0.9));
    expectOriginalSelection();

    startResizeDraft();
    const EventCtor = window.PointerEvent || window.MouseEvent;
    handle.dispatchEvent(new EventCtor("lostpointercapture", { bubbles: true, clientX: graphClientX(svg, 0.9) }));
    expectOriginalSelection();

    startResizeDraft();
    window.dispatchEvent(new Event("blur"));
    expectOriginalSelection();
  });

  it("restarts active playback from selection start when resized end moves before progress", async () => {
    const frames = mockAnimationFrames();
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.25, 0.75);
    const audio = prepareHtmlAudio();

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();
    audio.currentTime = 0.7;
    frames.shift()?.(performance.now() + 700);
    const handle = document.querySelector('[data-testid="aqe-selection-resize-end-0"]')!;

    dispatchHandlePointer(handle, "pointerdown", graphClientX(svg, 0.75));
    dispatchHandlePointer(handle, "pointermove", graphClientX(svg, 0.6));
    dispatchHandlePointer(handle, "pointerup", graphClientX(svg, 0.6));
    await Promise.resolve();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "playing",
      playButtonLabel: "Pause",
      cursorMs: 250,
      selectionStartMs: 250,
      selectionEndMs: 600,
      playbackStartMs: 250,
      playbackEndMs: 600,
      playbackRegionMode: "selection",
    });
    expect(audio.pause).toHaveBeenCalled();
    expect(audio.play).toHaveBeenCalledTimes(2);
  });
});
