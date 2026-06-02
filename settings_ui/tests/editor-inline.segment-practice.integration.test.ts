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

    const edit = document.querySelector<HTMLButtonElement>('[data-testid="aqe-segment-0-edit"]')!;
    expect(edit).not.toBeNull();
    expect(edit.disabled).toBe(false);

    edit.click();
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
    await openPlayOptions();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-segment-0-edit"]')!.click();
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
    await openPlayOptions();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-segment-0-edit"]')!.click();
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
});

async function prepareSegmentSelection(): Promise<{ row: HTMLElement; svg: SVGSVGElement }> {
  initializeEditorRuntime({ audioFieldIndices: [0], repeatPlaybackByDefault: false });
  scan({ audioFieldIndices: [0], repeatPlaybackByDefault: false });
  await Promise.resolve();
  window.__aqeSetVisualizer?.(0, track, 0);
  const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
  setGraphBounds(svg);
  dragGraphSelection(svg, 0.2, 0.8);
  const row = document.querySelector<HTMLElement>('[data-testid="aqe-segment-marker-row-0"]')!;
  return { row, svg };
}

function clickMarkerRow(row: HTMLElement, svg: SVGSVGElement, ratio: number): void {
  const EventCtor = window.PointerEvent || window.MouseEvent;
  row.dispatchEvent(new EventCtor("pointerdown", {
    bubbles: true,
    clientX: graphClientX(svg, ratio),
    clientY: 155,
  }));
}
