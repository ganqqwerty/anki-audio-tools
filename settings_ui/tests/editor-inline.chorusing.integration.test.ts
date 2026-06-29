import { readFileSync } from "node:fs";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import {
  dragGraphSelection,
  graphClientX,
  muteConsole,
  prepareHtmlAudio,
  renderFields,
  setFullGraphViewport,
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

describe("editor inline chorusing integration", () => {
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

  it("shows and edits whole-file markers as soon as the graph is available", async () => {
    const { row, svg } = await prepareChorusingGraph();

    expect(row.getAttribute("aria-hidden")).toBe("false");
    expect(row.style.display).toBe("");
    expect(row.querySelector(".aqe-chorusing-marker-track")).not.toBeNull();
    expect(row.querySelectorAll(".aqe-chorusing-marker")).toHaveLength(2);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingBaseEndMs: 1000,
      chorusingBaseStartMs: 0,
      chorusingCanPractice: true,
      chorusingCanPrevious: false,
      chorusingMarkersMs: [0, 500],
      chorusingState: "stopped",
    });
    expect(previousButton()).toBeDisabled();
    expect(previousButton().closest(".aqe-button-tooltip-target")).toHaveAttribute(
      "data-aqe-tooltip-content",
      "Move the selection start to the next marker.\n\nChoose a longer selected region before moving forward.",
    );
    expect(nextButton()).not.toBeDisabled();
    expect(nextButton().closest(".aqe-button-tooltip-target")).toHaveAttribute(
      "data-aqe-tooltip-content",
      "Move the selection start to the previous marker.",
    );

    clickMarkerRail(svg, 0.75);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingBaseEndMs: 1000,
      chorusingBaseStartMs: 0,
      chorusingMarkersMs: [0, 500, 750],
    });
  });

  it("keeps markers hidden when the marker panel is hidden and marker shift is disabled", async () => {
    const { row, svg } = await prepareChorusingGraph({
      selectionMarkerShiftButtonsEnabled: false,
      visibleEditorButtons: ["aqe:play", "aqe:analyze", "aqe:settings"],
    });

    expect(document.querySelector('[data-testid="aqe-chorusing-toolbar-panel-0"]')).toBeNull();
    expect(document.querySelector('[data-testid="aqe-selection-shift-start-previous-0"]')).toBeNull();
    expect(row.getAttribute("aria-hidden")).toBe("true");
    expect(row.style.display).toBe("none");
    expect(document.querySelector<HTMLElement>(".aqe-chorusing-marker-hitbox")?.hidden).toBe(true);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingBaseEndMs: 1000,
      chorusingBaseStartMs: 0,
      chorusingMarkersMs: [0, 500],
    });

    clickMarkerRail(svg, 0.5);
    await Promise.resolve();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingMarkersMs: [0, 500],
    });
  });

  it("initializes the rightmost suffix without starting playback", async () => {
    const { row } = await prepareChorusingGraph();
    const audio = prepareHtmlAudio();

    nextButton().click();
    await Promise.resolve();

    expect(audio.play).not.toHaveBeenCalled();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingMarkersMs: [0, 500],
      chorusingRepeatPassesCompleted: 0,
      playbackState: "stopped",
      selectionEndMs: 1000,
      selectionStartMs: 500,
    });
    expect(row.querySelectorAll(".aqe-chorusing-boundary-marker")).toHaveLength(1);
    expect(previousButton().disabled).toBe(true);
    expect(nextButton().disabled).toBe(false);
  });

  it("places markers using zoomed viewport time while keeping a whole-file base", async () => {
    const { svg } = await prepareChorusingGraph();
    window.__aqeSetTimeViewportForTest?.(0, 200, 800);

    clickMarkerRail(svg, 0.4);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingBaseEndMs: 1000,
      chorusingBaseStartMs: 0,
      chorusingMarkerVisibleXs: expect.any(Array),
      chorusingMarkersMs: [0, 440, 500],
      viewportEndMs: 800,
      viewportStartMs: 200,
    });
  });

  it("moves between longer and shorter suffixes from the toolbar", async () => {
    await prepareChorusingGraph();

    nextButton().click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionEndMs: 1000,
      selectionStartMs: 500,
    });

    nextButton().click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionEndMs: 1000,
      selectionStartMs: 0,
    });
    expect(nextButton().disabled).toBe(true);
    expect(previousButton().disabled).toBe(false);

    previousButton().click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionEndMs: 1000,
      selectionStartMs: 500,
    });
  });

  it("uses the active selection when moving between markers", async () => {
    const { svg } = await prepareChorusingGraph();
    dragGraphSelection(svg, 0.2, 0.8);
    await Promise.resolve();

    nextButton().click();
    await Promise.resolve();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionEndMs: 800,
      selectionStartMs: 0,
    });
  });

  it("adds markers and includes them in longer-suffix navigation", async () => {
    const { svg } = await prepareChorusingGraph();

    nextButton().click();
    await Promise.resolve();
    clickMarkerRail(svg, 0.25);
    await Promise.resolve();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingMarkersMs: [0, 250, 500],
      selectionStartMs: 500,
    });

    nextButton().click();
    await Promise.resolve();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionEndMs: 1000,
      selectionStartMs: 250,
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

type EditorRuntimeOverrides = Partial<Parameters<typeof initializeEditorRuntime>[0]>;

async function prepareChorusingGraph(
  overrides: EditorRuntimeOverrides = {},
): Promise<{ row: SVGGElement; svg: SVGSVGElement }> {
  const config = { audioFieldIndices: [0], repeatPlaybackByDefault: false, ...overrides };
  initializeEditorRuntime(config);
  scan(config);
  await Promise.resolve();
  window.__aqeSetVisualizer?.(0, track, 0);
  await Promise.resolve();
  const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
  setGraphBounds(svg);
  setFullGraphViewport();
  const row = document.querySelector<SVGGElement>('[data-testid="aqe-chorusing-marker-row-0"]')!;
  return { row, svg };
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

function nextButton(): HTMLButtonElement {
  return document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-chorusing-next"]')!;
}

function previousButton(): HTMLButtonElement {
  return document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-chorusing-previous"]')!;
}
