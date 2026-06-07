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
      const initialIntensityPath = document.querySelector<SVGPathElement>('[data-testid="aqe-intensity-0"]')!
        .getAttribute("d");
      const initialClipRect = svg.querySelector<SVGRectElement>("clipPath > rect")!;
      const initialClipLeft = Number(initialClipRect.getAttribute("x"));
      const initialClipWidth = Number(initialClipRect.getAttribute("width"));
      const initialTickX = Number(
        Array.from(svg.querySelectorAll<SVGLineElement>(".aqe-x-tick")).at(-1)!.getAttribute("x1"),
      );
      const initialState = window.__aqeGraphStateForTest?.(0);
      expect(svg.getAttribute("viewBox")).toBe("0 0 620 150");

      setGraphBounds(svg, { width: 1240 });
      for (const callback of resizeCallbacks) callback([], {} as ResizeObserver);

      const intensity = document.querySelector<SVGPathElement>('[data-testid="aqe-intensity-0"]')!;
      const clipRect = svg.querySelector<SVGRectElement>("clipPath > rect")!;
      const lastTick = Array.from(svg.querySelectorAll<SVGLineElement>(".aqe-x-tick")).at(-1)!;
      const state = window.__aqeGraphStateForTest?.(0);
      const resizedClipLeft = Number(clipRect.getAttribute("x"));
      const resizedClipWidth = Number(clipRect.getAttribute("width"));
      const resizedTickX = Number(lastTick.getAttribute("x1"));
      const initialCursorRatio = ((initialState?.cursorX ?? 0) - initialClipLeft) / initialClipWidth;
      const resizedCursorRatio = ((state?.cursorX ?? 0) - resizedClipLeft) / resizedClipWidth;

      expect(svg.getAttribute("viewBox")).toBe("0 0 1240 150");
      expect(initialIntensityPath).not.toBe("");
      expect(intensity.getAttribute("d")).not.toBe("");
      expect(intensity.getAttribute("d")).not.toBe(initialIntensityPath);
      expect(document.querySelectorAll(".aqe-pitch-path").length).toBeGreaterThan(0);
      expect(resizedClipWidth).toBeGreaterThan(initialClipWidth);
      expect(resizedTickX).toBeGreaterThan(initialTickX);
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
