import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import { muteConsole, renderFields, setGraphBounds, track } from "./editor-inline.integration.helpers.js";

describe("editor inline visualizer layout integration", () => {
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

  it("redraws graph layers when the rendered SVG width changes after mount", async () => {
    const resizeCallbacks: Array<(entries: never[], observer: ResizeObserver) => void> = [];
    const previousResizeObserver = globalThis.ResizeObserver;
    const previousWindowResizeObserver = window.ResizeObserver;
    class FakeResizeObserver implements ResizeObserver {
      constructor(callback: (entries: never[], observer: ResizeObserver) => void) {
        resizeCallbacks.push(callback);
      }

      disconnect(): void {
        return undefined;
      }

      observe(): void {
        return undefined;
      }

      unobserve(): void {
        return undefined;
      }
    }
    Object.defineProperty(globalThis, "ResizeObserver", {
      configurable: true,
      value: FakeResizeObserver,
    });
    Object.defineProperty(window, "ResizeObserver", {
      configurable: true,
      value: FakeResizeObserver,
    });
    try {
      initializeEditorRuntime({ audioFieldIndices: [0] });
      scan({ audioFieldIndices: [0] });
      await Promise.resolve();
      const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
      setGraphBounds(svg, { width: 620 });
      window.__aqeSetVisualizer?.(0, track, 250);
      const initialViewBox = svg.getAttribute("viewBox")!;
      const initialClipRect = svg.querySelector<SVGRectElement>("clipPath > rect")!;
      const initialClipLeft = Number(initialClipRect.getAttribute("x"));
      const initialClipWidth = Number(initialClipRect.getAttribute("width"));
      const initialIntensityPath = document.querySelector<SVGPathElement>('[data-testid="aqe-intensity-0"]')!
        .getAttribute("d");
      const initialState = window.__aqeGraphStateForTest?.(0);
      const initialCursorRatio = ((initialState?.cursorX ?? 0) - initialClipLeft) / initialClipWidth;

      setGraphBounds(svg, { width: 1240 });
      for (const callback of resizeCallbacks) callback([], {} as ResizeObserver);

      const intensity = document.querySelector<SVGPathElement>('[data-testid="aqe-intensity-0"]')!;
      const state = window.__aqeGraphStateForTest?.(0);
      const resizedClipRect = svg.querySelector<SVGRectElement>("clipPath > rect")!;
      const resizedClipLeft = Number(resizedClipRect.getAttribute("x"));
      const resizedClipWidth = Number(resizedClipRect.getAttribute("width"));
      const resizedCursorRatio = ((state?.cursorX ?? 0) - resizedClipLeft) / resizedClipWidth;
      const resizedViewBox = svg.getAttribute("viewBox")!;

      expect(resizedViewBox).not.toBe(initialViewBox);
      expect(initialIntensityPath).not.toBe("");
      expect(intensity.getAttribute("d")).not.toBe("");
      expect(intensity.getAttribute("d")).not.toBe(initialIntensityPath);
      expect(document.querySelectorAll(".aqe-pitch-path").length).toBeGreaterThan(0);
      expect(resizedClipWidth).toBeGreaterThan(initialClipWidth);
      expect(state?.cursorMs).toBe(250);
      expect(resizedCursorRatio).toBeCloseTo(initialCursorRatio, 2);
    } finally {
      Object.defineProperty(globalThis, "ResizeObserver", {
        configurable: true,
        value: previousResizeObserver,
      });
      Object.defineProperty(window, "ResizeObserver", {
        configurable: true,
        value: previousWindowResizeObserver,
      });
    }
  });
});
