<script lang="ts">
  import AqeTooltip from "../lib/AqeTooltip.svelte";
  import { t } from "../lib/i18n.js";
  import { PRODUCT_LINKS } from "../lib/product-links.js";
  import EditorCommandIcon from "./EditorCommandIcon.svelte";
  import { visualizerForOrd } from "./dom-selectors.js";
  import { openEditorExternalLink } from "./external-links.js";
  import {
    clearBackChainingMarkersForOrd,
    moveBackChainingForOrd,
    backChainingControlsForOrd,
    startBackChainingEditingForOrd,
    toggleBackChainingForOrd,
  } from "./back-chaining-controller.js";
  import type { BackChainingControlsState } from "./back-chaining-dom.js";
  import type { FieldTarget } from "./types.js";

  const { target }: { target: FieldTarget } = $props();
  let state = $state<BackChainingControlsState>(emptyControlsState());
  const visible = $derived(state.panelOpen && (state.baseStartMs !== null || state.canClear));
  const practiceLabel = $derived(
    state.practiceState === "playing"
      ? t("editor.back_chaining.pause_practice")
      : t("editor.back_chaining.practice"),
  );

  function sync(): void {
    state = backChainingControlsForOrd(target.ord);
  }

  function editBackChaining(): void {
    startBackChainingEditingForOrd(target.ord);
    sync();
  }

  function togglePractice(): void {
    toggleBackChainingForOrd(target.ord);
    sync();
  }

  function previous(): void {
    moveBackChainingForOrd(target.ord, "previous");
    sync();
  }

  function next(): void {
    moveBackChainingForOrd(target.ord, "next");
    sync();
  }

  function clearMarkers(): void {
    clearBackChainingMarkersForOrd(target.ord);
    sync();
  }

  function emptyControlsState(): BackChainingControlsState {
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
        "data-back-chaining-active-marker-index",
        "data-back-chaining-base-end-ms",
        "data-back-chaining-base-start-ms",
        "data-back-chaining-editing",
        "data-back-chaining-markers-ms",
        "data-back-chaining-panel-open",
        "data-back-chaining-state",
      ],
      attributes: true,
    });
    sync();
    return () => observer.disconnect();
  });
</script>

{#if visible}
  <div
    id={`aqe-back-chaining-${target.ord}-panel`}
    class="aqe-back-chaining-panel"
    data-testid={`aqe-back-chaining-${target.ord}-panel`}
  >
    <div class="aqe-back-chaining-header">
      <strong>{t("editor.back_chaining.title")}</strong>
      <a
        class="aqe-back-chaining-video-link"
        href={PRODUCT_LINKS.editorVideos.playback}
        onclick={(event) => openEditorExternalLink(event, PRODUCT_LINKS.editorVideos.playback)}
        target="_blank"
        rel="noopener noreferrer"
      >
        {t("links.see_video")}
      </a>
    </div>
    <div class="aqe-back-chaining-controls">
      <AqeTooltip>
        {#snippet trigger({ props })}
          <button
            {...props}
            type="button"
            class="aqe-button aqe-back-chaining-button aqe-tooltip-target"
            data-aqe-tooltip-content={t("editor.back_chaining.edit_title")}
            data-testid={`aqe-back-chaining-${target.ord}-edit`}
            aria-pressed={state.editing ? "true" : "false"}
            disabled={!state.canEdit}
            onpointerdown={(event) => event.stopPropagation()}
            onmousedown={(event) => event.preventDefault()}
            onclick={editBackChaining}
          >
            {t("editor.back_chaining.edit_markers")}
          </button>
        {/snippet}
      </AqeTooltip>
      <AqeTooltip>
        {#snippet trigger({ props })}
          <button
            {...props}
            type="button"
            class="aqe-button aqe-back-chaining-button aqe-tooltip-target"
            data-aqe-tooltip-content={t("editor.back_chaining.practice_title")}
            data-testid={`aqe-back-chaining-${target.ord}-practice`}
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
            class="aqe-button aqe-back-chaining-button aqe-tooltip-target"
            data-aqe-tooltip-content={t("editor.back_chaining.previous_title")}
            data-testid={`aqe-back-chaining-${target.ord}-previous`}
            aria-label={t("editor.back_chaining.previous")}
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
            class="aqe-button aqe-back-chaining-button aqe-tooltip-target"
            data-aqe-tooltip-content={t("editor.back_chaining.next_title")}
            data-testid={`aqe-back-chaining-${target.ord}-next`}
            aria-label={t("editor.back_chaining.next")}
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
            class="aqe-button aqe-back-chaining-button aqe-tooltip-target"
            data-aqe-tooltip-content={t("editor.back_chaining.clear_title")}
            data-testid={`aqe-back-chaining-${target.ord}-clear`}
            aria-label={t("editor.back_chaining.clear")}
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
