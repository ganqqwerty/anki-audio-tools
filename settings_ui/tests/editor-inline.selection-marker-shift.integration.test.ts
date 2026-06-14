import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import {
  dispatchHandlePointer,
  dragGraphSelection,
  graphClientX,
  muteConsole,
  renderFields,
  setFullGraphViewport,
  setGraphBounds,
  track,
} from "./editor-inline.integration.helpers.js";

describe("editor inline selection marker shift integration", () => {
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

  it("moves selection edges to neighboring markers and updates the playback region", async () => {
    const svg = await prepareShiftGraph();
    clickMarkerRail(svg, 0.75);
    await Promise.resolve();
    dragGraphSelection(svg, 1 / 3, 2 / 3);
    await Promise.resolve();

    shiftButton("end", "previous").click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      cursorMs: 333,
      playbackEndMs: 500,
      playbackStartMs: 333,
      selectionEndMs: 500,
      selectionStartMs: 333,
    });

    const startPrevious = shiftButton("start", "previous");
    startPrevious.click();
    await Promise.resolve();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      cursorMs: 0,
      playbackEndMs: 500,
      playbackStartMs: 0,
      selectionEndMs: 500,
      selectionStartMs: 0,
    });
    expect(startPrevious).toBeDisabled();
    expect(startPrevious.closest(".aqe-tooltip-target")).toHaveAttribute(
      "data-aqe-tooltip-content",
      expect.stringContaining("No earlier marker is available."),
    );
  });

  it("recomputes button availability when markers are added and removed after a selection exists", async () => {
    const svg = await prepareShiftGraph();
    dragGraphSelection(svg, 0, 0.5);
    await Promise.resolve();
    const startNext = shiftButton("start", "next");

    expect(startNext).toBeDisabled();
    expect(startNext.closest(".aqe-tooltip-target")?.getAttribute("data-aqe-tooltip-content")).toContain(
      "That marker would cross the other selection edge.",
    );

    clickMarkerRail(svg, 0.25);
    await Promise.resolve();
    expect(startNext).not.toBeDisabled();
    expect(startNext.closest(".aqe-tooltip-target")).toHaveAttribute(
      "data-aqe-tooltip-content",
      "Move selection start to next marker",
    );

    clickMarkerRail(svg, 0.25);
    await Promise.resolve();
    expect(startNext).toBeDisabled();
    expect(startNext.closest(".aqe-tooltip-target")?.getAttribute("data-aqe-tooltip-content")).toContain(
      "That marker would cross the other selection edge.",
    );
  });

  it("hides the marker shift buttons while a resize draft is active", async () => {
    const svg = await prepareShiftGraph();
    dragGraphSelection(svg, 1 / 3, 2 / 3);
    await Promise.resolve();

    const startNext = shiftButton("start", "next");
    const endPrevious = shiftButton("end", "previous");
    expect(startNext.hidden).toBe(false);
    expect(endPrevious.hidden).toBe(false);

    const handle = document.querySelector('[data-testid="aqe-selection-resize-end-0"]')!;
    dispatchHandlePointer(handle, "pointerdown", graphClientX(svg, 2 / 3));
    dispatchHandlePointer(handle, "pointermove", graphClientX(svg, 0.8));
    await Promise.resolve();

    expect(startNext.hidden).toBe(true);
    expect(endPrevious.hidden).toBe(true);

    dispatchHandlePointer(handle, "pointerup", graphClientX(svg, 0.8));
    await Promise.resolve();

    expect(startNext.hidden).toBe(false);
    expect(endPrevious.hidden).toBe(false);
  });
});

async function prepareShiftGraph(): Promise<SVGSVGElement> {
  initializeEditorRuntime({
    audioFieldIndices: [0],
    repeatPlaybackByDefault: false,
    selectionMarkerShiftButtonsEnabled: true,
  });
  scan({
    audioFieldIndices: [0],
    repeatPlaybackByDefault: false,
    selectionMarkerShiftButtonsEnabled: true,
  });
  await Promise.resolve();
  window.__aqeSetVisualizer?.(0, track, 0);
  await Promise.resolve();
  const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
  setGraphBounds(svg);
  setFullGraphViewport();
  return svg;
}

function clickMarkerRail(svg: SVGSVGElement, ratio: number): void {
  const row = document.querySelector<SVGGElement>('[data-testid="aqe-chorusing-marker-row-0"]')!;
  const target = row.getAttribute("aria-hidden") === "true"
    ? document.querySelector<HTMLElement>(".aqe-chorusing-marker-hitbox")!
    : row;
  const EventCtor = window.PointerEvent || window.MouseEvent;
  const clientX = graphClientX(svg, ratio);
  target.dispatchEvent(new EventCtor("pointerdown", {
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

function shiftButton(edge: "end" | "start", direction: "next" | "previous"): HTMLButtonElement {
  return document.querySelector<HTMLButtonElement>(
    `[data-testid="aqe-selection-shift-${edge}-${direction}-0"]`,
  )!;
}
