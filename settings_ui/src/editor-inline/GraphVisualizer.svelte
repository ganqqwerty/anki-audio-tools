<script lang="ts">
  import { onMount } from "svelte";
  import AqeTooltip from "../lib/AqeTooltip.svelte";
  import { t } from "../lib/i18n.js";
  import {
    configureAudioClock,
    handleVisualizerPointerDown,
    initializePlaybackRegionState,
    installAudioClockHandlers,
    resetAudioClockState,
    startSelectionResizeGesture,
  } from "./actions.js";
  import { visualizerForOrd } from "./dom-selectors.js";
  import {
    notifyPostEditPlaybackReady,
    postEditPlaybackIntentForOrd,
  } from "./post-edit-playback.js";
  import { PLOT } from "./plot.js";
  import { syncRecordingControls } from "./recording-actions.js";
  import { handleVisualizerKeyDown } from "./region-delete.js";
  import { handleChorusingMarkerPointerDown, installChorusingHandlers } from "./chorusing-controller.js";
  import GraphAreaControls from "./GraphAreaControls.svelte";
  import SelectionMarkerShiftButtons from "./SelectionMarkerShiftButtons.svelte";
  import SelectionToolbar from "./SelectionToolbar.svelte";
  import TimeViewportScroller from "./TimeViewportScroller.svelte";
  import type { FieldTarget } from "./types.js";
  import type { EditorButtonModes } from "../lib/editor-toolbar-buttons.js";
  import type { EditorCommand } from "./types.js";
  import { redrawVisualizerForCurrentViewport } from "./viewport-actions.js";
  import { handleVisualizerWheelZoom, handleVisualizerZoomKeyDown } from "./zoom-actions.js";
  import ZoomControls from "./ZoomControls.svelte";
  import { updateFieldState } from "./field-state-store.js";

  const {
    buttonModes,
    repeatDefault,
    repeatPauseDefault,
    selectionMarkerShiftButtonsEnabled = false,
    target,
    visibleCommands,
  }: {
    buttonModes: EditorButtonModes | undefined;
    repeatDefault: boolean;
    repeatPauseDefault: number;
    selectionMarkerShiftButtonsEnabled?: boolean;
    target: FieldTarget;
    visibleCommands: EditorCommand[] | undefined;
  } = $props();
  const effectiveRepeatDefault = $derived(
    postEditPlaybackIntentForOrd(target.ord)?.repeat ?? repeatDefault,
  );
  const plotClipId = $derived(`aqe-plot-clip-${target.ord}`);
  const plotClipUrl = $derived(`url(#${plotClipId})`);

  function handleGraphKeyDown(event: KeyboardEvent): void {
    const visualizer = visualizerForOrd(target.ord);
    if (visualizer && handleVisualizerZoomKeyDown(event, visualizer)) return;
    handleVisualizerKeyDown(event, target.ord);
  }

  function handleGraphWheel(event: WheelEvent): void {
    const visualizer = visualizerForOrd(target.ord);
    if (visualizer) handleVisualizerWheelZoom(event, visualizer);
  }

  function installGraphLayoutObserver(visualizer: HTMLElement): () => void {
    const svg = visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg");
    if (!svg) return () => undefined;
    let lastWidth = 0;
    const sync = () => {
      const width = Math.round(Number(svg.getBoundingClientRect().width) || 0);
      if (!width || width === lastWidth) return;
      lastWidth = width;
      redrawVisualizerForCurrentViewport(visualizer);
    };
    const observer = typeof ResizeObserver === "function" ? new ResizeObserver(sync) : null;
    observer?.observe(svg);
    sync();
    return () => {
      observer?.disconnect();
    };
  }

  onMount(() => {
    const visualizer = visualizerForOrd(target.ord);
    if (!visualizer) return;
    const stopGraphLayoutObserver = installGraphLayoutObserver(visualizer);
    const stopChorusingHandlers = installChorusingHandlers(visualizer);
    resetAudioClockState(visualizer);
    initializePlaybackRegionState(visualizer, effectiveRepeatDefault);
    installAudioClockHandlers(visualizer);
    updateFieldState(target.ord, (state) => ({
      ...state,
      sourceFilename: target.sourceFilename || "",
    }));
    configureAudioClock(visualizer, target.sourceFilename || "");
    syncRecordingControls(target.ord);
    notifyPostEditPlaybackReady(target.ord, target.sourceFilename || "");
    return () => {
      stopGraphLayoutObserver();
      stopChorusingHandlers();
    };
  });
