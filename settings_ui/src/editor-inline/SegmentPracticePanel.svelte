<script lang="ts">
  import AqeTooltip from "../lib/AqeTooltip.svelte";
  import { t } from "../lib/i18n.js";
  import EditorCommandIcon from "./EditorCommandIcon.svelte";
  import { visualizerForOrd } from "./dom-selectors.js";
  import {
    clearSegmentMarkersForOrd,
    moveSegmentPracticeForOrd,
    segmentPracticeControlsForOrd,
    startSegmentEditingForOrd,
    toggleSegmentPracticeForOrd,
  } from "./segment-practice-controller.js";
  import type { SegmentPracticeControlsState } from "./segment-practice-dom.js";
  import type { FieldTarget } from "./types.js";

  const { target }: { target: FieldTarget } = $props();
  let state = $state<SegmentPracticeControlsState>(emptyControlsState());
  const visible = $derived(state.panelOpen && (state.baseStartMs !== null || state.canClear));
  const practiceLabel = $derived(
    state.practiceState === "playing"
      ? t("editor.segment.pause_practice")
      : t("editor.segment.practice"),
  );

  function sync(): void {
    state = segmentPracticeControlsForOrd(target.ord);
  }

  function editSegments(): void {
    startSegmentEditingForOrd(target.ord);
    sync();
  }

  function togglePractice(): void {
    toggleSegmentPracticeForOrd(target.ord);
    sync();
  }

  function previous(): void {
    moveSegmentPracticeForOrd(target.ord, "previous");
    sync();
  }

  function next(): void {
    moveSegmentPracticeForOrd(target.ord, "next");
    sync();
  }

  function clearMarkers(): void {
    clearSegmentMarkersForOrd(target.ord);
    sync();
  }

  function emptyControlsState(): SegmentPracticeControlsState {
    return {
      activeMarkerIndex: null,
      activeSuffixEndMs: null,
      activeSuffixStartMs: null,
      baseEndMs: null,
      baseStartMs: null,
      canClear: false,
      canEdit: false,
      canNext: false,
      canPractice: false,
      canPrevious: false,
      editing: false,
      markersMs: [],
      panelOpen: false,
      practiceState: "stopped",
      visibleActiveRange: null,
      visibleMarkers: [],
    };
  }

  $effect(() => {
    const visualizer = visualizerForOrd(target.ord);
    if (!visualizer) return;
    const observer = new MutationObserver(sync);
    observer.observe(visualizer, {
      attributeFilter: [
        "data-selection-active",
        "data-segment-active-marker-index",
        "data-segment-base-end-ms",
        "data-segment-base-start-ms",
        "data-segment-editing",
        "data-segment-markers-ms",
        "data-segment-panel-open",
        "data-segment-practice-state",
      ],
      attributes: true,
    });
    sync();
    return () => observer.disconnect();
  });
</script>

{#if visible}
  <div
    class="aqe-segment-practice-panel"
    data-testid={`aqe-segment-${target.ord}-panel`}
  >
    <div class="aqe-segment-practice-header">
      <strong>{t("editor.segment.title")}</strong>
    </div>
    <div class="aqe-segment-practice-controls">
      <AqeTooltip>
        {#snippet trigger({ props })}
          <button
            {...props}
            type="button"
            class="aqe-button aqe-segment-practice-button aqe-tooltip-target"
            data-aqe-tooltip-content={t("editor.segment.edit_title")}
            data-testid={`aqe-segment-${target.ord}-edit`}
            aria-pressed={state.editing ? "true" : "false"}
            disabled={!state.canEdit}
            onclick={editSegments}
          >
            {t("editor.segment.edit_markers")}
          </button>
        {/snippet}
      </AqeTooltip>
      <AqeTooltip>
        {#snippet trigger({ props })}
          <button
            {...props}
            type="button"
            class="aqe-button aqe-segment-practice-button aqe-tooltip-target"
            data-aqe-tooltip-content={t("editor.segment.practice_title")}
            data-testid={`aqe-segment-${target.ord}-practice`}
            disabled={!state.canPractice}
            onclick={togglePractice}
          >
            {practiceLabel}
          </button>
        {/snippet}
      </AqeTooltip>
      <AqeTooltip>
        {#snippet trigger({ props })}
          <button
            {...props}
            type="button"
            class="aqe-button aqe-segment-practice-button aqe-tooltip-target"
            data-aqe-tooltip-content={t("editor.segment.previous_title")}
            data-testid={`aqe-segment-${target.ord}-previous`}
            aria-label={t("editor.segment.previous")}
            disabled={!state.canPrevious}
            onclick={previous}
          >
            <EditorCommandIcon icon="skip-back" />
          </button>
        {/snippet}
      </AqeTooltip>
      <AqeTooltip>
        {#snippet trigger({ props })}
          <button
            {...props}
            type="button"
            class="aqe-button aqe-segment-practice-button aqe-tooltip-target"
            data-aqe-tooltip-content={t("editor.segment.next_title")}
            data-testid={`aqe-segment-${target.ord}-next`}
            aria-label={t("editor.segment.next")}
            disabled={!state.canNext}
            onclick={next}
          >
            <EditorCommandIcon icon="skip-forward" />
          </button>
        {/snippet}
      </AqeTooltip>
      <AqeTooltip>
        {#snippet trigger({ props })}
          <button
            {...props}
            type="button"
            class="aqe-button aqe-segment-practice-button aqe-tooltip-target"
            data-aqe-tooltip-content={t("editor.segment.clear_title")}
            data-testid={`aqe-segment-${target.ord}-clear`}
            aria-label={t("editor.segment.clear")}
            disabled={!state.canClear}
            onclick={clearMarkers}
          >
            <EditorCommandIcon icon="trash-2" />
          </button>
        {/snippet}
      </AqeTooltip>
    </div>
  </div>
{/if}
