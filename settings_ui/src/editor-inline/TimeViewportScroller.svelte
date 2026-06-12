<script lang="ts">
  import { onMount, tick } from "svelte";
  import { visualizerForOrd } from "./dom-selectors.js";
  import {
    isFullTimeViewport,
    panTimeViewport,
    timeViewportSpan,
  } from "./time-viewport.js";
  import type { FieldTarget, VisualizerElement } from "./types.js";
  import { applyVisualizerTimeViewport } from "./viewport-actions.js";
  import { readVisualizerTimeViewport } from "./visualizer-state.js";
  import { readFieldState } from "./field-state-store.js";

  const { target }: { target: FieldTarget } = $props();
  let scroller = $state<HTMLDivElement | null>(null);
  let hidden = $state(true);
  let spacerWidthPercent = $state(100);
  let syncScrollPosition = false;
  let syncedScrollLeft = 0;

  function maxScrollableWidth(scrollElement: HTMLDivElement, clientWidth: number, widthPercent: number): number {
    const measuredScrollableWidth = scrollElement.scrollWidth - clientWidth;
    if (measuredScrollableWidth > 0) return measuredScrollableWidth;
    return Math.max(0, clientWidth * (widthPercent / 100) - clientWidth);
  }

  function syncFromVisualizer(visualizer: VisualizerElement | null = visualizerForOrd(target.ord)): void {
    if (!visualizer || !readFieldState(target.ord).graph.hasTrack) {
      hidden = true;
      spacerWidthPercent = 100;
      return;
    }
    const viewport = readVisualizerTimeViewport(visualizer);
    const span = timeViewportSpan(viewport);
    hidden = isFullTimeViewport(viewport) || span <= 0;
    if (hidden || !scroller) return;
    const nextSpacerWidthPercent = Math.max(100, (viewport.durationMs / span) * 100);
    spacerWidthPercent = nextSpacerWidthPercent;
    const maxStartMs = Math.max(0, viewport.durationMs - span);
    void tick().then(() => {
      if (!scroller) return;
      const clientWidth = scroller.clientWidth || scroller.getBoundingClientRect().width || 1;
      const maxScrollLeft = maxScrollableWidth(scroller, clientWidth, nextSpacerWidthPercent);
      const nextScrollLeft = maxStartMs > 0 ? (viewport.startMs / maxStartMs) * maxScrollLeft : 0;
      syncedScrollLeft = nextScrollLeft;
      syncScrollPosition = true;
      scroller.scrollLeft = nextScrollLeft;
      window.queueMicrotask(() => {
        syncScrollPosition = false;
      });
    });
  }

  function handleScroll(): void {
    if (!scroller) return;
    if (syncScrollPosition && Math.abs(scroller.scrollLeft - syncedScrollLeft) <= 1) return;
    syncScrollPosition = false;
    const visualizer = visualizerForOrd(target.ord);
    if (!visualizer || !readFieldState(target.ord).graph.hasTrack) return;
    const viewport = readVisualizerTimeViewport(visualizer);
    const span = timeViewportSpan(viewport);
    if (isFullTimeViewport(viewport) || span <= 0) return;
    const clientWidth = scroller.clientWidth || scroller.getBoundingClientRect().width || 1;
    const maxScrollLeft = maxScrollableWidth(scroller, clientWidth, spacerWidthPercent);
    if (maxScrollLeft <= 0) return;
    const maxStartMs = Math.max(0, viewport.durationMs - span);
    const scrollLeft = Math.max(0, Math.min(maxScrollLeft, scroller.scrollLeft));
    const nextStartMs = maxScrollLeft - scrollLeft <= 2
      ? maxStartMs
      : Math.max(0, Math.min(maxStartMs, (scrollLeft / maxScrollLeft) * maxStartMs));
    applyVisualizerTimeViewport(visualizer, panTimeViewport(viewport, nextStartMs - viewport.startMs));
  }

  onMount(() => {
    const visualizer = visualizerForOrd(target.ord);
    syncFromVisualizer(visualizer);
    const handleResize = (): void => syncFromVisualizer(visualizer);
    const handleViewportRendered = (): void => syncFromVisualizer(visualizer);
    const mutationObserver = visualizer ? new MutationObserver(() => syncFromVisualizer(visualizer)) : null;
    if (visualizer) {
      visualizer.addEventListener("aqe-viewport-rendered", handleViewportRendered);
      mutationObserver?.observe(visualizer, {
        attributes: true,
        attributeFilter: ["data-has-track", "data-viewport-start-ms", "data-viewport-end-ms", "data-duration-ms"],
      });
    }
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
      visualizer?.removeEventListener("aqe-viewport-rendered", handleViewportRendered);
      mutationObserver?.disconnect();
    };
  });
</script>

<div class="aqe-time-scrollbar" data-testid={`aqe-time-scrollbar-${target.ord}`} hidden={hidden}>
  <div
    bind:this={scroller}
    class="aqe-time-scrollbar-scroll"
    data-testid={`aqe-time-scrollbar-scroll-${target.ord}`}
    onscroll={handleScroll}
  >
    <div class="aqe-time-scrollbar-spacer" style={`width: ${spacerWidthPercent}%`}></div>
  </div>
</div>