</script>

<div
  class="aqe-visualizer"
  data-aqe-field-ord={target.ord}
  data-anchor-ms="0"
  data-cursor-ms="0"
  data-progress-ms="0"
  data-target-duration-ms="0"
  data-viewport-start-ms="0"
  data-viewport-end-ms="0"
  data-learner-duration-ms="0"
  data-learner-recording-status="idle"
  data-graph-active="false"
  data-graph-busy="false"
  data-has-track="false"
  data-playback-state="stopped"
  data-playback-engine=""
  data-playback-start-ms="0"
  data-playback-end-ms="0"
  data-playback-region-mode="full"
  data-playback-reset-cursor-ms="0"
  data-playback-loop={effectiveRepeatDefault ? "true" : "false"}
  data-resume-requires-restart="false"
  data-selection-active="false"
  data-selection-start-ms=""
  data-selection-end-ms=""
  data-selection-draft-active="false"
  data-selection-draft-start-ms=""
  data-selection-draft-end-ms=""
  data-selection-marker-shift-buttons-enabled={selectionMarkerShiftButtonsEnabled ? "true" : "false"}
  data-repeat-enabled={effectiveRepeatDefault ? "true" : "false"}
  data-repeat-pause-seconds={repeatPauseDefault}
  data-repeat-pause-waiting="false"
  data-chorusing-active-marker-index=""
  data-chorusing-base-end-ms=""
  data-chorusing-base-start-ms=""
  data-chorusing-markers-ms=""
  data-chorusing-state="stopped"
  data-testid={`aqe-graph-${target.ord}`}
  role="button"
  aria-label={t("editor.graph.aria")}
  tabindex="0"
  onkeydown={handleGraphKeyDown}
  hidden
