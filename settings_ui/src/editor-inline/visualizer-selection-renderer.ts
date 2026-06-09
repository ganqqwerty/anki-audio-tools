import type { PlaybackRegion } from "./playback-state.js";
import { PLOT, type PlotGeometry, plotGeometryForSvg, svgViewBoxScale, xForMs } from "./plot.js";
import { msVisibleInViewport } from "./time-viewport.js";
import type { VisualizerElement } from "./types.js";
import { readVisualizerTimeViewport, readVisualizerDurationMs } from "./visualizer-state.js";

const SELECTION_TOOLBAR_RIGHT_OFFSET_PX = 6;
const SELECTION_SHIFT_BUTTON_MIN_BAND_WIDTH_PX = 52;

export function renderSelection(
  visualizer: VisualizerElement,
  selection: PlaybackRegion | null,
  draftSelection: PlaybackRegion | null,
): void {
  const band = visualizer.querySelector<SVGRectElement>(".aqe-selection");
  const outsideShadeBefore = visualizer.querySelector<SVGRectElement>(".aqe-selection-outside-preview-before");
  const outsideShadeAfter = visualizer.querySelector<SVGRectElement>(".aqe-selection-outside-preview-after");
  const startEdge = visualizer.querySelector<HTMLElement>(".aqe-selection-start");
  const endEdge = visualizer.querySelector<HTMLElement>(".aqe-selection-end");
  const startHandle = visualizer.querySelector<HTMLElement>(".aqe-selection-resize-start");
  const endHandle = visualizer.querySelector<HTMLElement>(".aqe-selection-resize-end");
  const activeSelection = draftSelection ?? selection;
  const durationMs = readVisualizerDurationMs(visualizer);
  const plot = plotGeometryForVisualizer(visualizer);
  if (!band || !startEdge || !endEdge || !startHandle || !endHandle || !activeSelection || !durationMs) {
    band?.setAttribute("width", "0");
    band?.setAttribute("visibility", "hidden");
    band?.classList.remove("aqe-selection-draft");
    hideOutsideShade(outsideShadeBefore, outsideShadeAfter);
    startEdge && (startEdge.hidden = true);
    endEdge && (endEdge.hidden = true);
    startHandle && (startHandle.hidden = true);
    endHandle && (endHandle.hidden = true);
    startHandle?.classList.remove("aqe-selection-resize-dragging");
    endHandle?.classList.remove("aqe-selection-resize-dragging");
    clearSelectionOverlayGeometry(visualizer);
    return;
  }
  const viewport = readVisualizerTimeViewport(visualizer);
  const visibleStartMs = Math.max(activeSelection.startMs, viewport.startMs);
  const visibleEndMs = Math.min(activeSelection.endMs, viewport.endMs);
  if (visibleEndMs < visibleStartMs) {
    band.setAttribute("width", "0");
    band.setAttribute("visibility", "hidden");
    band.classList.remove("aqe-selection-draft");
    hideOutsideShade(outsideShadeBefore, outsideShadeAfter);
    startEdge.hidden = true;
    endEdge.hidden = true;
    startHandle.hidden = true;
    endHandle.hidden = true;
    clearSelectionOverlayGeometry(visualizer);
    return;
  }
  const startX = xForMs(visibleStartMs, durationMs, viewport, plot);
  const endX = xForMs(visibleEndMs, durationMs, viewport, plot);
  const actualStartVisible = msVisibleInViewport(activeSelection.startMs, viewport);
  const actualEndVisible = msVisibleInViewport(activeSelection.endMs, viewport);
  const actualStartX = xForMs(activeSelection.startMs, durationMs, viewport, plot);
  const actualEndX = xForMs(activeSelection.endMs, durationMs, viewport, plot);
  const plotTop = plot.top;
  const plotBottom = plot.height - plot.bottom;
  const plotHeight = plotBottom - plotTop;
  band.setAttribute("visibility", "visible");
  band.classList.toggle("aqe-selection-draft", draftSelection !== null);
  band.setAttribute("x", startX.toFixed(2));
  band.setAttribute("y", String(plotTop));
  band.setAttribute("width", Math.max(0, endX - startX).toFixed(2));
  band.setAttribute("height", String(plotHeight));
  renderOutsideShade(outsideShadeBefore, outsideShadeAfter, plot, startX, endX, plotTop, plotHeight);
  startEdge.hidden = !actualStartVisible;
  endEdge.hidden = !actualEndVisible;
  const showHandles = selection !== null;
  const handlesDragging = selection !== null && draftSelection !== null;
  for (const [handle, visible] of [
    [startHandle, actualStartVisible],
    [endHandle, actualEndVisible],
  ] as const) {
    const showEdgeHandle = showHandles && visible;
    handle.hidden = !showEdgeHandle;
    handle.classList.toggle("aqe-selection-resize-dragging", handlesDragging);
  }
  setSelectionOverlayGeometry(
    visualizer,
    plot,
    actualStartX,
    actualEndX,
    startX,
    endX,
    plotTop,
    plotBottom,
    actualStartVisible,
    actualEndVisible,
  );
}

