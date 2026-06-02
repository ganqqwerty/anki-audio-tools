import type { PlaybackRegion } from "./playback-state.js";
import { PLOT, type PlotGeometry, plotGeometryForSvg, svgViewBoxScale, xForMs } from "./plot.js";
import { msVisibleInViewport } from "./time-viewport.js";
import type { VisualizerElement } from "./types.js";
import { readVisualizerTimeViewport } from "./visualizer-state.js";

const SELECTION_TOOLBAR_RIGHT_OFFSET_PX = 6;
const SEGMENT_PANEL_MAX_WIDTH_PX = 360;
const SEGMENT_PANEL_TOP_OFFSET_PX = 40;

export function renderSelection(
  visualizer: VisualizerElement,
  selection: PlaybackRegion | null,
  draftSelection: PlaybackRegion | null,
): void {
  const band = visualizer.querySelector<SVGRectElement>(".aqe-selection");
  const startEdge = visualizer.querySelector<SVGLineElement>(".aqe-selection-start");
  const endEdge = visualizer.querySelector<SVGLineElement>(".aqe-selection-end");
  const startHandle = visualizer.querySelector<SVGRectElement>(".aqe-selection-resize-start");
  const endHandle = visualizer.querySelector<SVGRectElement>(".aqe-selection-resize-end");
  const startGrip = visualizer.querySelector<SVGGElement>(".aqe-selection-resize-grip-start");
  const endGrip = visualizer.querySelector<SVGGElement>(".aqe-selection-resize-grip-end");
  const activeSelection = draftSelection ?? selection;
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  const plot = plotGeometryForVisualizer(visualizer);
  if (!band || !startEdge || !endEdge || !activeSelection || !durationMs) {
    band?.setAttribute("width", "0");
    band?.setAttribute("visibility", "hidden");
    band?.classList.remove("aqe-selection-draft");
    startEdge?.setAttribute("visibility", "hidden");
    endEdge?.setAttribute("visibility", "hidden");
    startHandle?.setAttribute("visibility", "hidden");
    endHandle?.setAttribute("visibility", "hidden");
    startHandle?.classList.remove("aqe-selection-resize-dragging");
    endHandle?.classList.remove("aqe-selection-resize-dragging");
    startGrip?.setAttribute("visibility", "hidden");
    endGrip?.setAttribute("visibility", "hidden");
    startGrip?.classList.remove("aqe-selection-resize-dragging");
    endGrip?.classList.remove("aqe-selection-resize-dragging");
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
    startEdge.setAttribute("visibility", "hidden");
    endEdge.setAttribute("visibility", "hidden");
    startHandle?.setAttribute("visibility", "hidden");
    endHandle?.setAttribute("visibility", "hidden");
    startGrip?.setAttribute("visibility", "hidden");
    endGrip?.setAttribute("visibility", "hidden");
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
  const handleHeight = plotHeight * 0.8;
  const handleY = plotTop + (plotHeight - handleHeight) / 2;
  const handleCenterY = handleY + handleHeight / 2;
  band.setAttribute("visibility", "visible");
  band.classList.toggle("aqe-selection-draft", draftSelection !== null);
  band.setAttribute("x", startX.toFixed(2));
  band.setAttribute("y", String(plotTop));
  band.setAttribute("width", Math.max(0, endX - startX).toFixed(2));
  band.setAttribute("height", String(plotHeight));
  startEdge.setAttribute("visibility", actualStartVisible ? "visible" : "hidden");
  endEdge.setAttribute("visibility", actualEndVisible ? "visible" : "hidden");
  for (const [edge, x] of [[startEdge, actualStartX], [endEdge, actualEndX]] as const) {
    edge.setAttribute("x1", x.toFixed(2));
    edge.setAttribute("x2", x.toFixed(2));
    edge.setAttribute("y1", String(plotTop));
    edge.setAttribute("y2", String(plotBottom));
  }
  const showHandles = selection !== null;
  const handlesDragging = selection !== null && draftSelection !== null;
  for (const [handle, grip, x, visible] of [
    [startHandle, startGrip, actualStartX, actualStartVisible],
    [endHandle, endGrip, actualEndX, actualEndVisible],
  ] as const) {
    const showEdgeHandle = showHandles && visible;
    handle?.setAttribute("visibility", showEdgeHandle ? "visible" : "hidden");
    handle?.classList.toggle("aqe-selection-resize-dragging", handlesDragging);
    handle?.setAttribute("x", (x - 5).toFixed(2));
    handle?.setAttribute("y", handleY.toFixed(2));
    handle?.setAttribute("width", "10");
    handle?.setAttribute("height", handleHeight.toFixed(2));
    grip?.setAttribute("visibility", showEdgeHandle ? "visible" : "hidden");
    grip?.classList.toggle("aqe-selection-resize-dragging", handlesDragging);
    grip?.setAttribute("transform", `translate(${x.toFixed(2)} ${handleCenterY.toFixed(2)})`);
  }
  setSelectionOverlayGeometry(visualizer, plot, startX, endX, plotTop, plotBottom);
}

function plotGeometryForVisualizer(visualizer: VisualizerElement): PlotGeometry {
  const svg = visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg");
  return svg ? plotGeometryForSvg(svg) : PLOT;
}

function setSelectionOverlayGeometry(
  visualizer: VisualizerElement,
  plot: PlotGeometry,
  startX: number,
  endX: number,
  plotTop: number,
  plotBottom: number,
): void {
  const wrapper = visualizer.querySelector<HTMLElement>(".aqe-visualizer-plot");
  const svg = visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg");
  if (!wrapper || !svg) return;
  const rect = svg.getBoundingClientRect();
  const rectWidth = Number(rect.width) || PLOT.width;
  const scale = svgViewBoxScale(svg);
  const startPx = startX * scale.x;
  const endPx = endX * scale.x;
  const plotTopPx = plotTop * scale.y;
  const plotBottomPx = plotBottom * scale.y;
  const plotHeightPx = Math.max(0, plotBottomPx - plotTopPx);
  const plotLeftPx = plot.left * scale.x;
  const plotRightEdgePx = (plot.width - plot.right) * scale.x;
  const plotRightPx = Math.max(0, rectWidth - plotRightEdgePx);
  const plotWidthPx = Math.max(0, plotRightEdgePx - plotLeftPx);
  const contentHeightPx = plot.height * scale.y;
  const toolbarLeftPx = Math.max(
    plotLeftPx,
    Math.min(endPx, plotRightEdgePx - SELECTION_TOOLBAR_RIGHT_OFFSET_PX),
  );
  const toolbarTopPx = Math.max(plotTopPx, Math.min(plotBottomPx, contentHeightPx - 34));
  const toolbarRightPx = Math.max(
    plotLeftPx,
    Math.min(toolbarLeftPx + SELECTION_TOOLBAR_RIGHT_OFFSET_PX, plotRightEdgePx),
  );
  const segmentPanelWidthPx = Math.min(SEGMENT_PANEL_MAX_WIDTH_PX, plotWidthPx);
  const segmentPanelLeftPx = Math.max(
    plotLeftPx,
    Math.min(toolbarRightPx - segmentPanelWidthPx, plotRightEdgePx - segmentPanelWidthPx),
  );
  const segmentPanelTopPx = toolbarTopPx + SEGMENT_PANEL_TOP_OFFSET_PX;
  wrapper.dataset.selectionOverlayReady = "true";
  wrapper.style.setProperty("--aqe-selection-start-px", `${startPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-selection-end-px", `${endPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-selection-bottom-px", `${plotBottomPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-selection-toolbar-left-px", `${toolbarLeftPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-selection-toolbar-top-px", `${toolbarTopPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-plot-left-px", `${plotLeftPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-plot-right-px", `${plotRightPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-plot-top-px", `${plotTopPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-plot-height-px", `${plotHeightPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-segment-panel-left-px", `${segmentPanelLeftPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-segment-panel-top-px", `${segmentPanelTopPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-segment-panel-width-px", `${segmentPanelWidthPx.toFixed(2)}px`);
  setOverlayNodePosition(wrapper.querySelector<HTMLElement>(".aqe-selection-toolbar"), toolbarLeftPx, toolbarTopPx);
  setOverlayNodePosition(wrapper.querySelector<HTMLElement>(".aqe-selection-toolbar-dot"), toolbarLeftPx, toolbarTopPx);
}

function clearSelectionOverlayGeometry(visualizer: VisualizerElement): void {
  const wrapper = visualizer.querySelector<HTMLElement>(".aqe-visualizer-plot");
  if (!wrapper) return;
  wrapper.dataset.selectionOverlayReady = "false";
  for (const property of [
    "--aqe-selection-start-px",
    "--aqe-selection-end-px",
    "--aqe-selection-bottom-px",
    "--aqe-selection-toolbar-left-px",
    "--aqe-selection-toolbar-top-px",
    "--aqe-plot-left-px",
    "--aqe-plot-right-px",
    "--aqe-plot-top-px",
    "--aqe-plot-height-px",
    "--aqe-segment-panel-left-px",
    "--aqe-segment-panel-top-px",
    "--aqe-segment-panel-width-px",
  ]) {
    wrapper.style.removeProperty(property);
  }
  clearOverlayNodePosition(wrapper.querySelector<HTMLElement>(".aqe-selection-toolbar"));
  clearOverlayNodePosition(wrapper.querySelector<HTMLElement>(".aqe-selection-toolbar-dot"));
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
