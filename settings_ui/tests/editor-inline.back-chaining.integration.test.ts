import { readFileSync } from "node:fs";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import {
  dragGraphSelection,
  graphClientX,
  muteConsole,
  prepareHtmlAudio,
  renderFields,
  setGraphBounds,
  track,
} from "./editor-inline.integration.helpers.js";

const visualizerCss = readFileSync(
  "src/editor-inline/styles/visualizer.css",
  "utf8",
);
const selectionCss = readFileSync(
  "src/editor-inline/styles/selection.css",
  "utf8",
);

describe("editor inline back-chaining integration", () => {
  let restoreConsole: () => void;

  beforeEach(() => {
    installVisualizerStyles();
    restoreConsole = muteConsole();
    renderFields();
  });

  afterEach(() => {
    disposeEditorRuntime();
    restoreConsole();
    vi.restoreAllMocks();
  });

  it("starts back-chaining from the toolbar for the whole file instead of the graph selection", async () => {
    const { row, svg } = await prepareBackChainingGraph();
    dragGraphSelection(svg, 0.2, 0.8);

    expect(document.querySelector('[data-testid="aqe-selection-toolbar-back-chaining-0"]')).toBeNull();
    expect(document.querySelector('[data-testid="aqe-back-chaining-0-panel"]')).toBeNull();
    expect(document.querySelector('[data-testid="aqe-back-chaining-0-edit"]')).toBeNull();
    expect(document.querySelector('[data-testid="aqe-back-chaining-0-clear"]')).toBeNull();
    expect(document.querySelector('[data-testid="aqe-back-chaining-0-previous"]')).toBeNull();

    prepareHtmlAudio();
    practiceButton().click();
    await Promise.resolve();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      backChainingBaseEndMs: 1000,
      backChainingBaseStartMs: 0,
      backChainingMarkersMs: [0, 333, 667],
      backChainingState: "playing",
      playbackEndMs: 1000,
      playbackRegionMode: "selection",
      playbackStartMs: 667,
      selectionEndMs: 1000,
      selectionStartMs: 667,
    });
    expect(row.querySelectorAll(".aqe-back-chaining-boundary-marker")).toHaveLength(1);
    expect(practiceButton().dataset.aqeButtonState).toBe("pause");
    expect(nextButton().disabled).toBe(false);
  });

  it("places markers using zoomed viewport time while keeping a whole-file base", async () => {
    const { svg } = await prepareBackChainingGraph();
    window.__aqeSetTimeViewportForTest?.(0, 200, 800);

    clickMarkerRail(svg, 0.5);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      backChainingBaseEndMs: 1000,
      backChainingBaseStartMs: 0,
      backChainingMarkerVisibleXs: expect.any(Array),
      backChainingMarkersMs: [0, 333, 500, 667],
      viewportEndMs: 800,
      viewportStartMs: 200,
    });
  });

  it("advances to longer suffixes from the toolbar and normal Play pauses practice", async () => {
    await prepareBackChainingGraph();
    prepareHtmlAudio();

    practiceButton().click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      backChainingActiveMarkerIndex: 2,
      backChainingActiveStartMs: 667,
      backChainingState: "playing",
      repeatEnabled: true,
    });

    nextButton().click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      backChainingActiveMarkerIndex: 1,
      playbackStartMs: 333,
      selectionEndMs: 1000,
      selectionStartMs: 333,
    });

    nextButton().click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      backChainingActiveMarkerIndex: 0,
      playbackStartMs: 0,
      selectionEndMs: 1000,
      selectionStartMs: 0,
    });
    expect(nextButton().disabled).toBe(true);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      backChainingState: "paused",
      repeatEnabled: false,
    });
    expect(practiceButton().dataset.aqeButtonState).toBe("default");
  });

  it("adds markers mid-practice and includes them in longer-suffix navigation", async () => {
    const { svg } = await prepareBackChainingGraph();
    prepareHtmlAudio();

    practiceButton().click();
    await Promise.resolve();
    clickMarkerRail(svg, 0.5);
    await Promise.resolve();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      backChainingActiveMarkerIndex: 3,
      backChainingActiveStartMs: 667,
      backChainingMarkersMs: [0, 333, 500, 667],
      playbackStartMs: 667,
    });

    nextButton().click();
    await Promise.resolve();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      backChainingActiveMarkerIndex: 2,
      backChainingActiveStartMs: 500,
      playbackStartMs: 500,
      selectionStartMs: 500,
    });
  });
});

function installVisualizerStyles(): void {
  if (document.querySelector("style[data-aqe-test-visualizer-styles]")) return;
  const style = document.createElement("style");
  style.dataset.aqeTestVisualizerStyles = "true";
  style.textContent = `${visualizerCss}\n${selectionCss}`;
  document.head.appendChild(style);
}

async function prepareBackChainingGraph(): Promise<{ row: SVGGElement; svg: SVGSVGElement }> {
  initializeEditorRuntime({ audioFieldIndices: [0], repeatPlaybackByDefault: false });
  scan({ audioFieldIndices: [0], repeatPlaybackByDefault: false });
  await Promise.resolve();
  window.__aqeSetVisualizer?.(0, track, 0);
  await Promise.resolve();
  const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
  setGraphBounds(svg);
  const row = document.querySelector<SVGGElement>('[data-testid="aqe-back-chaining-marker-row-0"]')!;
  return { row, svg };
}

function clickMarkerRail(svg: SVGSVGElement, ratio: number): void {
  const row = document.querySelector<SVGGElement>('[data-testid="aqe-back-chaining-marker-row-0"]')!;
  const target = row.getAttribute("aria-hidden") === "true"
    ? document.querySelector<HTMLElement>(".aqe-back-chaining-marker-hitbox")!
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

function practiceButton(): HTMLButtonElement {
  return document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-back-chain-practice"]')!;
}

function nextButton(): HTMLButtonElement {
  return document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-back-chain-next"]')!;
}