function hideOutsideShade(
  outsideShadeBefore: SVGRectElement | null,
  outsideShadeAfter: SVGRectElement | null,
): void {
  for (const node of [outsideShadeBefore, outsideShadeAfter]) {
    node?.setAttribute("width", "0");
    node?.setAttribute("visibility", "hidden");
  }
}

function renderOutsideShade(
  outsideShadeBefore: SVGRectElement | null,
  outsideShadeAfter: SVGRectElement | null,
  plot: PlotGeometry,
  startX: number,
  endX: number,
  plotTop: number,
  plotHeight: number,
): void {
  const plotRightEdge = plot.width - plot.right;
  if (outsideShadeBefore) {
    outsideShadeBefore.setAttribute("visibility", "visible");
    outsideShadeBefore.setAttribute("x", String(plot.left));
    outsideShadeBefore.setAttribute("y", String(plotTop));
    outsideShadeBefore.setAttribute("width", Math.max(0, startX - plot.left).toFixed(2));
    outsideShadeBefore.setAttribute("height", String(plotHeight));
  }
  if (outsideShadeAfter) {
    outsideShadeAfter.setAttribute("visibility", "visible");
    outsideShadeAfter.setAttribute("x", endX.toFixed(2));
    outsideShadeAfter.setAttribute("y", String(plotTop));
    outsideShadeAfter.setAttribute("width", Math.max(0, plotRightEdge - endX).toFixed(2));
    outsideShadeAfter.setAttribute("height", String(plotHeight));
  }
}

function plotGeometryForVisualizer(visualizer: VisualizerElement): PlotGeometry {
  const svg = visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg");
  return svg ? plotGeometryForSvg(svg) : PLOT;
}

