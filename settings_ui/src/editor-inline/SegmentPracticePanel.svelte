<script lang="ts">
  import AqeTooltip from "../lib/AqeTooltip.svelte";
  import { t } from "../lib/i18n.js";
  import { PRODUCT_LINKS } from "../lib/product-links.js";
  import EditorCommandIcon from "./EditorCommandIcon.svelte";
  import { visualizerForOrd } from "./dom-selectors.js";
  import { openEditorExternalLink } from "./external-links.js";
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
    id={`aqe-segment-${target.ord}-panel`}
    class="aqe-segment-practice-panel"
    data-testid={`aqe-segment-${target.ord}-panel`}
  >
    <div class="aqe-segment-practice-header">
      <strong>{t("editor.segment.title")}</strong>
      <a
        class="aqe-segment-video-link"
        href={PRODUCT_LINKS.editorVideos.playback}
        onclick={(event) => openEditorExternalLink(event, PRODUCT_LINKS.editorVideos.playback)}
        target="_blank"
        rel="noopener noreferrer"
      >
        {t("links.see_video")}
      </a>
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
            onpointerdown={(event) => event.stopPropagation()}
            onmousedown={(event) => event.preventDefault()}
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
            onpointerdown={(event) => event.stopPropagation()}
            onmousedown={(event) => event.preventDefault()}
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
            onpointerdown={(event) => event.stopPropagation()}
            onmousedown={(event) => event.preventDefault()}
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
            onpointerdown={(event) => event.stopPropagation()}
            onmousedown={(event) => event.preventDefault()}
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
            onpointerdown={(event) => event.stopPropagation()}
            onmousedown={(event) => event.preventDefault()}
            onclick={clearMarkers}
          >
            <EditorCommandIcon icon="trash-2" />
          </button>
        {/snippet}
      </AqeTooltip>
    </div>
  </div>
{/if}