>
  <audio class="aqe-audio-clock" data-testid={`aqe-audio-clock-${target.ord}`} preload="metadata" hidden></audio>
  <div class="aqe-graph-layout">
    <GraphAreaControls {target} {visibleCommands} />
    <div
      class="aqe-graph-main"
      data-testid={`aqe-graph-main-${target.ord}`}
    >
      <div
        class="aqe-visualizer-plot"
        data-testid={`aqe-visualizer-plot-${target.ord}`}
        onwheel={handleGraphWheel}
      >
        <div class="aqe-selection-region-preview-halo aqe-selection-region-preview-halo-top" aria-hidden="true"></div>
        <div class="aqe-selection-region-preview-halo aqe-selection-region-preview-halo-bottom" aria-hidden="true"></div>
        <div
          class="aqe-graph-countdown-overlay aqe-recording-countdown-overlay"
          data-testid={`aqe-recording-countdown-overlay-${target.ord}`}
          aria-live="polite"
          aria-atomic="true"
          hidden
        >
          <span class="aqe-graph-countdown-value aqe-recording-countdown-value"></span>
        </div>
        <AqeTooltip side="bottom">
          {#snippet trigger({ props })}
            <div
              {...props}
              class="aqe-chorusing-marker-hitbox aqe-tooltip-target"
              data-aqe-tooltip-content={t("editor.chorusing.marker_row_tooltip")}
              aria-hidden="true"
              hidden
              onpointerdown={(event) => handleChorusingMarkerPointerDown(event, target.ord)}
            ></div>
          {/snippet}
        </AqeTooltip>
        <svg
          class="aqe-visualizer-svg"
          data-testid={`aqe-graph-svg-${target.ord}`}
          viewBox={`0 0 ${PLOT.width} ${PLOT.height}`}
          preserveAspectRatio="xMinYMin meet"
          role="img"
          aria-label={t("editor.graph.image_aria")}
          onpointerdown={(event) => handleVisualizerPointerDown(event, target.ord)}
        >
          <defs>
            <clipPath id={plotClipId}>
              <rect
                x={PLOT.left}
                y={PLOT.top}
                width={PLOT.width - PLOT.left - PLOT.right}
                height={PLOT.height - PLOT.top - PLOT.bottom}
              ></rect>
            </clipPath>
          </defs>
          <rect
            class="aqe-selection"
            data-testid={`aqe-selection-${target.ord}`}
            x={PLOT.left}
            y={PLOT.top}
            width="0"
            height={PLOT.height - PLOT.top - PLOT.bottom}
            visibility="hidden"
          ></rect>
          <path class="aqe-intensity" data-testid={`aqe-intensity-${target.ord}`} d="" clip-path={plotClipUrl}></path>
          <g class="aqe-pitch" data-testid={`aqe-pitch-${target.ord}`} clip-path={plotClipUrl}></g>
          <g class="aqe-learner-pitch" data-testid={`aqe-learner-pitch-${target.ord}`} clip-path={plotClipUrl}></g>
          <rect
            class="aqe-selection-outside-preview aqe-selection-outside-preview-before aqe-selection-rest-preview aqe-selection-rest-preview-before"
            data-testid={`aqe-selection-outside-preview-before-${target.ord}`}
            x={PLOT.left}
            y={PLOT.top}
            width="0"
            height={PLOT.height - PLOT.top - PLOT.bottom}
            visibility="hidden"
          ></rect>
          <rect
            class="aqe-selection-outside-preview aqe-selection-outside-preview-after aqe-selection-rest-preview aqe-selection-rest-preview-after"
            data-testid={`aqe-selection-outside-preview-after-${target.ord}`}
            x={PLOT.left}
            y={PLOT.top}
            width="0"
            height={PLOT.height - PLOT.top - PLOT.bottom}
            visibility="hidden"
          ></rect>
          <g class="aqe-labels"></g>
          <g class="aqe-x-axis" data-testid={`aqe-x-axis-${target.ord}`}></g>
          <g
            class="aqe-chorusing-marker-row"
            data-testid={`aqe-chorusing-marker-row-${target.ord}`}
            role="button"
            aria-label={t("editor.chorusing.marker_row_aria")}
            aria-hidden="true"
            tabindex="0"
            style="display: none"
            onpointerdown={(event) => handleChorusingMarkerPointerDown(event, target.ord)}
          ></g>
        </svg>
        <div class="aqe-selection-edge aqe-selection-start" data-testid={`aqe-selection-start-${target.ord}`} hidden></div>
        <div class="aqe-selection-edge aqe-selection-end" data-testid={`aqe-selection-end-${target.ord}`} hidden></div>
        <button
          type="button"
          class="aqe-selection-resize-handle aqe-selection-resize-start"
          data-testid={`aqe-selection-resize-start-${target.ord}`}
          aria-label="Resize selection start"
          hidden
          onpointerdown={(event) => {
            if (event.shiftKey) return;
            startSelectionResizeGesture(event, target.ord, "start");
          }}
        >
          <span class="aqe-selection-resize-grip" aria-hidden="true">
            <span></span>
            <span></span>
            <span></span>
          </span>
        </button>
        <button
          type="button"
          class="aqe-selection-resize-handle aqe-selection-resize-end"
          data-testid={`aqe-selection-resize-end-${target.ord}`}
          aria-label="Resize selection end"
          hidden
          onpointerdown={(event) => {
            if (event.shiftKey) return;
            startSelectionResizeGesture(event, target.ord, "end");
          }}
        >
          <span class="aqe-selection-resize-grip" aria-hidden="true">
            <span></span>
            <span></span>
            <span></span>
          </span>
        </button>
        <div class="aqe-css-cursor" data-testid={`aqe-css-cursor-${target.ord}`} aria-hidden="true">
          <div class="aqe-css-cursor-line"></div>
          <div class="aqe-css-cursor-flag">
            <div class="aqe-css-cursor-flag-box">
              <span class="aqe-css-cursor-flag-current">0 ms</span>
              <span class="aqe-css-cursor-flag-pitch"> / -- Hz</span>
            </div>
          </div>
        </div>
        {#if selectionMarkerShiftButtonsEnabled}
          <SelectionMarkerShiftButtons {target} />
        {/if}
        <SelectionToolbar {buttonModes} {target} {visibleCommands} />
      </div>
      <TimeViewportScroller {target} />
    </div>
    <ZoomControls {target} />
  </div>
  <span class="aqe-cursor-label" data-testid={`aqe-progress-label-${target.ord}`}>0 ms</span>
</div>