function setSelectionOverlayGeometry(
  visualizer: VisualizerElement,
  plot: PlotGeometry,
  actualStartX: number,
  actualEndX: number,
  startX: number,
  endX: number,
  plotTop: number,
  plotBottom: number,
  actualStartVisible: boolean,
  actualEndVisible: boolean,
): void {
  const wrapper = visualizer.querySelector<HTMLElement>(".aqe-visualizer-plot");
  const svg = visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg");
  if (!wrapper || !svg) return;
  const scale = svgViewBoxScale(svg);
  const viewportLeftPx = Number(svg.clientLeft) || 0;
  const viewportTopPx = Number(svg.clientTop) || 0;
  const viewportWidthPx = Number(svg.clientWidth) || PLOT.width;
  const viewportHeightPx = Number(svg.clientHeight) || PLOT.height;
  const wrapperWidthPx = Number(wrapper.clientWidth) || viewportLeftPx + viewportWidthPx;
  const wrapperHeightPx = Number(wrapper.clientHeight) || viewportTopPx + viewportHeightPx;
  const startPx = viewportLeftPx + startX * scale.x;
  const endPx = viewportLeftPx + endX * scale.x;
  const actualStartPx = viewportLeftPx + actualStartX * scale.x;
  const actualEndPx = viewportLeftPx + actualEndX * scale.x;
  const plotTopPx = viewportTopPx + plotTop * scale.y;
  const plotBottomPx = viewportTopPx + plotBottom * scale.y;
  const plotHeightPx = Math.max(0, plotBottomPx - plotTopPx);
  const plotLeftPx = viewportLeftPx + plot.left * scale.x;
  const plotRightEdgePx = viewportLeftPx + (plot.width - plot.right) * scale.x;
  const plotRightPx = Math.max(0, wrapperWidthPx - plotRightEdgePx);
  const toolbarLeftPx = Math.max(
    plotLeftPx,
    Math.min(endPx, plotRightEdgePx - SELECTION_TOOLBAR_RIGHT_OFFSET_PX),
  );
  const toolbarTopPx = Math.max(plotTopPx, Math.min(plotBottomPx, wrapperHeightPx - 34));
  const shiftTopPx = Math.max(plotTopPx, plotBottomPx - 20);
  const hideInnerButtons = Math.max(0, endPx - startPx) < SELECTION_SHIFT_BUTTON_MIN_BAND_WIDTH_PX;
  wrapper.dataset.selectionOverlayReady = "true";
  wrapper.dataset.selectionShiftHideInner = hideInnerButtons ? "true" : "false";
  wrapper.dataset.selectionStartEdgeVisible = actualStartVisible ? "true" : "false";
  wrapper.dataset.selectionEndEdgeVisible = actualEndVisible ? "true" : "false";
  wrapper.style.setProperty("--aqe-selection-start-px", `${startPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-selection-end-px", `${endPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-selection-start-edge-px", `${actualStartPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-selection-end-edge-px", `${actualEndPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-selection-bottom-px", `${plotBottomPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-selection-shift-top-px", `${shiftTopPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-selection-toolbar-left-px", `${toolbarLeftPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-selection-toolbar-top-px", `${toolbarTopPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-plot-left-px", `${plotLeftPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-plot-right-px", `${plotRightPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-plot-top-px", `${plotTopPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-plot-height-px", `${plotHeightPx.toFixed(2)}px`);
  setOverlayNodePosition(wrapper.querySelector<HTMLElement>(".aqe-selection-toolbar"), toolbarLeftPx, toolbarTopPx);
}

function clearSelectionOverlayGeometry(visualizer: VisualizerElement): void {
  const wrapper = visualizer.querySelector<HTMLElement>(".aqe-visualizer-plot");
  if (!wrapper) return;
  wrapper.dataset.selectionOverlayReady = "false";
  for (const property of [
    "--aqe-selection-start-px",
    "--aqe-selection-end-px",
    "--aqe-selection-start-edge-px",
    "--aqe-selection-end-edge-px",
    "--aqe-selection-bottom-px",
    "--aqe-selection-shift-top-px",
    "--aqe-selection-toolbar-left-px",
    "--aqe-selection-toolbar-top-px",
    "--aqe-plot-left-px",
    "--aqe-plot-right-px",
    "--aqe-plot-top-px",
    "--aqe-plot-height-px",
  ]) {
    wrapper.style.removeProperty(property);
  }
  wrapper.dataset.selectionShiftHideInner = "false";
  wrapper.dataset.selectionStartEdgeVisible = "false";
  wrapper.dataset.selectionEndEdgeVisible = "false";
  clearOverlayNodePosition(wrapper.querySelector<HTMLElement>(".aqe-selection-toolbar"));
}

function setOverlayNodePosition(node: HTMLElement | null, leftPx: number, topPx: number): void {
  if (!node) return;
  node.style.left = `${leftPx.toFixed(2)}px`;
  node.style.top = `${topPx.toFixed(2)}px`;
}

function clearOverlayNodePosition(node: HTMLElement | null): void {
  if (!node) return;
  node.style.removeProperty("left");
  node.style.removeProperty("top");
}
