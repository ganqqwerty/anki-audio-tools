<script lang="ts">
  import { onMount } from "svelte";
  import AqeTooltip from "../lib/AqeTooltip.svelte";
  import { tooltipWithDisabledClarification } from "../lib/disabled-tooltip.js";
  import { t } from "../lib/i18n.js";
  import { visualizerForOrd } from "./dom-selectors.js";
  import EditorCommandIcon from "./EditorCommandIcon.svelte";
  import type { FieldTarget, VisualizerElement } from "./types.js";
  import {
    fitTimeViewportForVisualizer,
    zoomInForVisualizer,
    zoomOutForVisualizer,
    zoomSelectionForVisualizer,
  } from "./zoom-actions.js";
  import { readFieldState } from "./field-state-store.js";

  const { target }: { target: FieldTarget } = $props();
  let hasTrack = $state(false);
  let hasSelection = $state(false);

  function syncState(visualizer: VisualizerElement | null = visualizerForOrd(target.ord)): void {
    const state = readFieldState(target.ord);
    hasTrack = Boolean(visualizer && state.graph.hasTrack);
    hasSelection = Boolean(visualizer && state.selection.active);
  }

  function withVisualizer(action: (visualizer: VisualizerElement) => void): void {
    const visualizer = visualizerForOrd(target.ord);
    if (!visualizer || !readFieldState(target.ord).graph.hasTrack) return;
    action(visualizer);
    syncState(visualizer);
  }

  function trackTooltip(title: string): string {
    return tooltipWithDisabledClarification(title, hasTrack ? undefined : t("editor.zoom.disabled_no_graph"));
  }

  function selectionTooltip(): string {
    return tooltipWithDisabledClarification(
      t("editor.zoom.selection"),
      hasSelection ? undefined : t("editor.zoom.selection.disabled_no_selection"),
    );
  }

  onMount(() => {
    const visualizer = visualizerForOrd(target.ord);
    syncState(visualizer);
    if (!visualizer) return;
    const observer = new MutationObserver(() => syncState(visualizer));
    observer.observe(visualizer, {
      attributes: true,
      attributeFilter: ["data-has-track", "data-selection-active"],
    });
    return () => observer.disconnect();
  });
</script>

<div
  class="aqe-zoom-controls"
  data-testid={`aqe-zoom-controls-${target.ord}`}
  role="toolbar"
  aria-label="Graph zoom"
  hidden={!hasTrack}
>
  <AqeTooltip>
    {#snippet trigger({ props })}
      <button
        {...props}
        type="button"
        class="aqe-button aqe-icon-only aqe-zoom-button aqe-tooltip-target"
        data-aqe-tooltip-content={trackTooltip(t("editor.zoom.in"))}
        data-testid={`aqe-zoom-in-${target.ord}`}
        aria-label={trackTooltip(t("editor.zoom.in"))}
        disabled={!hasTrack}
        onmousedown={(event) => event.preventDefault()}
        onclick={() => withVisualizer(zoomInForVisualizer)}
      >
        <EditorCommandIcon icon="zoom-in" />
        <span class="aqe-button-label">{t("editor.zoom.in")}</span>
      </button>
    {/snippet}
  </AqeTooltip>
  <AqeTooltip>
    {#snippet trigger({ props })}
      <button
        {...props}
        type="button"
        class="aqe-button aqe-icon-only aqe-zoom-button aqe-tooltip-target"
        data-aqe-tooltip-content={trackTooltip(t("editor.zoom.out"))}
        data-testid={`aqe-zoom-out-${target.ord}`}
        aria-label={trackTooltip(t("editor.zoom.out"))}
        disabled={!hasTrack}
        onmousedown={(event) => event.preventDefault()}
        onclick={() => withVisualizer(zoomOutForVisualizer)}
      >
        <EditorCommandIcon icon="zoom-out" />
        <span class="aqe-button-label">{t("editor.zoom.out")}</span>
      </button>
    {/snippet}
  </AqeTooltip>
  <AqeTooltip>
    {#snippet trigger({ props })}
      <button
        {...props}
        type="button"
        class="aqe-button aqe-icon-only aqe-zoom-button aqe-tooltip-target"
        data-aqe-tooltip-content={selectionTooltip()}
        data-testid={`aqe-zoom-selection-${target.ord}`}
        aria-label={selectionTooltip()}
        aria-disabled={!hasSelection}
        disabled={!hasTrack}
        onmousedown={(event) => event.preventDefault()}
        onclick={() => withVisualizer(zoomSelectionForVisualizer)}
      >
        <EditorCommandIcon icon="scan-search" />
        <span class="aqe-button-label">{t("editor.zoom.selection")}</span>
      </button>
    {/snippet}
  </AqeTooltip>
  <AqeTooltip>
    {#snippet trigger({ props })}
      <button
        {...props}
        type="button"
        class="aqe-button aqe-icon-only aqe-zoom-button aqe-tooltip-target"
        data-aqe-tooltip-content={trackTooltip(t("editor.zoom.fit"))}
        data-testid={`aqe-zoom-fit-${target.ord}`}
        aria-label={trackTooltip(t("editor.zoom.fit"))}
        disabled={!hasTrack}
        onmousedown={(event) => event.preventDefault()}
        onclick={() => withVisualizer(fitTimeViewportForVisualizer)}
      >
        <EditorCommandIcon icon="maximize-2" />
        <span class="aqe-button-label">{t("editor.zoom.fit")}</span>
      </button>
    {/snippet}
  </AqeTooltip>
</div>
