import { readFileSync } from "node:fs";
import { waitFor } from "@testing-library/svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { handlePlaybackBoundary } from "../src/editor-inline/actions.js";
import { handleChorusingLoopBoundary } from "../src/editor-inline/chorusing-controller.js";
import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import {
  setChorusingAutoAdvanceForField,
  setChorusingRepeatCountForField,
} from "../src/editor-inline/split-button-state.js";
import {
  bridgeCommands,
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
      "Move to the next shorter chorusing suffix.\n\nStart chorusing practice and move to a longer suffix before choosing a shorter suffix.",
    );
    expect(nextButton()).not.toBeDisabled();
    expect(nextButton().closest(".aqe-button-tooltip-target")).toHaveAttribute(
      "data-aqe-tooltip-content",
      "Move to the next longer chorusing suffix.",
    );

    clickMarkerRail(svg, 0.75);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingBaseEndMs: 1000,
      chorusingBaseStartMs: 0,
      chorusingMarkersMs: [0, 500, 750],
    });
  });

  it("keeps markers hidden when the chorusing panel is hidden and marker shift is disabled", async () => {
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

  it("starts chorusing from the toolbar for the whole file instead of the graph selection", async () => {
    const { row, svg } = await prepareChorusingGraph();
    dragGraphSelection(svg, 0.2, 0.8);

    expect(document.querySelector('[data-testid="aqe-selection-toolbar-chorusing-0"]')).toBeNull();
    expect(document.querySelector('[data-testid="aqe-chorusing-0-panel"]')).toBeNull();
    expect(document.querySelector('[data-testid="aqe-chorusing-0-edit"]')).toBeNull();
    expect(document.querySelector('[data-testid="aqe-chorusing-0-clear"]')).toBeNull();
    expect(document.querySelector('[data-testid="aqe-chorusing-0-previous"]')).toBeNull();

    prepareHtmlAudio();
    practiceButton().click();
    await Promise.resolve();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingBaseEndMs: 1000,
      chorusingBaseStartMs: 0,
      chorusingMarkersMs: [0, 500],
      chorusingState: "playing",
      playbackEndMs: 1000,
      playbackRegionMode: "selection",
      playbackStartMs: 500,
      selectionEndMs: 1000,
      selectionStartMs: 500,
    });
    expect(row.querySelectorAll(".aqe-chorusing-boundary-marker")).toHaveLength(1);
    expect(practiceButton().dataset.aqeButtonState).toBe("pause");
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

  it("moves between longer and shorter suffixes from the toolbar and normal Play pauses practice", async () => {
    await prepareChorusingGraph();
    prepareHtmlAudio();

    practiceButton().click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingActiveMarkerIndex: 1,
      chorusingActiveStartMs: 500,
      chorusingState: "playing",
      repeatEnabled: true,
    });

    nextButton().click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingActiveMarkerIndex: 0,
      playbackStartMs: 0,
      selectionEndMs: 1000,
      selectionStartMs: 0,
    });
    expect(nextButton().disabled).toBe(true);
    expect(previousButton().disabled).toBe(false);

    previousButton().click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingActiveMarkerIndex: 1,
      playbackStartMs: 500,
      selectionEndMs: 1000,
      selectionStartMs: 500,
    });
    expect(nextButton().disabled).toBe(false);
    expect(previousButton().disabled).toBe(true);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingState: "paused",
      repeatEnabled: false,
    });
    expect(practiceButton().dataset.aqeButtonState).toBe("default");
  });

  it("adds markers mid-practice and includes them in longer-suffix navigation", async () => {
    const { svg } = await prepareChorusingGraph();
    prepareHtmlAudio();

    practiceButton().click();
    await Promise.resolve();
    clickMarkerRail(svg, 0.25);
    await Promise.resolve();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingActiveMarkerIndex: 2,
      chorusingActiveStartMs: 500,
      chorusingMarkersMs: [0, 250, 500],
      playbackStartMs: 500,
    });

    nextButton().click();
    await Promise.resolve();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingActiveMarkerIndex: 1,
      chorusingActiveStartMs: 250,
      playbackStartMs: 250,
      selectionStartMs: 250,
    });
  });

  it("opens a dedicated chorusing split menu and promotes its defaults", async () => {
    await prepareChorusingGraph();

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-chorusing-practice-menu"]')!.click();

    await waitFor(() => {
      expect(document.querySelector('[data-testid="aqe-split-0-chorusing-popover"]')).not.toBeNull();
    });

    const pauseInput = document.querySelector<HTMLInputElement>(
      '[data-testid="aqe-split-0-chorusing-pause-seconds"]',
    )!;
    pauseInput.value = "1.5";
    pauseInput.dispatchEvent(new Event("input", { bubbles: true }));

    const autoAdvance = document.querySelector<HTMLInputElement>(
      '[data-testid="aqe-split-0-chorusing-auto-advance"]',
    )!;
    autoAdvance.click();

    const repeatCount = document.querySelector<HTMLInputElement>(
      '[data-testid="aqe-split-0-chorusing-repeat-count"]',
    )!;
    repeatCount.value = "4";
    repeatCount.dispatchEvent(new Event("input", { bubbles: true }));

    expect(window.__aqeSplitButtonStates?.[0]).toMatchObject({
      chorusingPauseSeconds: 1.5,
      chorusingAutoAdvance: true,
      chorusingRepeatCount: 4,
    });

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-chorusing-save-default"]')!.click();

    expect(window.__aqePopPendingSplitDefaultSaveRequest?.()).toEqual({
      defaults: {
        chorusingPauseSeconds: 1.5,
        chorusingAutoAdvanceByDefault: true,
        chorusingAutoAdvanceRepeats: 4,
      },
      fieldOrd: 0,
    });
    expect(window.__AQE_EDITOR_CONFIG__?.splitButtonDefaults).toMatchObject({
      chorusingPauseSeconds: 1.5,
      chorusingAutoAdvanceByDefault: true,
      chorusingAutoAdvanceRepeats: 4,
    });
  });

  it("auto-advances chorusing after the configured repeat count", async () => {
    await prepareChorusingGraph();
    const audio = prepareHtmlAudio();

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-chorusing-practice-menu"]')!.click();
    await waitFor(() => {
      expect(document.querySelector('[data-testid="aqe-split-0-chorusing-popover"]')).not.toBeNull();
    });
    document.querySelector<HTMLInputElement>('[data-testid="aqe-split-0-chorusing-auto-advance"]')!.click();
    const repeatCount = document.querySelector<HTMLInputElement>(
      '[data-testid="aqe-split-0-chorusing-repeat-count"]',
    )!;
    repeatCount.value = "2";
    repeatCount.dispatchEvent(new Event("input", { bubbles: true }));

    practiceButton().click();
    await Promise.resolve();
    await Promise.resolve();

    expect(audio.play).toHaveBeenCalledTimes(1);
    expect(window.__aqePendingPlaybackRequest).toBeNull();
    expect(bridgeCommands().filter((command) => command === "aqe:play")).toHaveLength(0);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingActiveMarkerIndex: 1,
      chorusingState: "playing",
      playbackStartMs: 500,
      repeatEnabled: true,
    });
    expect(window.__aqePendingPlaybackRequest).toBeNull();
    expect(bridgeCommands().filter((command) => command === "aqe:play")).toHaveLength(0);

    handlePlaybackBoundary(visualizer(), 1000);
    await Promise.resolve();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingActiveMarkerIndex: 1,
      chorusingRepeatPassesCompleted: 1,
      chorusingState: "playing",
    });
    expect(audio.play).toHaveBeenCalledTimes(1);
    expect(window.__aqePendingPlaybackRequest).toBeNull();

    handlePlaybackBoundary(visualizer(), 1000);
    await Promise.resolve();
    await Promise.resolve();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingActiveMarkerIndex: 0,
      chorusingRepeatPassesCompleted: 0,
      chorusingState: "playing",
      playbackStartMs: 0,
      selectionStartMs: 0,
    });
    expect(audio.play).toHaveBeenCalledTimes(2);
    expect(window.__aqePendingPlaybackRequest).toBeNull();
    expect(bridgeCommands().filter((command) => command === "aqe:play")).toHaveLength(0);
  });

  it("ignores stale chorusing loop boundaries after auto-advance starts the next suffix", async () => {
    await prepareChorusingGraph();
    const audio = prepareHtmlAudio();
    setChorusingAutoAdvanceForField(0, true);
    setChorusingRepeatCountForField(0, 1);

    practiceButton().click();
    await Promise.resolve();
    await Promise.resolve();
    expect(window.__aqePendingPlaybackRequest).toBeNull();
    expect(bridgeCommands().filter((command) => command === "aqe:play")).toHaveLength(0);

    const stalePass = {
      endMs: 1000,
      loop: true,
      regionMode: "selection" as const,
      resetCursorMs: 500,
      startMs: 500,
    };
    expect(handleChorusingLoopBoundary(visualizer(), stalePass)).toBe(true);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingActiveMarkerIndex: 0,
      selectionStartMs: 0,
    });

    expect(handleChorusingLoopBoundary(visualizer(), stalePass)).toBe(false);
    await Promise.resolve();
    await Promise.resolve();

    expect(audio.play).toHaveBeenCalledTimes(2);
    expect(window.__aqePendingPlaybackRequest).toBeNull();
    expect(bridgeCommands().filter((command) => command === "aqe:play")).toHaveLength(0);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingActiveMarkerIndex: 0,
      chorusingRepeatPassesCompleted: 0,
      playbackStartMs: 0,
      selectionStartMs: 0,
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

function practiceButton(): HTMLButtonElement {
  return document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-chorusing-practice"]')!;
}

function nextButton(): HTMLButtonElement {
  return document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-chorusing-next"]')!;
}

function previousButton(): HTMLButtonElement {
  return document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-chorusing-previous"]')!;
}

function visualizer(): HTMLElement {
  return document.querySelector('.aqe-visualizer[data-aqe-field-ord="0"]')!;
}
