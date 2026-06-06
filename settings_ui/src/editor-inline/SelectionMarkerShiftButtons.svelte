<script lang="ts">
  import { onMount } from "svelte";
  import AqeTooltip from "../lib/AqeTooltip.svelte";
  import { visualizerForOrd } from "./dom-selectors.js";
  import { shiftSelectionEdgeToMarkerForOrd } from "./actions.js";
  import { selectionShiftMutationObserverOptions, syncSelectionMarkerShiftButtons } from "./selection-marker-shift-state.js";
  import type { FieldTarget } from "./types.js";

  const { target }: { target: FieldTarget } = $props();

  function click(edge: "end" | "start", direction: "next" | "previous"): void {
    shiftSelectionEdgeToMarkerForOrd(target.ord, edge, direction);
  }

  onMount(() => {
    const visualizer = visualizerForOrd(target.ord);
    const wrapper = visualizer?.querySelector<HTMLElement>(".aqe-visualizer-plot") ?? null;
    if (!visualizer || !wrapper) return;
    const sync = () => syncSelectionMarkerShiftButtons(visualizer);
    const observer = new MutationObserver(sync);
    observer.observe(visualizer, selectionShiftMutationObserverOptions());
    observer.observe(wrapper, selectionShiftMutationObserverOptions());
    const bodyObserver = new MutationObserver(sync);
    bodyObserver.observe(document.body, {
      attributes: true,
      attributeFilter: ["data-aqe-busy"],
    });
    sync();
    return () => {
      observer.disconnect();
      bodyObserver.disconnect();
    };
  });
</script>

<AqeTooltip>
  {#snippet trigger({ props })}
    <button
      {...props}
      type="button"
      class="aqe-button aqe-icon-only aqe-selection-shift-button aqe-selection-shift-button-start-previous aqe-tooltip-target"
      data-selection-edge="start"
      data-selection-direction="previous"
      data-testid={`aqe-selection-shift-start-previous-${target.ord}`}
      hidden
      onpointerdown={(event) => event.stopPropagation()}
      onmousedown={(event) => event.preventDefault()}
      onclick={() => click("start", "previous")}
    >
      <span class="aqe-selection-shift-triangle" aria-hidden="true"></span>
    </button>
  {/snippet}
</AqeTooltip>
<AqeTooltip>
  {#snippet trigger({ props })}
    <button
      {...props}
      type="button"
      class="aqe-button aqe-icon-only aqe-selection-shift-button aqe-selection-shift-button-start-next aqe-tooltip-target"
      data-selection-edge="start"
      data-selection-direction="next"
      data-testid={`aqe-selection-shift-start-next-${target.ord}`}
      hidden
      onpointerdown={(event) => event.stopPropagation()}
      onmousedown={(event) => event.preventDefault()}
      onclick={() => click("start", "next")}
    >
      <span class="aqe-selection-shift-triangle" aria-hidden="true"></span>
    </button>
  {/snippet}
</AqeTooltip>
<AqeTooltip>
  {#snippet trigger({ props })}
    <button
      {...props}
      type="button"
      class="aqe-button aqe-icon-only aqe-selection-shift-button aqe-selection-shift-button-end-previous aqe-tooltip-target"
      data-selection-edge="end"
      data-selection-direction="previous"
      data-testid={`aqe-selection-shift-end-previous-${target.ord}`}
      hidden
      onpointerdown={(event) => event.stopPropagation()}
      onmousedown={(event) => event.preventDefault()}
      onclick={() => click("end", "previous")}
    >
      <span class="aqe-selection-shift-triangle" aria-hidden="true"></span>
    </button>
  {/snippet}
</AqeTooltip>
<AqeTooltip>
  {#snippet trigger({ props })}
    <button
      {...props}
      type="button"
      class="aqe-button aqe-icon-only aqe-selection-shift-button aqe-selection-shift-button-end-next aqe-tooltip-target"
      data-selection-edge="end"
      data-selection-direction="next"
      data-testid={`aqe-selection-shift-end-next-${target.ord}`}
      hidden
      onpointerdown={(event) => event.stopPropagation()}
      onmousedown={(event) => event.preventDefault()}
      onclick={() => click("end", "next")}
    >
      <span class="aqe-selection-shift-triangle" aria-hidden="true"></span>
    </button>
  {/snippet}
</AqeTooltip>
