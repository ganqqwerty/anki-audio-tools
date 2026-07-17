import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  disposeEditorRuntime,
  initializeEditorRuntime,
  scan,
} from "../src/editor-inline/runtime.js";
import { PLOT, plotWidth } from "../src/editor-inline/plot.js";
import {
  commandLog,
  dragGraphSelection,
  graphClientX,
  muteConsole,
  renderFields,
  setGraphBounds,
  track,
} from "./editor-inline.integration.helpers.js";

describe("editor inline viewport controls", () => {
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

  it("zooms, fits, and zooms to selection from graph controls", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 500);
    await Promise.resolve();
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);

    let state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBe(0);
    expect(state?.viewportEndMs).toBe(track.durationMs);

    window.__aqeSetCursorForTest?.(0, track.durationMs / 2, false);
    for (let index = 0; index < 4; index += 1) {
      document.querySelector<HTMLButtonElement>('[data-testid="aqe-zoom-in-0"]')?.click();
    }
    state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBeGreaterThan(0);
    expect(state?.viewportEndMs).toBeLessThan(track.durationMs);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-zoom-fit-0"]')?.click();
    state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBe(0);
    expect(state?.viewportEndMs).toBe(track.durationMs);

    dragGraphSelection(svg, 0.25, 0.5);
    await Promise.resolve();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-zoom-selection-0"]')?.click();
    state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBeLessThanOrEqual(state?.selectionStartMs ?? 0);
    expect(state?.viewportEndMs).toBeGreaterThanOrEqual(state?.selectionEndMs ?? 0);
    expect((state?.viewportEndMs ?? 0) - (state?.viewportStartMs ?? 0)).toBeLessThan(track.durationMs);
  });

  it("uses graph wheel and keyboard gestures for horizontal zoom only", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 500);
    await Promise.resolve();
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    const plot = document.querySelector<HTMLElement>('[data-testid="aqe-visualizer-plot-0"]')!;
    setGraphBounds(svg);

    plot.dispatchEvent(new WheelEvent("wheel", {
      bubbles: true,
      clientX: graphClientX(svg, 0.5),
      ctrlKey: true,
      deltaY: -100,
    }));
    let state = window.__aqeGraphStateForTest?.(0);
    let span = (state?.viewportEndMs ?? 0) - (state?.viewportStartMs ?? 0);
    expect(span).toBeLessThan(track.durationMs);
    expect(span).toBeGreaterThan(track.durationMs * 0.75);

    for (let index = 0; index < 4; index += 1) {
      plot.dispatchEvent(new WheelEvent("wheel", {
        bubbles: true,
        clientX: graphClientX(svg, 0.5),
        ctrlKey: true,
        deltaY: -100,
      }));
    }
    state = window.__aqeGraphStateForTest?.(0);

    const beforeShiftPanStart = state?.viewportStartMs ?? 0;
    plot.dispatchEvent(new WheelEvent("wheel", {
      bubbles: true,
      clientX: graphClientX(svg, 0.5),
      deltaX: 100,
      shiftKey: true,
    }));
    state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBeGreaterThan(beforeShiftPanStart);

    const beforePanStart = state?.viewportStartMs ?? 0;
    plot.dispatchEvent(new WheelEvent("wheel", {
      bubbles: true,
      clientX: graphClientX(svg, 0.5),
      deltaX: -100,
    }));
    state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBeLessThan(beforePanStart);

    const beforeVerticalStart = state?.viewportStartMs ?? 0;
    plot.dispatchEvent(new WheelEvent("wheel", {
      bubbles: true,
      clientX: graphClientX(svg, 0.5),
      deltaY: 100,
    }));
    state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBe(beforeVerticalStart);

    const visualizer = document.querySelector<HTMLElement>('[data-testid="aqe-graph-0"]')!;
    visualizer.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, key: "0" }));
    state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBe(0);
    expect(state?.viewportEndMs).toBe(track.durationMs);
  });

  it("scrolls the visible time viewport with a horizontal scrollbar only when audio is scrollable", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 500);
    await Promise.resolve();
    const scrollbar = document.querySelector<HTMLElement>('[data-testid="aqe-time-scrollbar-0"]')!;
    const scrollport = document.querySelector<HTMLDivElement>('[data-testid="aqe-time-scrollbar-scroll-0"]')!;
    Object.defineProperty(scrollport, "clientWidth", { configurable: true, value: 200 });

    expect(scrollbar.hidden).toBe(true);

    for (let index = 0; index < 4; index += 1) {
      document.querySelector<HTMLButtonElement>('[data-testid="aqe-zoom-in-0"]')?.click();
    }
    await Promise.resolve();
    await Promise.resolve();
    expect(scrollbar.hidden).toBe(false);
    const beforeScroll = window.__aqeGraphStateForTest?.(0);
    expect(scrollport.querySelector<HTMLElement>(".aqe-time-scrollbar-spacer")?.style.width).not.toBe("100%");

    scrollport.scrollLeft = 10_000;
    scrollport.dispatchEvent(new Event("scroll"));

    const afterScroll = window.__aqeGraphStateForTest?.(0);
    expect(afterScroll?.viewportStartMs).toBeGreaterThan(beforeScroll?.viewportStartMs ?? 0);
    expect(afterScroll?.viewportEndMs).toBe(track.durationMs);
  });

  it("projects and hides the stopped cursor against the zoomed viewport", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 500);
    await Promise.resolve();
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);

    window.__aqeSetTimeViewportForTest?.(0, 250, 750);
    window.__aqeSetCursorForTest?.(0, 600, false);
    let state = window.__aqeGraphStateForTest?.(0);

    expect(state).toMatchObject({
      cursorMs: 600,
      progressMs: 600,
      timecodeFlagCurrent: "600 ms",
      timecodeFlagPitch: " / 260 Hz",
      timecodeFlagVisible: true,
    });
    expect(state?.cursorX).toBeCloseTo(PLOT.left + plotWidth() * 0.7);

    window.__aqeSetCursorForTest?.(0, 900, false);
    state = window.__aqeGraphStateForTest?.(0);

    expect(state).toMatchObject({
      cursorMs: 900,
      progressMs: 900,
      timecodeFlagCurrent: "900 ms",
      timecodeFlagVisible: false,
    });
  });

  it("scrolls away from and back to the stopped cursor without committing cursor state", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 250);
    await Promise.resolve();
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    const scrollport = document.querySelector<HTMLDivElement>('[data-testid="aqe-time-scrollbar-scroll-0"]')!;
    Object.defineProperty(scrollport, "clientWidth", { configurable: true, value: 200 });
    setGraphBounds(svg);
    window.__aqeSetTimeViewportForTest?.(0, 0, 500);
    window.__aqeSetCursorForTest?.(0, 250, false);
    await Promise.resolve();
    await Promise.resolve();
    const commandsBeforeScroll = commandLog().slice();

    scrollport.scrollLeft = 200;
    scrollport.dispatchEvent(new Event("scroll"));
    let state = window.__aqeGraphStateForTest?.(0);
    expect(state).toMatchObject({
      cursorMs: 250,
      timecodeFlagVisible: false,
      viewportEndMs: 1000,
      viewportStartMs: 500,
    });

    scrollport.scrollLeft = 0;
    scrollport.dispatchEvent(new Event("scroll"));
    state = window.__aqeGraphStateForTest?.(0);
    expect(state).toMatchObject({
      cursorMs: 250,
      timecodeFlagVisible: true,
      viewportEndMs: 500,
      viewportStartMs: 0,
    });
    expect(state?.cursorX).toBeCloseTo(PLOT.left + plotWidth() * 0.5);
    expect(commandLog().slice(commandsBeforeScroll.length)).not.toContain("aqe:set-cursor");
  });

  it("fits the whole clip when a graph is redrawn for a new track", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 0);
    window.__aqeSetTimeViewportForTest?.(0, 250, 750);

    window.__aqeSetVisualizer?.(0, { ...track, durationMs: 2000, sourceFilename: "next.mp3" }, 0);

    const state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBe(0);
    expect(state?.viewportEndMs).toBe(2000);
  });
});
